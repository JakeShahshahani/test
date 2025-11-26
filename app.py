#!/usr/bin/env python3
"""
Simple VC Portfolio Management System
Fully functional with working dashboards and forms
"""
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize database
db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class Company(db.Model):
    """Portfolio company"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)

    # Relationships
    metrics = db.relationship('CompanyMetrics', backref='company', lazy='dynamic')
    revenues = db.relationship('QuarterlyRevenue', backref='company', lazy='dynamic')

    def __repr__(self):
        return f'<Company {self.name}>'


class CompanyMetrics(db.Model):
    """Company financial metrics"""
    __tablename__ = 'company_metrics'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Financial metrics
    arr = db.Column(db.Float, default=0)
    headcount = db.Column(db.Integer, default=0)
    gross_profit = db.Column(db.Float, default=0)
    gross_profit_percent = db.Column(db.Float, default=0)
    sales_marketing = db.Column(db.Float, default=0)
    research_development = db.Column(db.Float, default=0)
    general_administrative = db.Column(db.Float, default=0)
    eop_cash = db.Column(db.Float, default=0)
    eop_runway = db.Column(db.Float, default=0)  # in months

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Metrics for {self.company.name}>'


class QuarterlyRevenue(db.Model):
    """Quarterly revenue tracking"""
    __tablename__ = 'quarterly_revenue'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4
    revenue = db.Column(db.Float, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('company_id', 'year', 'quarter', name='_company_quarter_uc'),)

    def __repr__(self):
        return f'<Revenue {self.company.name} Q{self.quarter} {self.year}: ${self.revenue}>'


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Homepage - redirect to portfolio metrics dashboard"""
    return redirect(url_for('portfolio_metrics'))


@app.route('/dashboard/portfolio-metrics')
def portfolio_metrics():
    """Dashboard #1: Portfolio Metrics Dashboard"""
    companies = Company.query.all()

    portfolio_data = []
    for company in companies:
        metrics = CompanyMetrics.query.filter_by(company_id=company.id).first()

        if metrics:
            portfolio_data.append({
                'id': company.id,
                'name': company.name,
                'arr': metrics.arr,
                'headcount': metrics.headcount,
                'gross_profit': metrics.gross_profit,
                'gross_profit_percent': metrics.gross_profit_percent,
                'sales_marketing': metrics.sales_marketing,
                'research_development': metrics.research_development,
                'general_administrative': metrics.general_administrative,
                'eop_cash': metrics.eop_cash,
                'eop_runway': metrics.eop_runway,
                'updated_at': metrics.updated_at
            })
        else:
            # Company exists but no metrics yet
            portfolio_data.append({
                'id': company.id,
                'name': company.name,
                'arr': 0,
                'headcount': 0,
                'gross_profit': 0,
                'gross_profit_percent': 0,
                'sales_marketing': 0,
                'research_development': 0,
                'general_administrative': 0,
                'eop_cash': 0,
                'eop_runway': 0,
                'updated_at': None
            })

    return render_template('portfolio_metrics.html', portfolio_data=portfolio_data)


@app.route('/dashboard/revenue-tracking')
def revenue_tracking():
    """Dashboard #2: Revenue Tracking Dashboard"""
    companies = Company.query.all()

    revenue_data = []
    for company in companies:
        # Get all revenue records for this company
        revenues = QuarterlyRevenue.query.filter_by(company_id=company.id).order_by(
            QuarterlyRevenue.year.desc(), QuarterlyRevenue.quarter.desc()
        ).all()

        if revenues:
            latest_revenue = revenues[0]
            historical = [
                {
                    'period': f'Q{rev.quarter} {rev.year}',
                    'revenue': rev.revenue,
                    'year': rev.year,
                    'quarter': rev.quarter
                }
                for rev in reversed(revenues)  # Chronological order for chart
            ]

            revenue_data.append({
                'company_name': company.name,
                'latest_revenue': latest_revenue.revenue,
                'latest_period': f'Q{latest_revenue.quarter} {latest_revenue.year}',
                'historical': historical
            })
        else:
            revenue_data.append({
                'company_name': company.name,
                'latest_revenue': 0,
                'latest_period': 'N/A',
                'historical': []
            })

    return render_template('revenue_tracking.html', revenue_data=revenue_data)


@app.route('/form/submit-revenue', methods=['GET', 'POST'])
def submit_revenue():
    """Form for submitting quarterly revenue"""
    companies = Company.query.order_by(Company.name).all()

    if request.method == 'POST':
        company_id = request.form.get('company_id')
        year = request.form.get('year')
        quarter = request.form.get('quarter')
        revenue = request.form.get('revenue')

        # Validate
        if not all([company_id, year, quarter, revenue]):
            return render_template('submit_revenue.html',
                                 companies=companies,
                                 error='All fields are required')

        try:
            company_id = int(company_id)
            year = int(year)
            quarter = int(quarter)
            revenue = float(revenue)

            if quarter not in [1, 2, 3, 4]:
                raise ValueError('Quarter must be 1-4')

        except ValueError as e:
            return render_template('submit_revenue.html',
                                 companies=companies,
                                 error=f'Invalid input: {str(e)}')

        # Check if revenue already exists for this company/quarter
        existing = QuarterlyRevenue.query.filter_by(
            company_id=company_id,
            year=year,
            quarter=quarter
        ).first()

        if existing:
            # Update existing
            existing.revenue = revenue
            existing.submitted_at = datetime.utcnow()
            message = 'Revenue updated successfully!'
        else:
            # Create new
            new_revenue = QuarterlyRevenue(
                company_id=company_id,
                year=year,
                quarter=quarter,
                revenue=revenue
            )
            db.session.add(new_revenue)
            message = 'Revenue submitted successfully!'

        db.session.commit()

        return render_template('submit_revenue.html',
                             companies=companies,
                             success=message)

    return render_template('submit_revenue.html', companies=companies)


@app.route('/admin/add-company', methods=['GET', 'POST'])
def add_company():
    """Admin: Add a new company"""
    if request.method == 'POST':
        company_name = request.form.get('company_name', '').strip()

        if not company_name:
            return render_template('add_company.html', error='Company name is required')

        # Check if exists
        existing = Company.query.filter_by(name=company_name).first()
        if existing:
            return render_template('add_company.html', error='Company already exists')

        # Create company
        company = Company(name=company_name)
        db.session.add(company)

        # Create empty metrics record
        metrics = CompanyMetrics(company=company)
        db.session.add(metrics)

        db.session.commit()

        return render_template('add_company.html', success=f'Company "{company_name}" added successfully!')

    return render_template('add_company.html')


@app.route('/admin/update-metrics/<int:company_id>', methods=['GET', 'POST'])
def update_metrics(company_id):
    """Admin: Update company metrics"""
    company = Company.query.get_or_404(company_id)
    metrics = CompanyMetrics.query.filter_by(company_id=company_id).first()

    if not metrics:
        # Create if doesn't exist
        metrics = CompanyMetrics(company_id=company_id)
        db.session.add(metrics)
        db.session.commit()

    if request.method == 'POST':
        try:
            metrics.arr = float(request.form.get('arr', 0))
            metrics.headcount = int(request.form.get('headcount', 0))
            metrics.gross_profit = float(request.form.get('gross_profit', 0))
            metrics.gross_profit_percent = float(request.form.get('gross_profit_percent', 0))
            metrics.sales_marketing = float(request.form.get('sales_marketing', 0))
            metrics.research_development = float(request.form.get('research_development', 0))
            metrics.general_administrative = float(request.form.get('general_administrative', 0))
            metrics.eop_cash = float(request.form.get('eop_cash', 0))
            metrics.eop_runway = float(request.form.get('eop_runway', 0))

            db.session.commit()

            return render_template('update_metrics.html',
                                 company=company,
                                 metrics=metrics,
                                 success='Metrics updated successfully!')
        except ValueError as e:
            return render_template('update_metrics.html',
                                 company=company,
                                 metrics=metrics,
                                 error=f'Invalid input: {str(e)}')

    return render_template('update_metrics.html', company=company, metrics=metrics)


# ==================== INITIALIZATION ====================

def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        # Create tables
        db.create_all()

        # Check if we need sample data
        if Company.query.count() == 0:
            print("Creating sample data...")

            # Sample companies
            companies_data = [
                'TechCorp Inc',
                'DataFlow Systems',
                'CloudVenture Ltd'
            ]

            for company_name in companies_data:
                company = Company(name=company_name)
                db.session.add(company)
                db.session.flush()  # Get company ID

                # Add sample metrics
                metrics = CompanyMetrics(
                    company_id=company.id,
                    arr=1000000 * (company.id),
                    headcount=50 * company.id,
                    gross_profit=700000 * company.id,
                    gross_profit_percent=70.0,
                    sales_marketing=200000 * company.id,
                    research_development=150000 * company.id,
                    general_administrative=100000 * company.id,
                    eop_cash=2000000 * company.id,
                    eop_runway=18.0
                )
                db.session.add(metrics)

                # Add sample revenue data
                for q in range(1, 5):
                    revenue = QuarterlyRevenue(
                        company_id=company.id,
                        year=2024,
                        quarter=q,
                        revenue=250000 * q * company.id
                    )
                    db.session.add(revenue)

            db.session.commit()
            print("Sample data created!")
        else:
            print("Database already populated")


if __name__ == '__main__':
    init_db()

    print("=" * 60)
    print("VC Portfolio Management System")
    print("=" * 60)
    print("\nStarting server...")
    print("Access the application at: http://localhost:5001")
    print("\nDashboards:")
    print("  - Portfolio Metrics: http://localhost:5001/dashboard/portfolio-metrics")
    print("  - Revenue Tracking:  http://localhost:5001/dashboard/revenue-tracking")
    print("\nForms:")
    print("  - Submit Revenue:    http://localhost:5001/form/submit-revenue")
    print("  - Add Company:       http://localhost:5001/admin/add-company")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60)
    print()

    app.run(debug=True, host='0.0.0.0', port=5001)
