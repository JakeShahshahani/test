import os
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from app import db
from app.models import Company, QuarterlyMetrics, Document
from app.excel_handler import ExcelHandler
from app.parser import DataParser
from app.analytics import DueDiligenceAnalytics
from config import Config

bp = Blueprint('main', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ==================== WEB ROUTES ====================

@bp.route('/')
def index():
    """Main dashboard"""
    portfolio_data = DueDiligenceAnalytics.get_portfolio_overview()
    return render_template('index.html', portfolio=portfolio_data)


@bp.route('/company/<int:company_id>')
def company_detail(company_id):
    """Company detail page"""
    company = Company.query.get_or_404(company_id)
    health = DueDiligenceAnalytics.get_company_health_score(company_id)
    trends = DueDiligenceAnalytics.get_growth_trends(company_id)
    metrics = QuarterlyMetrics.query.filter_by(company_id=company_id).order_by(
        QuarterlyMetrics.year.desc(), QuarterlyMetrics.quarter.desc()
    ).all()
    documents = Document.query.filter_by(company_id=company_id).order_by(
        Document.upload_date.desc()
    ).all()

    return render_template('company.html',
                         company=company,
                         health=health,
                         trends=trends,
                         metrics=metrics,
                         documents=documents)


@bp.route('/upload')
def upload_page():
    """File upload page"""
    companies = Company.query.order_by(Company.name).all()
    return render_template('upload.html', companies=companies)


# ==================== API ROUTES - COMPANIES ====================

@bp.route('/api/companies', methods=['GET', 'POST'])
def companies():
    """Get all companies or create new company"""
    if request.method == 'GET':
        companies = Company.query.order_by(Company.name).all()
        return jsonify([c.to_dict() for c in companies])

    elif request.method == 'POST':
        data = request.get_json()

        if not data.get('name'):
            return jsonify({'error': 'Company name is required'}), 400

        # Check if company already exists
        existing = Company.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': 'Company already exists'}), 400

        company = Company(
            name=data['name'],
            industry=data.get('industry'),
            stage=data.get('stage'),
            investment_date=datetime.strptime(data['investment_date'], '%Y-%m-%d').date() if data.get('investment_date') else None,
            description=data.get('description')
        )

        db.session.add(company)
        db.session.commit()

        return jsonify(company.to_dict()), 201


@bp.route('/api/companies/<int:company_id>', methods=['GET', 'PUT', 'DELETE'])
def company(company_id):
    """Get, update, or delete a specific company"""
    company = Company.query.get_or_404(company_id)

    if request.method == 'GET':
        return jsonify(company.to_dict())

    elif request.method == 'PUT':
        data = request.get_json()

        if 'name' in data:
            company.name = data['name']
        if 'industry' in data:
            company.industry = data['industry']
        if 'stage' in data:
            company.stage = data['stage']
        if 'investment_date' in data:
            company.investment_date = datetime.strptime(data['investment_date'], '%Y-%m-%d').date()
        if 'description' in data:
            company.description = data['description']

        db.session.commit()
        return jsonify(company.to_dict())

    elif request.method == 'DELETE':
        db.session.delete(company)
        db.session.commit()
        return jsonify({'message': 'Company deleted successfully'}), 200


# ==================== API ROUTES - METRICS ====================

@bp.route('/api/companies/<int:company_id>/metrics', methods=['GET', 'POST'])
def company_metrics(company_id):
    """Get or add metrics for a company"""
    company = Company.query.get_or_404(company_id)

    if request.method == 'GET':
        metrics = QuarterlyMetrics.query.filter_by(company_id=company_id).order_by(
            QuarterlyMetrics.year.desc(), QuarterlyMetrics.quarter.desc()
        ).all()
        return jsonify([m.to_dict() for m in metrics])

    elif request.method == 'POST':
        data = request.get_json()

        # Check if metrics already exist for this quarter
        existing = QuarterlyMetrics.query.filter_by(
            company_id=company_id,
            year=data['year'],
            quarter=data['quarter']
        ).first()

        if existing:
            # Update existing
            for key in ['revenue', 'arr', 'carr', 'larr', 'gross_margin', 'burn_rate', 'cash_balance', 'customer_count', 'notes']:
                if key in data:
                    setattr(existing, key, data[key])
            metric = existing
        else:
            # Create new
            metric = QuarterlyMetrics(
                company_id=company_id,
                year=data['year'],
                quarter=data['quarter'],
                revenue=data.get('revenue'),
                arr=data.get('arr'),
                carr=data.get('carr'),
                larr=data.get('larr'),
                gross_margin=data.get('gross_margin'),
                burn_rate=data.get('burn_rate'),
                cash_balance=data.get('cash_balance'),
                customer_count=data.get('customer_count'),
                notes=data.get('notes')
            )
            db.session.add(metric)

        db.session.commit()
        return jsonify(metric.to_dict()), 201


@bp.route('/api/metrics/<int:metric_id>', methods=['GET', 'PUT', 'DELETE'])
def metric(metric_id):
    """Get, update, or delete a specific metric"""
    metric = QuarterlyMetrics.query.get_or_404(metric_id)

    if request.method == 'GET':
        return jsonify(metric.to_dict())

    elif request.method == 'PUT':
        data = request.get_json()

        for key in ['year', 'quarter', 'revenue', 'arr', 'carr', 'larr', 'gross_margin', 'burn_rate', 'cash_balance', 'customer_count', 'notes']:
            if key in data:
                setattr(metric, key, data[key])

        db.session.commit()
        return jsonify(metric.to_dict())

    elif request.method == 'DELETE':
        db.session.delete(metric)
        db.session.commit()
        return jsonify({'message': 'Metric deleted successfully'}), 200


# ==================== API ROUTES - FILE UPLOAD ====================

@bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and parsing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    company_id = request.form.get('company_id')
    year = request.form.get('year')
    quarter = request.form.get('quarter')
    document_type = request.form.get('document_type', 'other')

    if not company_id:
        return jsonify({'error': 'Company ID is required'}), 400

    company = Company.query.get(company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Save file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{company_id}_{timestamp}_{filename}"
    file_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    file_extension = filename.rsplit('.', 1)[1].lower()
    file_size = os.path.getsize(file_path)

    # Create document record
    document = Document(
        company_id=company_id,
        filename=unique_filename,
        original_filename=filename,
        file_type=file_extension,
        file_size=file_size,
        year=int(year) if year else None,
        quarter=int(quarter) if quarter else None,
        document_type=document_type
    )
    db.session.add(document)
    db.session.commit()

    # Parse file if it contains metrics
    parse_result = None
    if file_extension in ['xlsx', 'xls']:
        parse_result = ExcelHandler.parse_metrics_from_excel(file_path, company_id)
    elif file_extension == 'csv':
        parse_result = DataParser.parse_csv(file_path, company_id)
    elif file_extension == 'pdf' and document_type == 'quarterly_deck':
        parse_result = DataParser.parse_pdf_for_metrics(file_path, company_id)

    # Save parsed metrics to database
    metrics_saved = 0
    if parse_result and parse_result.get('success'):
        validation = DataParser.validate_metrics_data(parse_result['data'])

        if validation['valid']:
            for metric_data in validation['valid_metrics']:
                # Check if metrics already exist
                existing = QuarterlyMetrics.query.filter_by(
                    company_id=company_id,
                    year=metric_data['year'],
                    quarter=metric_data['quarter']
                ).first()

                if existing:
                    # Update existing
                    for key, value in metric_data.items():
                        if key not in ['company_id', 'year', 'quarter'] and value is not None:
                            setattr(existing, key, value)
                else:
                    # Create new
                    metric = QuarterlyMetrics(**metric_data)
                    db.session.add(metric)

                metrics_saved += 1

            db.session.commit()

    return jsonify({
        'message': 'File uploaded successfully',
        'document': document.to_dict(),
        'metrics_parsed': metrics_saved,
        'parse_result': parse_result
    }), 201


# ==================== API ROUTES - ANALYTICS ====================

@bp.route('/api/companies/<int:company_id>/health')
def company_health(company_id):
    """Get company health score"""
    company = Company.query.get_or_404(company_id)
    health = DueDiligenceAnalytics.get_company_health_score(company_id)
    return jsonify(health)


@bp.route('/api/companies/<int:company_id>/trends')
def company_trends(company_id):
    """Get company growth trends"""
    company = Company.query.get_or_404(company_id)
    periods = request.args.get('periods', 8, type=int)
    trends = DueDiligenceAnalytics.get_growth_trends(company_id, periods)
    return jsonify(trends)


@bp.route('/api/portfolio/overview')
def portfolio_overview():
    """Get portfolio overview"""
    overview = DueDiligenceAnalytics.get_portfolio_overview()
    return jsonify(overview)


# ==================== API ROUTES - EXCEL EXPORT ====================

@bp.route('/api/companies/<int:company_id>/export')
def export_company(company_id):
    """Export company metrics to Excel"""
    company = Company.query.get_or_404(company_id)

    try:
        file_path = ExcelHandler.export_company_metrics(company)
        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/portfolio/export')
def export_portfolio():
    """Export entire portfolio to Excel"""
    try:
        file_path = ExcelHandler.export_all_companies()
        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
