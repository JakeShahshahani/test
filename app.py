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

    print("\n✓ Sample data created successfully!")
    print(f"  - 3 Funds (Fund 1, Fund 2, Fund 3)")
    print(f"  - 5 Portfolio Companies")
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
