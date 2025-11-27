#!/usr/bin/env python3
"""
Complete VC Portfolio Management System
With Google Form Integration, Multiple Dashboards, and Visualizations
"""
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'vc-portfolio-secret-key-2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize database
db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class Company(db.Model):
    """Portfolio company"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    industry = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    quarterly_data = db.relationship('QuarterlyData', backref='company', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Company {self.name}>'


class QuarterlyData(db.Model):
    """Complete quarterly financial data for each company"""
    __tablename__ = 'quarterly_data'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4

    # Core metrics
    revenue = db.Column(db.Float, default=0)
    arr = db.Column(db.Float, default=0)  # Annual Recurring Revenue

    # Additional metrics
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

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.name,
            'year': self.year,
            'quarter': self.quarter,
            'period': f'Q{self.quarter} {self.year}',
            'revenue': self.revenue,
            'arr': self.arr,
            'headcount': self.headcount,
            'gross_profit': self.gross_profit,
            'gross_profit_percent': self.gross_profit_percent,
            'sales_marketing': self.sales_marketing,
            'research_development': self.research_development,
            'general_administrative': self.general_administrative,
            'eop_cash': self.eop_cash,
            'eop_runway': self.eop_runway,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }

    def __repr__(self):
        return f'<QuarterlyData {self.company.name} Q{self.quarter} {self.year}>'


# ==================== HELPER FUNCTIONS ====================

def get_latest_data_for_company(company_id):
    """Get the most recent quarterly data for a company"""
    return QuarterlyData.query.filter_by(company_id=company_id).order_by(
        desc(QuarterlyData.year), desc(QuarterlyData.quarter)
    ).first()


def get_all_historical_data(company_id):
    """Get all historical quarterly data for a company, sorted chronologically"""
    return QuarterlyData.query.filter_by(company_id=company_id).order_by(
        QuarterlyData.year.asc(), QuarterlyData.quarter.asc()
    ).all()


def calculate_qoq_growth(current, previous):
    """Calculate quarter-over-quarter growth percentage"""
    if previous and previous > 0:
        return ((current - previous) / previous) * 100
    return 0


# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    """Homepage - redirect to current metrics dashboard"""
    return redirect(url_for('dashboard_current'))


# ==================== DASHBOARD 1: CURRENT METRICS ====================

@app.route('/dashboard/current')
def dashboard_current():
    """Dashboard showing latest quarterly metrics for all companies"""
    companies = Company.query.order_by(Company.name).all()

    current_data = []
    for company in companies:
        latest = get_latest_data_for_company(company.id)

        if latest:
            # Get previous quarter for growth calculation
            all_data = get_all_historical_data(company.id)
            previous = all_data[-2] if len(all_data) >= 2 else None

            revenue_growth = calculate_qoq_growth(latest.revenue, previous.revenue if previous else 0)
            arr_growth = calculate_qoq_growth(latest.arr, previous.arr if previous else 0)

            current_data.append({
                'company_id': company.id,
                'company_name': company.name,
                'industry': company.industry,
                'period': f'Q{latest.quarter} {latest.year}',
                'revenue': latest.revenue,
                'arr': latest.arr,
                'revenue_growth': revenue_growth,
                'arr_growth': arr_growth,
                'headcount': latest.headcount,
                'gross_profit_percent': latest.gross_profit_percent,
                'eop_cash': latest.eop_cash,
                'eop_runway': latest.eop_runway
            })
        else:
            current_data.append({
                'company_id': company.id,
                'company_name': company.name,
                'industry': company.industry,
                'period': 'No data',
                'revenue': 0,
                'arr': 0,
                'revenue_growth': 0,
                'arr_growth': 0,
                'headcount': 0,
                'gross_profit_percent': 0,
                'eop_cash': 0,
                'eop_runway': 0
            })

    return render_template('dashboard_current.html', current_data=current_data)


# ==================== DASHBOARD 2: REVENUE & ARR HISTORY ====================

@app.route('/dashboard/revenue-arr-history')
def dashboard_revenue_arr():
    """Dashboard showing historical revenue and ARR for all companies"""
    companies = Company.query.order_by(Company.name).all()

    company_histories = []
    for company in companies:
        historical_data = get_all_historical_data(company.id)

        if historical_data:
            history = []
            for i, data in enumerate(historical_data):
                prev_data = historical_data[i-1] if i > 0 else None

                history.append({
                    'period': f'Q{data.quarter} {data.year}',
                    'year': data.year,
                    'quarter': data.quarter,
                    'revenue': data.revenue,
                    'arr': data.arr,
                    'revenue_growth': calculate_qoq_growth(data.revenue, prev_data.revenue if prev_data else 0),
                    'arr_growth': calculate_qoq_growth(data.arr, prev_data.arr if prev_data else 0)
                })

            company_histories.append({
                'company_id': company.id,
                'company_name': company.name,
                'history': history
            })

    return render_template('dashboard_revenue_arr.html', company_histories=company_histories)


# ==================== DASHBOARD 3: FULL METRICS HISTORY ====================

@app.route('/dashboard/full-metrics-history')
def dashboard_full_metrics():
    """Dashboard showing complete historical metrics for all companies"""
    companies = Company.query.order_by(Company.name).all()

    company_metrics = []
    for company in companies:
        historical_data = get_all_historical_data(company.id)

        if historical_data:
            metrics = [data.to_dict() for data in historical_data]
            company_metrics.append({
                'company_id': company.id,
                'company_name': company.name,
                'metrics': metrics
            })

    return render_template('dashboard_full_metrics.html', company_metrics=company_metrics)


# ==================== DASHBOARD 4: GOOGLE FORM INTEGRATION ====================

@app.route('/dashboard/google-form')
def dashboard_google_form():
    """Dashboard for Google Form integration"""
    companies = Company.query.order_by(Company.name).all()

    # Generate form URL for instructions
    base_url = request.url_root
    webhook_url = f"{base_url}api/google-form-submit"

    return render_template('dashboard_google_form.html',
                         companies=companies,
                         webhook_url=webhook_url)


@app.route('/api/google-form-submit', methods=['POST'])
def google_form_submit():
    """
    API endpoint to receive data from Google Forms
    This endpoint accepts form submissions and saves them to the database
    """
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()

        # Extract data (adjust field names based on your Google Form)
        company_name = data.get('company_name') or data.get('Company Name')
        year = int(data.get('year') or data.get('Year'))
        quarter = int(data.get('quarter') or data.get('Quarter'))
        revenue = float(data.get('revenue') or data.get('Revenue') or 0)
        arr = float(data.get('arr') or data.get('ARR') or 0)

        # Optional fields
        headcount = int(data.get('headcount') or data.get('Headcount') or 0)
        gross_profit = float(data.get('gross_profit') or data.get('Gross Profit') or 0)
        gross_profit_percent = float(data.get('gross_profit_percent') or data.get('Gross Profit %') or 0)
        sales_marketing = float(data.get('sales_marketing') or data.get('Sales & Marketing') or 0)
        research_development = float(data.get('research_development') or data.get('R&D') or 0)
        general_administrative = float(data.get('general_administrative') or data.get('G&A') or 0)
        eop_cash = float(data.get('eop_cash') or data.get('EOP Cash') or 0)
        eop_runway = float(data.get('eop_runway') or data.get('EOP Runway') or 0)

        # Find or create company
        company = Company.query.filter_by(name=company_name).first()
        if not company:
            company = Company(name=company_name)
            db.session.add(company)
            db.session.flush()

        # Check if quarterly data already exists
        existing = QuarterlyData.query.filter_by(
            company_id=company.id,
            year=year,
            quarter=quarter
        ).first()

        if existing:
            # Update existing
            existing.revenue = revenue
            existing.arr = arr
            existing.headcount = headcount
            existing.gross_profit = gross_profit
            existing.gross_profit_percent = gross_profit_percent
            existing.sales_marketing = sales_marketing
            existing.research_development = research_development
            existing.general_administrative = general_administrative
            existing.eop_cash = eop_cash
            existing.eop_runway = eop_runway
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            quarterly_data = QuarterlyData(
                company_id=company.id,
                year=year,
                quarter=quarter,
                revenue=revenue,
                arr=arr,
                headcount=headcount,
                gross_profit=gross_profit,
                gross_profit_percent=gross_profit_percent,
                sales_marketing=sales_marketing,
                research_development=research_development,
                general_administrative=general_administrative,
                eop_cash=eop_cash,
                eop_runway=eop_runway
            )
            db.session.add(quarterly_data)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Data saved for {company_name} Q{quarter} {year}'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


# ==================== MANUAL ENTRY SECTION ====================

@app.route('/manual/add-company', methods=['GET', 'POST'])
def manual_add_company():
    """Manually add a new portfolio company"""
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()
        industry = request.form.get('industry', '').strip()

        if not company_name:
            return render_template('manual_add_company.html', error='Company name is required')

        existing = Company.query.filter_by(name=company_name).first()
        if existing:
            return render_template('manual_add_company.html', error='Company already exists')

        company = Company(name=company_name, industry=industry)
        db.session.add(company)
        db.session.commit()

        return redirect(url_for('manual_enter_data', company_id=company.id))

    return render_template('manual_add_company.html')


@app.route('/manual/enter-data/<int:company_id>', methods=['GET', 'POST'])
def manual_enter_data(company_id):
    """Manually enter quarterly data for a company"""
    company = Company.query.get_or_404(company_id)

    if request.method == 'POST':
        try:
            year = int(request.form.get('year'))
            quarter = int(request.form.get('quarter'))

            # Check if data exists
            existing = QuarterlyData.query.filter_by(
                company_id=company_id,
                year=year,
                quarter=quarter
            ).first()

            data_dict = {
                'revenue': float(request.form.get('revenue', 0)),
                'arr': float(request.form.get('arr', 0)),
                'headcount': int(request.form.get('headcount', 0)),
                'gross_profit': float(request.form.get('gross_profit', 0)),
                'gross_profit_percent': float(request.form.get('gross_profit_percent', 0)),
                'sales_marketing': float(request.form.get('sales_marketing', 0)),
                'research_development': float(request.form.get('research_development', 0)),
                'general_administrative': float(request.form.get('general_administrative', 0)),
                'eop_cash': float(request.form.get('eop_cash', 0)),
                'eop_runway': float(request.form.get('eop_runway', 0))
            }

            if existing:
                for key, value in data_dict.items():
                    setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                message = f'Data updated for Q{quarter} {year}'
            else:
                quarterly_data = QuarterlyData(
                    company_id=company_id,
                    year=year,
                    quarter=quarter,
                    **data_dict
                )
                db.session.add(quarterly_data)
                message = f'Data added for Q{quarter} {year}'

            db.session.commit()

            return render_template('manual_enter_data.html',
                                 company=company,
                                 success=message)

        except ValueError as e:
            return render_template('manual_enter_data.html',
                                 company=company,
                                 error=f'Invalid input: {str(e)}')

    return render_template('manual_enter_data.html', company=company)


@app.route('/manual/manage-companies')
def manual_manage_companies():
    """View and manage all companies"""
    companies = Company.query.order_by(Company.name).all()

    companies_data = []
    for company in companies:
        latest = get_latest_data_for_company(company.id)
        data_count = QuarterlyData.query.filter_by(company_id=company.id).count()

        companies_data.append({
            'id': company.id,
            'name': company.name,
            'industry': company.industry,
            'latest_period': f'Q{latest.quarter} {latest.year}' if latest else 'No data',
            'quarters_count': data_count
        })

    return render_template('manual_manage_companies.html', companies=companies_data)


# ==================== API ENDPOINTS FOR CHARTS ====================

@app.route('/api/company/<int:company_id>/revenue-arr-chart')
def api_revenue_arr_chart(company_id):
    """Get revenue and ARR data for charts"""
    historical_data = get_all_historical_data(company_id)

    labels = [f'Q{d.quarter} {d.year}' for d in historical_data]
    revenue_data = [d.revenue for d in historical_data]
    arr_data = [d.arr for d in historical_data]

    return jsonify({
        'labels': labels,
        'revenue': revenue_data,
        'arr': arr_data
    })


@app.route('/api/company/<int:company_id>/all-metrics-chart')
def api_all_metrics_chart(company_id):
    """Get all metrics data for comprehensive charts"""
    historical_data = get_all_historical_data(company_id)

    return jsonify({
        'labels': [f'Q{d.quarter} {d.year}' for d in historical_data],
        'revenue': [d.revenue for d in historical_data],
        'arr': [d.arr for d in historical_data],
        'headcount': [d.headcount for d in historical_data],
        'gross_profit': [d.gross_profit for d in historical_data],
        'gross_profit_percent': [d.gross_profit_percent for d in historical_data],
        'sales_marketing': [d.sales_marketing for d in historical_data],
        'research_development': [d.research_development for d in historical_data],
        'general_administrative': [d.general_administrative for d in historical_data],
        'eop_cash': [d.eop_cash for d in historical_data],
        'eop_runway': [d.eop_runway for d in historical_data]
    })


# ==================== INITIALIZATION ====================

def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        db.create_all()

        if Company.query.count() == 0:
            print("\n" + "="*60)
            print("Creating sample data...")
            print("="*60)

            # Create sample companies
            companies_data = [
                {'name': 'TechFlow AI', 'industry': 'Artificial Intelligence'},
                {'name': 'CloudScale Systems', 'industry': 'Cloud Infrastructure'},
                {'name': 'DataVision Analytics', 'industry': 'Data Analytics'}
            ]

            for comp_data in companies_data:
                company = Company(**comp_data)
                db.session.add(company)
                db.session.flush()

                # Add 6 quarters of historical data
                base_revenue = 500000
                base_arr = 2000000

                for year in [2023, 2024]:
                    for quarter in range(1, 5 if year == 2023 else 3):  # 2023: Q1-Q4, 2024: Q1-Q2
                        quarter_index = (year - 2023) * 4 + quarter

                        growth_factor = 1 + (quarter_index * 0.15)

                        quarterly_data = QuarterlyData(
                            company_id=company.id,
                            year=year,
                            quarter=quarter,
                            revenue=base_revenue * growth_factor * company.id,
                            arr=base_arr * growth_factor * company.id,
                            headcount=20 + (quarter_index * 5) * company.id,
                            gross_profit=base_revenue * growth_factor * company.id * 0.7,
                            gross_profit_percent=70 + (quarter_index * 2),
                            sales_marketing=100000 * growth_factor * company.id,
                            research_development=150000 * growth_factor * company.id,
                            general_administrative=80000 * growth_factor * company.id,
                            eop_cash=3000000 * growth_factor * company.id,
                            eop_runway=18 - (quarter_index * 0.5)
                        )
                        db.session.add(quarterly_data)

            db.session.commit()
            print("✓ Sample data created!")
            print("  - 3 companies")
            print("  - 6 quarters of historical data per company")
            print("="*60 + "\n")


if __name__ == '__main__':
    init_db()

    print("="*60)
    print("VC PORTFOLIO MANAGEMENT SYSTEM")
    print("="*60)
    print("\n🌐 Access the application at: http://localhost:5001\n")
    print("📊 DASHBOARDS:")
    print("  1. Current Metrics:      /dashboard/current")
    print("  2. Revenue & ARR History: /dashboard/revenue-arr-history")
    print("  3. Full Metrics History:  /dashboard/full-metrics-history")
    print("  4. Google Form Setup:     /dashboard/google-form")
    print("\n✏️  MANUAL ENTRY:")
    print("  - Add Company:           /manual/add-company")
    print("  - Manage Companies:      /manual/manage-companies")
    print("\n🔌 API:")
    print("  - Google Form Webhook:   /api/google-form-submit")
    print("\n" + "="*60)
    print("Press CTRL+C to stop\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
