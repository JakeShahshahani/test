from datetime import datetime
from app import db

class Company(db.Model):
    """Portfolio company model"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    industry = db.Column(db.String(100))
    stage = db.Column(db.String(50))  # Seed, Series A, Series B, etc.
    investment_date = db.Column(db.Date)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    metrics = db.relationship('QuarterlyMetrics', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='company', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Company {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'stage': self.stage,
            'investment_date': self.investment_date.isoformat() if self.investment_date else None,
            'description': self.description
        }


class QuarterlyMetrics(db.Model):
    """Quarterly financial metrics for portfolio companies"""
    __tablename__ = 'quarterly_metrics'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4

    # Financial metrics
    revenue = db.Column(db.Float)
    arr = db.Column(db.Float)  # Annual Recurring Revenue
    carr = db.Column(db.Float)  # Committed Annual Recurring Revenue
    larr = db.Column(db.Float)  # Linear Annual Recurring Revenue

    # Additional metrics
    gross_margin = db.Column(db.Float)
    burn_rate = db.Column(db.Float)
    cash_balance = db.Column(db.Float)
    customer_count = db.Column(db.Integer)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one entry per company per quarter
    __table_args__ = (db.UniqueConstraint('company_id', 'year', 'quarter', name='_company_quarter_uc'),)

    def __repr__(self):
        return f'<QuarterlyMetrics {self.company.name} Q{self.quarter} {self.year}>'

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
            'carr': self.carr,
            'larr': self.larr,
            'gross_margin': self.gross_margin,
            'burn_rate': self.burn_rate,
            'cash_balance': self.cash_balance,
            'customer_count': self.customer_count,
            'notes': self.notes
        }


class Document(db.Model):
    """Uploaded documents (quarterly decks, financial reports, etc.)"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # pdf, xlsx, csv
    file_size = db.Column(db.Integer)  # in bytes
    year = db.Column(db.Integer)
    quarter = db.Column(db.Integer)
    document_type = db.Column(db.String(50))  # 'quarterly_deck', 'financial_report', 'other'
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Document {self.original_filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.name,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'year': self.year,
            'quarter': self.quarter,
            'document_type': self.document_type,
            'upload_date': self.upload_date.isoformat()
        }
