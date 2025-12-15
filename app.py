#!/usr/bin/env python3
"""
GreatPoint Ventures Portfolio Management System
Multi-Fund Architecture with Google Form Integration
"""
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc, func
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'greatpoint-ventures-2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize database
db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class Fund(db.Model):
    """Investment Fund (Fund 1, Fund 2, Fund 3)"""
    __tablename__ = 'funds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    vintage_year = db.Column(db.Integer)
    fund_size = db.Column(db.Float)  # in millions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    companies = db.relationship('Company', backref='fund', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Fund {self.name}>'


class Company(db.Model):
    """Portfolio Company"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    industry = db.Column(db.String(100))
    fund_id = db.Column(db.Integer, db.ForeignKey('funds.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    quarterly_data = db.relationship('QuarterlyData', backref='company', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Company {self.name}>'


class QuarterlyData(db.Model):
    """Quarterly Financial Metrics"""
    __tablename__ = 'quarterly_data'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4

    # Core metrics
    revenue = db.Column(db.Float, default=0)
    arr = db.Column(db.Float, default=0)
    arr_projection = db.Column(db.Float, default=0)  # End-of-year ARR projection
    headcount = db.Column(db.Integer, default=0)
    gross_profit = db.Column(db.Float, default=0)
    gross_profit_percent = db.Column(db.Float, default=0)
    sales_marketing = db.Column(db.Float, default=0)
    research_development = db.Column(db.Float, default=0)
    general_administrative = db.Column(db.Float, default=0)
    eop_cash = db.Column(db.Float, default=0)
    eop_runway = db.Column(db.Float, default=0)  # in months

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('company_id', 'year', 'quarter', name='_company_quarter_uc'),)

    @property
    def period(self):
        return f'Q{self.quarter} {self.year}'

    def __repr__(self):
        return f'<QuarterlyData {self.company.name} Q{self.quarter} {self.year}>'


# ==================== HELPER FUNCTIONS ====================

def get_fund_aggregates(fund_id):
    """Get aggregate metrics for a fund"""
    companies = Company.query.filter_by(fund_id=fund_id).all()

    total_companies = len(companies)
    total_arr = 0
    total_revenue = 0
    growth_rates = []

    for company in companies:
        # Get latest data
        latest = QuarterlyData.query.filter_by(company_id=company.id)\
            .order_by(desc(QuarterlyData.year), desc(QuarterlyData.quarter)).first()

        if latest:
            total_arr += latest.arr
            total_revenue += latest.revenue

            # Calculate QoQ growth
            prev_quarter = get_previous_quarter(latest.year, latest.quarter)
            if prev_quarter:
                prev_data = QuarterlyData.query.filter_by(
                    company_id=company.id,
                    year=prev_quarter[0],
                    quarter=prev_quarter[1]
                ).first()

                if prev_data and prev_data.arr > 0:
                    growth = ((latest.arr - prev_data.arr) / prev_data.arr) * 100
                    growth_rates.append(growth)

    avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0

    return {
        'total_companies': total_companies,
        'total_arr': total_arr,
        'total_revenue': total_revenue,
        'avg_growth': avg_growth
    }


def get_previous_quarter(year, quarter):
    """Get previous quarter (year, quarter)"""
    if quarter == 1:
        return (year - 1, 4)
    else:
        return (year, quarter - 1)


def calculate_qoq_growth(company_id, year, quarter, metric='arr'):
    """Calculate quarter-over-quarter growth for a metric"""
    current = QuarterlyData.query.filter_by(
        company_id=company_id, year=year, quarter=quarter
    ).first()

    if not current:
        return None

    prev_quarter = get_previous_quarter(year, quarter)
    prev = QuarterlyData.query.filter_by(
        company_id=company_id,
        year=prev_quarter[0],
        quarter=prev_quarter[1]
    ).first()

    if not prev:
        return None

    current_value = getattr(current, metric, 0)
    prev_value = getattr(prev, metric, 0)

    if prev_value == 0:
        return None

    growth = ((current_value - prev_value) / prev_value) * 100
    return round(growth, 1)


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Redirect to main dashboard"""
    return redirect(url_for('dashboard_overview'))


# ==================== PAGE 1: MAIN DASHBOARD ====================

@app.route('/dashboard/overview')
def dashboard_overview():
    """Main Dashboard - Portfolio Overview by Fund"""
    funds = Fund.query.all()

    fund_data = []
    for fund in funds:
        aggregates = get_fund_aggregates(fund.id)

        # Get companies with latest metrics
        companies = Company.query.filter_by(fund_id=fund.id).all()
        company_metrics = []

        for company in companies:
            latest = QuarterlyData.query.filter_by(company_id=company.id)\
                .order_by(desc(QuarterlyData.year), desc(QuarterlyData.quarter)).first()

            if latest:
                qoq_growth = calculate_qoq_growth(company.id, latest.year, latest.quarter)
                company_metrics.append({
                    'id': company.id,
                    'name': company.name,
                    'industry': company.industry,
                    'period': latest.period,
                    'arr': latest.arr,
                    'revenue': latest.revenue,
                    'headcount': latest.headcount,
                    'qoq_growth': qoq_growth
                })

        fund_data.append({
            'fund': fund,
            'aggregates': aggregates,
            'companies': company_metrics
        })

    return render_template('dashboard_overview.html', fund_data=fund_data)


# ==================== PAGE 2: REVENUE & ARR HISTORY ====================

@app.route('/dashboard/revenue-arr-by-fund')
def revenue_arr_by_fund():
    """Revenue & ARR History by Fund"""
    fund_id = request.args.get('fund_id', type=int)

    funds = Fund.query.all()

    if fund_id:
        selected_fund = Fund.query.get(fund_id)
        companies = Company.query.filter_by(fund_id=fund_id).all()
    else:
        selected_fund = None
        companies = Company.query.all()

    company_data = []
    for company in companies:
        history = QuarterlyData.query.filter_by(company_id=company.id)\
            .order_by(desc(QuarterlyData.year), desc(QuarterlyData.quarter)).all()

        history_list = []
        for data in history:
            qoq_growth = calculate_qoq_growth(company.id, data.year, data.quarter)
            history_list.append({
                'period': data.period,
                'year': data.year,
                'quarter': data.quarter,
                'revenue': data.revenue,
                'arr': data.arr,
                'arr_projection': data.arr_projection,
                'qoq_growth': qoq_growth
            })

        if history_list:
            company_data.append({
                'company_id': company.id,
                'company_name': company.name,
                'fund_name': company.fund.name,
                'history': history_list
            })

    return render_template('revenue_arr_by_fund.html',
                         funds=funds,
                         selected_fund=selected_fund,
                         company_data=company_data)


# ==================== PAGE 3: COMPANY METRICS DETAIL ====================

@app.route('/dashboard/company-metrics')
def company_metrics():
    """Detailed Company Metrics"""
    fund_id = request.args.get('fund_id', type=int)
    company_id = request.args.get('company_id', type=int)

    funds = Fund.query.all()
    companies = []
    metrics = []
    selected_fund = None
    selected_company = None

    if fund_id:
        selected_fund = Fund.query.get(fund_id)
        companies = Company.query.filter_by(fund_id=fund_id).all()

    if company_id:
        selected_company = Company.query.get(company_id)
        metrics = QuarterlyData.query.filter_by(company_id=company_id)\
            .order_by(desc(QuarterlyData.year), desc(QuarterlyData.quarter)).all()

    return render_template('company_metrics.html',
                         funds=funds,
                         companies=companies,
                         metrics=metrics,
                         selected_fund=selected_fund,
                         selected_company=selected_company)


# ==================== PAGE 4: GOOGLE FORM MANAGEMENT ====================

@app.route('/forms/manage')
def forms_manage():
    """Google Form Management"""
    # Get webhook URL
    webhook_url = request.url_root + 'api/form-submit'

    # Get all companies for form generation
    funds = Fund.query.all()
    companies = Company.query.all()

    return render_template('forms_manage.html',
                         webhook_url=webhook_url,
                         funds=funds,
                         companies=companies)


@app.route('/api/form-submit', methods=['POST'])
def api_form_submit():
    """Handle Google Form submissions"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()

        # Extract data from form
        company_name = data.get('company_name')
        year = int(data.get('year'))
        quarter = int(data.get('quarter'))

        # Find company
        company = Company.query.filter_by(name=company_name).first()
        if not company:
            return jsonify({'error': 'Company not found'}), 404

        # Check if data already exists for this period
        existing = QuarterlyData.query.filter_by(
            company_id=company.id,
            year=year,
            quarter=quarter
        ).first()

        if existing:
            # Update existing
            quarterly_data = existing
        else:
            # Create new
            quarterly_data = QuarterlyData(
                company_id=company.id,
                year=year,
                quarter=quarter
            )

        # Update all fields
        quarterly_data.revenue = float(data.get('revenue', 0))
        quarterly_data.arr = float(data.get('arr', 0))
        quarterly_data.arr_projection = float(data.get('arr_projection', 0))
        quarterly_data.headcount = int(data.get('headcount', 0))
        quarterly_data.gross_profit = float(data.get('gross_profit', 0))
        quarterly_data.gross_profit_percent = float(data.get('gross_profit_percent', 0))
        quarterly_data.sales_marketing = float(data.get('sales_marketing', 0))
        quarterly_data.research_development = float(data.get('research_development', 0))
        quarterly_data.general_administrative = float(data.get('general_administrative', 0))
        quarterly_data.eop_cash = float(data.get('eop_cash', 0))
        quarterly_data.eop_runway = float(data.get('eop_runway', 0))

        db.session.add(quarterly_data)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Data submitted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PAGE 5: PORTFOLIO COMPANY DATABASE ====================

@app.route('/admin/companies')
def admin_companies():
    """Portfolio Company Master Database"""
    funds = Fund.query.all()

    fund_companies = []
    for fund in funds:
        companies = Company.query.filter_by(fund_id=fund.id).all()

        company_list = []
        for company in companies:
            latest = QuarterlyData.query.filter_by(company_id=company.id)\
                .order_by(desc(QuarterlyData.year), desc(QuarterlyData.quarter)).first()

            company_list.append({
                'id': company.id,
                'name': company.name,
                'industry': company.industry,
                'latest_period': latest.period if latest else 'No data',
                'data_count': QuarterlyData.query.filter_by(company_id=company.id).count()
            })

        fund_companies.append({
            'fund': fund,
            'companies': company_list
        })

    return render_template('admin_companies.html', fund_companies=fund_companies)


@app.route('/admin/companies/add', methods=['GET', 'POST'])
def admin_add_company():
    """Add new company"""
    if request.method == 'POST':
        name = request.form.get('name')
        industry = request.form.get('industry')
        fund_id = int(request.form.get('fund_id'))

        if not name:
            flash('Company name is required', 'error')
            return redirect(url_for('admin_add_company'))

        existing = Company.query.filter_by(name=name).first()
        if existing:
            flash('Company already exists', 'error')
            return redirect(url_for('admin_add_company'))

        company = Company(name=name, industry=industry, fund_id=fund_id)
        db.session.add(company)
        db.session.commit()

        flash(f'Company "{name}" added successfully', 'success')
        return redirect(url_for('admin_companies'))

    funds = Fund.query.all()
    return render_template('admin_add_company.html', funds=funds)


@app.route('/admin/companies/<int:company_id>/edit', methods=['GET', 'POST'])
def admin_edit_company(company_id):
    """Edit company and metrics"""
    company = Company.query.get_or_404(company_id)

    if request.method == 'POST':
        # Update company info
        company.name = request.form.get('name')
        company.industry = request.form.get('industry')
        company.fund_id = int(request.form.get('fund_id'))

        # Update or create quarterly data
        year = int(request.form.get('year'))
        quarter = int(request.form.get('quarter'))

        quarterly_data = QuarterlyData.query.filter_by(
            company_id=company.id,
            year=year,
            quarter=quarter
        ).first()

        if not quarterly_data:
            quarterly_data = QuarterlyData(
                company_id=company.id,
                year=year,
                quarter=quarter
            )

        quarterly_data.revenue = float(request.form.get('revenue', 0))
        quarterly_data.arr = float(request.form.get('arr', 0))
        quarterly_data.arr_projection = float(request.form.get('arr_projection', 0))
        quarterly_data.headcount = int(request.form.get('headcount', 0))
        quarterly_data.gross_profit = float(request.form.get('gross_profit', 0))
        quarterly_data.gross_profit_percent = float(request.form.get('gross_profit_percent', 0))
        quarterly_data.sales_marketing = float(request.form.get('sales_marketing', 0))
        quarterly_data.research_development = float(request.form.get('research_development', 0))
        quarterly_data.general_administrative = float(request.form.get('general_administrative', 0))
        quarterly_data.eop_cash = float(request.form.get('eop_cash', 0))
        quarterly_data.eop_runway = float(request.form.get('eop_runway', 0))

        db.session.add(quarterly_data)
        db.session.commit()

        flash('Company updated successfully', 'success')
        return redirect(url_for('admin_companies'))

    funds = Fund.query.all()
    metrics = QuarterlyData.query.filter_by(company_id=company.id)\
        .order_by(desc(QuarterlyData.year), desc(QuarterlyData.quarter)).all()

    return render_template('admin_edit_company.html',
                         company=company,
                         funds=funds,
                         metrics=metrics)


# ==================== API ENDPOINTS FOR CHARTS ====================

@app.route('/api/company/<int:company_id>/revenue-arr-chart')
def api_revenue_arr_chart(company_id):
    """Get revenue and ARR data for charts"""
    historical_data = QuarterlyData.query.filter_by(company_id=company_id)\
        .order_by(QuarterlyData.year.asc(), QuarterlyData.quarter.asc()).all()

    labels = [f'Q{d.quarter} {d.year}' for d in historical_data]
    revenue_data = [d.revenue for d in historical_data]
    arr_data = [d.arr for d in historical_data]

    return jsonify({
        'labels': labels,
        'revenue': revenue_data,
        'arr': arr_data
    })


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize database with sample data"""
    db.create_all()

    # Check if already initialized
    if Fund.query.first():
        return

    print("\n" + "="*60)
    print("Initializing GreatPoint Ventures Portfolio Database")
    print("="*60)

    # Create Funds
    fund1 = Fund(name='Fund 1', vintage_year=2020, fund_size=100)
    fund2 = Fund(name='Fund 2', vintage_year=2022, fund_size=150)
    fund3 = Fund(name='Fund 3', vintage_year=2024, fund_size=200)

    db.session.add_all([fund1, fund2, fund3])
    db.session.commit()

    # Create 5 Sample Companies
    companies = [
        Company(name='CloudSync Solutions', industry='SaaS - Enterprise', fund_id=fund1.id),
        Company(name='DataFlow Analytics', industry='SaaS - Data', fund_id=fund1.id),
        Company(name='SecureAuth Pro', industry='Security', fund_id=fund2.id),
        Company(name='MarketPulse AI', industry='MarTech', fund_id=fund2.id),
        Company(name='FinStream Technologies', industry='FinTech', fund_id=fund3.id),
    ]

    db.session.add_all(companies)
    db.session.commit()

    # Add realistic quarterly data for 3 years (Q1 2022 - Q4 2024)
    print("\nCreating sample data...")

    # CloudSync Solutions - Strong enterprise SaaS growth
    cloudsync_data = [
        # 2022
        {'year': 2022, 'quarter': 1, 'revenue': 2.5, 'arr': 10.0, 'arr_projection': 15.0, 'headcount': 45, 'gross_profit': 2.0, 'gross_profit_percent': 80, 'sales_marketing': 1.0, 'research_development': 0.7, 'general_administrative': 0.4, 'eop_cash': 8.5, 'eop_runway': 14},
        {'year': 2022, 'quarter': 2, 'revenue': 2.8, 'arr': 11.2, 'arr_projection': 15.0, 'headcount': 48, 'gross_profit': 2.24, 'gross_profit_percent': 80, 'sales_marketing': 1.1, 'research_development': 0.75, 'general_administrative': 0.42, 'eop_cash': 8.2, 'eop_runway': 13},
        {'year': 2022, 'quarter': 3, 'revenue': 3.2, 'arr': 12.8, 'arr_projection': 15.0, 'headcount': 52, 'gross_profit': 2.56, 'gross_profit_percent': 80, 'sales_marketing': 1.25, 'research_development': 0.85, 'general_administrative': 0.45, 'eop_cash': 7.8, 'eop_runway': 12},
        {'year': 2022, 'quarter': 4, 'revenue': 3.6, 'arr': 14.4, 'arr_projection': 20.0, 'headcount': 55, 'gross_profit': 2.88, 'gross_profit_percent': 80, 'sales_marketing': 1.4, 'research_development': 0.9, 'general_administrative': 0.48, 'eop_cash': 12.0, 'eop_runway': 15},
        # 2023
        {'year': 2023, 'quarter': 1, 'revenue': 4.2, 'arr': 16.8, 'arr_projection': 20.0, 'headcount': 60, 'gross_profit': 3.36, 'gross_profit_percent': 80, 'sales_marketing': 1.6, 'research_development': 1.0, 'general_administrative': 0.52, 'eop_cash': 11.5, 'eop_runway': 14},
        {'year': 2023, 'quarter': 2, 'revenue': 4.8, 'arr': 19.2, 'arr_projection': 20.0, 'headcount': 65, 'gross_profit': 3.84, 'gross_profit_percent': 80, 'sales_marketing': 1.8, 'research_development': 1.1, 'general_administrative': 0.55, 'eop_cash': 11.0, 'eop_runway': 13},
        {'year': 2023, 'quarter': 3, 'revenue': 5.5, 'arr': 22.0, 'arr_projection': 20.0, 'headcount': 70, 'gross_profit': 4.4, 'gross_profit_percent': 80, 'sales_marketing': 2.0, 'research_development': 1.2, 'general_administrative': 0.6, 'eop_cash': 10.5, 'eop_runway': 12},
        {'year': 2023, 'quarter': 4, 'revenue': 6.2, 'arr': 24.8, 'arr_projection': 32.0, 'headcount': 75, 'gross_profit': 4.96, 'gross_profit_percent': 80, 'sales_marketing': 2.3, 'research_development': 1.3, 'general_administrative': 0.65, 'eop_cash': 15.5, 'eop_runway': 16},
        # 2024
        {'year': 2024, 'quarter': 1, 'revenue': 7.0, 'arr': 28.0, 'arr_projection': 32.0, 'headcount': 82, 'gross_profit': 5.6, 'gross_profit_percent': 80, 'sales_marketing': 2.5, 'research_development': 1.5, 'general_administrative': 0.7, 'eop_cash': 15.0, 'eop_runway': 15},
        {'year': 2024, 'quarter': 2, 'revenue': 7.8, 'arr': 31.2, 'arr_projection': 32.0, 'headcount': 88, 'gross_profit': 6.24, 'gross_profit_percent': 80, 'sales_marketing': 2.8, 'research_development': 1.6, 'general_administrative': 0.75, 'eop_cash': 14.5, 'eop_runway': 14},
        {'year': 2024, 'quarter': 3, 'revenue': 8.8, 'arr': 35.2, 'arr_projection': 32.0, 'headcount': 95, 'gross_profit': 7.04, 'gross_profit_percent': 80, 'sales_marketing': 3.2, 'research_development': 1.8, 'general_administrative': 0.8, 'eop_cash': 14.0, 'eop_runway': 13},
        {'year': 2024, 'quarter': 4, 'revenue': 9.5, 'arr': 38.0, 'arr_projection': 50.0, 'headcount': 100, 'gross_profit': 7.6, 'gross_profit_percent': 80, 'sales_marketing': 3.5, 'research_development': 2.0, 'general_administrative': 0.85, 'eop_cash': 20.0, 'eop_runway': 18},
    ]

    # DataFlow Analytics - Moderate data analytics growth
    dataflow_data = [
        # 2022
        {'year': 2022, 'quarter': 1, 'revenue': 1.5, 'arr': 6.0, 'arr_projection': 8.0, 'headcount': 28, 'gross_profit': 1.2, 'gross_profit_percent': 78, 'sales_marketing': 0.6, 'research_development': 0.4, 'general_administrative': 0.25, 'eop_cash': 4.2, 'eop_runway': 12},
        {'year': 2022, 'quarter': 2, 'revenue': 1.7, 'arr': 6.8, 'arr_projection': 8.0, 'headcount': 30, 'gross_profit': 1.33, 'gross_profit_percent': 78, 'sales_marketing': 0.65, 'research_development': 0.45, 'general_administrative': 0.27, 'eop_cash': 4.0, 'eop_runway': 11},
        {'year': 2022, 'quarter': 3, 'revenue': 1.9, 'arr': 7.6, 'arr_projection': 8.0, 'headcount': 32, 'gross_profit': 1.48, 'gross_profit_percent': 78, 'sales_marketing': 0.72, 'research_development': 0.5, 'general_administrative': 0.28, 'eop_cash': 3.8, 'eop_runway': 10},
        {'year': 2022, 'quarter': 4, 'revenue': 2.2, 'arr': 8.8, 'arr_projection': 12.0, 'headcount': 35, 'gross_profit': 1.72, 'gross_profit_percent': 78, 'sales_marketing': 0.8, 'research_development': 0.55, 'general_administrative': 0.3, 'eop_cash': 6.5, 'eop_runway': 13},
        # 2023
        {'year': 2023, 'quarter': 1, 'revenue': 2.5, 'arr': 10.0, 'arr_projection': 12.0, 'headcount': 38, 'gross_profit': 1.95, 'gross_profit_percent': 78, 'sales_marketing': 0.9, 'research_development': 0.6, 'general_administrative': 0.32, 'eop_cash': 6.2, 'eop_runway': 12},
        {'year': 2023, 'quarter': 2, 'revenue': 2.8, 'arr': 11.2, 'arr_projection': 12.0, 'headcount': 40, 'gross_profit': 2.18, 'gross_profit_percent': 78, 'sales_marketing': 1.0, 'research_development': 0.65, 'general_administrative': 0.35, 'eop_cash': 6.0, 'eop_runway': 11},
        {'year': 2023, 'quarter': 3, 'revenue': 3.2, 'arr': 12.8, 'arr_projection': 12.0, 'headcount': 43, 'gross_profit': 2.5, 'gross_profit_percent': 78, 'sales_marketing': 1.15, 'research_development': 0.7, 'general_administrative': 0.38, 'eop_cash': 5.8, 'eop_runway': 10},
        {'year': 2023, 'quarter': 4, 'revenue': 3.6, 'arr': 14.4, 'arr_projection': 18.0, 'headcount': 45, 'gross_profit': 2.81, 'gross_profit_percent': 78, 'sales_marketing': 1.3, 'research_development': 0.75, 'general_administrative': 0.4, 'eop_cash': 8.0, 'eop_runway': 12},
        # 2024
        {'year': 2024, 'quarter': 1, 'revenue': 4.0, 'arr': 16.0, 'arr_projection': 18.0, 'headcount': 48, 'gross_profit': 3.12, 'gross_profit_percent': 78, 'sales_marketing': 1.4, 'research_development': 0.8, 'general_administrative': 0.42, 'eop_cash': 7.8, 'eop_runway': 11},
        {'year': 2024, 'quarter': 2, 'revenue': 4.5, 'arr': 18.0, 'arr_projection': 18.0, 'headcount': 52, 'gross_profit': 3.51, 'gross_profit_percent': 78, 'sales_marketing': 1.6, 'research_development': 0.9, 'general_administrative': 0.45, 'eop_cash': 7.5, 'eop_runway': 10},
        {'year': 2024, 'quarter': 3, 'revenue': 5.0, 'arr': 20.0, 'arr_projection': 18.0, 'headcount': 55, 'gross_profit': 3.9, 'gross_profit_percent': 78, 'sales_marketing': 1.8, 'research_development': 1.0, 'general_administrative': 0.48, 'eop_cash': 7.2, 'eop_runway': 9},
        {'year': 2024, 'quarter': 4, 'revenue': 5.5, 'arr': 22.0, 'arr_projection': 28.0, 'headcount': 58, 'gross_profit': 4.29, 'gross_profit_percent': 78, 'sales_marketing': 2.0, 'research_development': 1.1, 'general_administrative': 0.5, 'eop_cash': 10.0, 'eop_runway': 12},
    ]

    # SecureAuth Pro - Security product with steady growth
    secureauth_data = [
        # 2022
        {'year': 2022, 'quarter': 1, 'revenue': 1.8, 'arr': 7.2, 'arr_projection': 10.0, 'headcount': 32, 'gross_profit': 1.44, 'gross_profit_percent': 82, 'sales_marketing': 0.7, 'research_development': 0.5, 'general_administrative': 0.28, 'eop_cash': 5.5, 'eop_runway': 13},
        {'year': 2022, 'quarter': 2, 'revenue': 2.0, 'arr': 8.0, 'arr_projection': 10.0, 'headcount': 34, 'gross_profit': 1.64, 'gross_profit_percent': 82, 'sales_marketing': 0.75, 'research_development': 0.55, 'general_administrative': 0.3, 'eop_cash': 5.3, 'eop_runway': 12},
        {'year': 2022, 'quarter': 3, 'revenue': 2.3, 'arr': 9.2, 'arr_projection': 10.0, 'headcount': 36, 'gross_profit': 1.89, 'gross_profit_percent': 82, 'sales_marketing': 0.85, 'research_development': 0.6, 'general_administrative': 0.32, 'eop_cash': 5.0, 'eop_runway': 11},
        {'year': 2022, 'quarter': 4, 'revenue': 2.6, 'arr': 10.4, 'arr_projection': 14.0, 'headcount': 38, 'gross_profit': 2.13, 'gross_profit_percent': 82, 'sales_marketing': 0.95, 'research_development': 0.65, 'general_administrative': 0.35, 'eop_cash': 7.5, 'eop_runway': 14},
        # 2023
        {'year': 2023, 'quarter': 1, 'revenue': 3.0, 'arr': 12.0, 'arr_projection': 14.0, 'headcount': 42, 'gross_profit': 2.46, 'gross_profit_percent': 82, 'sales_marketing': 1.1, 'research_development': 0.7, 'general_administrative': 0.38, 'eop_cash': 7.2, 'eop_runway': 13},
        {'year': 2023, 'quarter': 2, 'revenue': 3.4, 'arr': 13.6, 'arr_projection': 14.0, 'headcount': 45, 'gross_profit': 2.79, 'gross_profit_percent': 82, 'sales_marketing': 1.25, 'research_development': 0.8, 'general_administrative': 0.4, 'eop_cash': 7.0, 'eop_runway': 12},
        {'year': 2023, 'quarter': 3, 'revenue': 3.8, 'arr': 15.2, 'arr_projection': 14.0, 'headcount': 48, 'gross_profit': 3.12, 'gross_profit_percent': 82, 'sales_marketing': 1.4, 'research_development': 0.9, 'general_administrative': 0.42, 'eop_cash': 6.8, 'eop_runway': 11},
        {'year': 2023, 'quarter': 4, 'revenue': 4.2, 'arr': 16.8, 'arr_projection': 22.0, 'headcount': 50, 'gross_profit': 3.44, 'gross_profit_percent': 82, 'sales_marketing': 1.5, 'research_development': 1.0, 'general_administrative': 0.45, 'eop_cash': 9.5, 'eop_runway': 13},
        # 2024
        {'year': 2024, 'quarter': 1, 'revenue': 4.8, 'arr': 19.2, 'arr_projection': 22.0, 'headcount': 54, 'gross_profit': 3.94, 'gross_profit_percent': 82, 'sales_marketing': 1.7, 'research_development': 1.1, 'general_administrative': 0.48, 'eop_cash': 9.2, 'eop_runway': 12},
        {'year': 2024, 'quarter': 2, 'revenue': 5.4, 'arr': 21.6, 'arr_projection': 22.0, 'headcount': 58, 'gross_profit': 4.43, 'gross_profit_percent': 82, 'sales_marketing': 1.9, 'research_development': 1.2, 'general_administrative': 0.5, 'eop_cash': 9.0, 'eop_runway': 11},
        {'year': 2024, 'quarter': 3, 'revenue': 6.0, 'arr': 24.0, 'arr_projection': 22.0, 'headcount': 62, 'gross_profit': 4.92, 'gross_profit_percent': 82, 'sales_marketing': 2.1, 'research_development': 1.3, 'general_administrative': 0.55, 'eop_cash': 8.8, 'eop_runway': 10},
        {'year': 2024, 'quarter': 4, 'revenue': 6.5, 'arr': 26.0, 'arr_projection': 35.0, 'headcount': 65, 'gross_profit': 5.33, 'gross_profit_percent': 82, 'sales_marketing': 2.3, 'research_development': 1.4, 'general_administrative': 0.58, 'eop_cash': 12.5, 'eop_runway': 13},
    ]

    # MarketPulse AI - AI-powered marketing with high growth
    marketpulse_data = [
        # 2022
        {'year': 2022, 'quarter': 1, 'revenue': 0.8, 'arr': 3.2, 'arr_projection': 5.0, 'headcount': 18, 'gross_profit': 0.64, 'gross_profit_percent': 75, 'sales_marketing': 0.35, 'research_development': 0.25, 'general_administrative': 0.15, 'eop_cash': 3.5, 'eop_runway': 14},
        {'year': 2022, 'quarter': 2, 'revenue': 1.0, 'arr': 4.0, 'arr_projection': 5.0, 'headcount': 20, 'gross_profit': 0.75, 'gross_profit_percent': 75, 'sales_marketing': 0.4, 'research_development': 0.28, 'general_administrative': 0.17, 'eop_cash': 3.3, 'eop_runway': 13},
        {'year': 2022, 'quarter': 3, 'revenue': 1.2, 'arr': 4.8, 'arr_projection': 5.0, 'headcount': 22, 'gross_profit': 0.9, 'gross_profit_percent': 75, 'sales_marketing': 0.45, 'research_development': 0.32, 'general_administrative': 0.18, 'eop_cash': 3.0, 'eop_runway': 12},
        {'year': 2022, 'quarter': 4, 'revenue': 1.5, 'arr': 6.0, 'arr_projection': 8.0, 'headcount': 25, 'gross_profit': 1.13, 'gross_profit_percent': 75, 'sales_marketing': 0.55, 'research_development': 0.38, 'general_administrative': 0.2, 'eop_cash': 5.0, 'eop_runway': 15},
        # 2023
        {'year': 2023, 'quarter': 1, 'revenue': 1.8, 'arr': 7.2, 'arr_projection': 8.0, 'headcount': 28, 'gross_profit': 1.35, 'gross_profit_percent': 75, 'sales_marketing': 0.65, 'research_development': 0.45, 'general_administrative': 0.22, 'eop_cash': 4.8, 'eop_runway': 14},
        {'year': 2023, 'quarter': 2, 'revenue': 2.2, 'arr': 8.8, 'arr_projection': 8.0, 'headcount': 32, 'gross_profit': 1.65, 'gross_profit_percent': 75, 'sales_marketing': 0.8, 'research_development': 0.55, 'general_administrative': 0.25, 'eop_cash': 4.5, 'eop_runway': 13},
        {'year': 2023, 'quarter': 3, 'revenue': 2.8, 'arr': 11.2, 'arr_projection': 8.0, 'headcount': 36, 'gross_profit': 2.1, 'gross_profit_percent': 75, 'sales_marketing': 1.0, 'research_development': 0.7, 'general_administrative': 0.28, 'eop_cash': 4.2, 'eop_runway': 12},
        {'year': 2023, 'quarter': 4, 'revenue': 3.5, 'arr': 14.0, 'arr_projection': 20.0, 'headcount': 40, 'gross_profit': 2.63, 'gross_profit_percent': 75, 'sales_marketing': 1.25, 'research_development': 0.9, 'general_administrative': 0.32, 'eop_cash': 7.5, 'eop_runway': 15},
        # 2024
        {'year': 2024, 'quarter': 1, 'revenue': 4.5, 'arr': 18.0, 'arr_projection': 20.0, 'headcount': 46, 'gross_profit': 3.38, 'gross_profit_percent': 75, 'sales_marketing': 1.6, 'research_development': 1.1, 'general_administrative': 0.38, 'eop_cash': 7.2, 'eop_runway': 14},
        {'year': 2024, 'quarter': 2, 'revenue': 5.5, 'arr': 22.0, 'arr_projection': 20.0, 'headcount': 52, 'gross_profit': 4.13, 'gross_profit_percent': 75, 'sales_marketing': 2.0, 'research_development': 1.4, 'general_administrative': 0.45, 'eop_cash': 7.0, 'eop_runway': 13},
        {'year': 2024, 'quarter': 3, 'revenue': 6.8, 'arr': 27.2, 'arr_projection': 20.0, 'headcount': 58, 'gross_profit': 5.1, 'gross_profit_percent': 75, 'sales_marketing': 2.5, 'research_development': 1.7, 'general_administrative': 0.52, 'eop_cash': 6.8, 'eop_runway': 12},
        {'year': 2024, 'quarter': 4, 'revenue': 8.0, 'arr': 32.0, 'arr_projection': 45.0, 'headcount': 65, 'gross_profit': 6.0, 'gross_profit_percent': 75, 'sales_marketing': 3.0, 'research_development': 2.0, 'general_administrative': 0.6, 'eop_cash': 11.0, 'eop_runway': 15},
    ]

    # FinStream Technologies - FinTech with conservative growth
    finstream_data = [
        # 2022
        {'year': 2022, 'quarter': 1, 'revenue': 1.2, 'arr': 4.8, 'arr_projection': 6.5, 'headcount': 22, 'gross_profit': 0.96, 'gross_profit_percent': 77, 'sales_marketing': 0.5, 'research_development': 0.35, 'general_administrative': 0.2, 'eop_cash': 4.0, 'eop_runway': 13},
        {'year': 2022, 'quarter': 2, 'revenue': 1.4, 'arr': 5.6, 'arr_projection': 6.5, 'headcount': 24, 'gross_profit': 1.08, 'gross_profit_percent': 77, 'sales_marketing': 0.55, 'research_development': 0.38, 'general_administrative': 0.22, 'eop_cash': 3.8, 'eop_runway': 12},
        {'year': 2022, 'quarter': 3, 'revenue': 1.6, 'arr': 6.4, 'arr_projection': 6.5, 'headcount': 26, 'gross_profit': 1.23, 'gross_profit_percent': 77, 'sales_marketing': 0.6, 'research_development': 0.42, 'general_administrative': 0.24, 'eop_cash': 3.5, 'eop_runway': 11},
        {'year': 2022, 'quarter': 4, 'revenue': 1.9, 'arr': 7.6, 'arr_projection': 10.0, 'headcount': 28, 'gross_profit': 1.46, 'gross_profit_percent': 77, 'sales_marketing': 0.7, 'research_development': 0.48, 'general_administrative': 0.27, 'eop_cash': 6.0, 'eop_runway': 14},
        # 2023
        {'year': 2023, 'quarter': 1, 'revenue': 2.2, 'arr': 8.8, 'arr_projection': 10.0, 'headcount': 31, 'gross_profit': 1.69, 'gross_profit_percent': 77, 'sales_marketing': 0.8, 'research_development': 0.55, 'general_administrative': 0.3, 'eop_cash': 5.8, 'eop_runway': 13},
        {'year': 2023, 'quarter': 2, 'revenue': 2.5, 'arr': 10.0, 'arr_projection': 10.0, 'headcount': 34, 'gross_profit': 1.93, 'gross_profit_percent': 77, 'sales_marketing': 0.9, 'research_development': 0.62, 'general_administrative': 0.33, 'eop_cash': 5.5, 'eop_runway': 12},
        {'year': 2023, 'quarter': 3, 'revenue': 2.9, 'arr': 11.6, 'arr_projection': 10.0, 'headcount': 37, 'gross_profit': 2.23, 'gross_profit_percent': 77, 'sales_marketing': 1.05, 'research_development': 0.72, 'general_administrative': 0.36, 'eop_cash': 5.2, 'eop_runway': 11},
        {'year': 2023, 'quarter': 4, 'revenue': 3.3, 'arr': 13.2, 'arr_projection': 16.0, 'headcount': 40, 'gross_profit': 2.54, 'gross_profit_percent': 77, 'sales_marketing': 1.2, 'research_development': 0.82, 'general_administrative': 0.4, 'eop_cash': 7.8, 'eop_runway': 13},
        # 2024
        {'year': 2024, 'quarter': 1, 'revenue': 3.8, 'arr': 15.2, 'arr_projection': 16.0, 'headcount': 44, 'gross_profit': 2.93, 'gross_profit_percent': 77, 'sales_marketing': 1.4, 'research_development': 0.95, 'general_administrative': 0.45, 'eop_cash': 7.5, 'eop_runway': 12},
        {'year': 2024, 'quarter': 2, 'revenue': 4.2, 'arr': 16.8, 'arr_projection': 16.0, 'headcount': 48, 'gross_profit': 3.23, 'gross_profit_percent': 77, 'sales_marketing': 1.55, 'research_development': 1.05, 'general_administrative': 0.48, 'eop_cash': 7.2, 'eop_runway': 11},
        {'year': 2024, 'quarter': 3, 'revenue': 4.7, 'arr': 18.8, 'arr_projection': 16.0, 'headcount': 52, 'gross_profit': 3.62, 'gross_profit_percent': 77, 'sales_marketing': 1.75, 'research_development': 1.18, 'general_administrative': 0.52, 'eop_cash': 7.0, 'eop_runway': 10},
        {'year': 2024, 'quarter': 4, 'revenue': 5.2, 'arr': 20.8, 'arr_projection': 28.0, 'headcount': 55, 'gross_profit': 4.0, 'gross_profit_percent': 77, 'sales_marketing': 1.9, 'research_development': 1.3, 'general_administrative': 0.55, 'eop_cash': 10.5, 'eop_runway': 13},
    ]

    # Add all quarterly data
    for data in cloudsync_data:
        qd = QuarterlyData(company_id=companies[0].id, **data)
        db.session.add(qd)

    for data in dataflow_data:
        qd = QuarterlyData(company_id=companies[1].id, **data)
        db.session.add(qd)

    for data in secureauth_data:
        qd = QuarterlyData(company_id=companies[2].id, **data)
        db.session.add(qd)

    for data in marketpulse_data:
        qd = QuarterlyData(company_id=companies[3].id, **data)
        db.session.add(qd)

    for data in finstream_data:
        qd = QuarterlyData(company_id=companies[4].id, **data)
        db.session.add(qd)

    db.session.commit()

    print("\n✓ Sample data created!")
    print(f"  - 3 companies")
    print(f"  - 6 quarters of historical data per company")
    print("="*60 + "\n")


# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    with app.app_context():
        init_db()

    print("="*60)
    print("GREATPOINT VENTURES PORTFOLIO MANAGEMENT SYSTEM - VERSION 2.0")
    print("="*60)
    print("\n🌐 Access the application at: http://localhost:5003\n")
    print("📊 PAGES:")
    print("  1. Main Dashboard:         /dashboard/overview")
    print("  2. Revenue & ARR History:  /dashboard/revenue-arr-by-fund")
    print("  3. Company Metrics:        /dashboard/company-metrics")
    print("  4. Form Management:        /forms/manage")
    print("  5. Company Database:       /admin/companies")
    print("\n" + "="*60)
    print("Press CTRL+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5003)
