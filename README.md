# VC Portfolio Management System

A comprehensive database system for venture capital firms to track portfolio company financial metrics and performance. The system enables portfolio companies to upload financial data and quarterly decks, which are automatically parsed and stored in structured Excel format for due diligence health analysis.

## Features

### 📊 Core Functionality
- **Portfolio Company Management**: Add, edit, and manage portfolio companies with detailed information
- **Quarterly Metrics Tracking**: Track historical and current financial metrics on a quarterly basis
  - Revenue
  - ARR (Annual Recurring Revenue)
  - cARR (Committed Annual Recurring Revenue)
  - LARR (Linear Annual Recurring Revenue)
  - Gross Margin
  - Burn Rate
  - Cash Balance
  - Customer Count

### 📤 Data Upload & Parsing
- **Multi-Format Support**: Upload files in Excel (.xlsx, .xls), CSV, or PDF formats
- **Automatic Parsing**: Intelligent data extraction from uploaded files
- **Quarterly Deck Support**: Upload and track quarterly presentation decks
- **Validation**: Automatic data validation before saving to database

### 📈 Analytics & Reporting
- **Health Score Calculation**: Automated company health scoring (0-100) based on:
  - Revenue growth trends
  - ARR growth trends
  - Gross margin performance
  - Cash runway analysis
  - Customer growth metrics
- **Growth Trends Analysis**: Quarter-over-quarter and year-over-year comparisons
- **Portfolio Overview**: Dashboard with portfolio-wide metrics and insights
- **Due Diligence Reports**: Comprehensive health analysis for investment decisions

### 📋 Excel Export
- **Structured Excel Output**: Export data in professionally formatted Excel files
- **Individual Company Export**: Detailed metrics for specific companies
- **Portfolio Export**: Comprehensive portfolio overview with all companies
- **Historical Data**: Complete historical tracking across all quarters

## Technology Stack

- **Backend**: Python 3.8+ with Flask web framework
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **Excel Processing**: pandas and openpyxl
- **PDF Parsing**: PyPDF2
- **Frontend**: HTML, CSS, JavaScript (vanilla)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd test
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   Open your browser and navigate to: `http://localhost:5000`

## Quick Start Guide

### 1. Add a Portfolio Company

1. Navigate to the Dashboard (home page)
2. Click "Add Company"
3. Fill in company details:
   - Name (required)
   - Industry
   - Stage (Seed, Series A, B, C, etc.)
   - Investment Date
   - Description
4. Click "Add Company"

### 2. Upload Financial Data

#### Option A: Upload Excel/CSV File

1. Click "Upload Data" in the navigation
2. Select the company from the dropdown
3. Choose document type: "Financial Report"
4. Select the file (use the provided format)
5. Click "Upload File"

**Excel/CSV Format:**
```csv
Year,Quarter,Revenue,ARR,cARR,LARR,Gross Margin,Burn Rate,Cash Balance,Customer Count
2024,1,1500000,6000000,7000000,6500000,0.72,200000,5000000,150
2024,2,1800000,7200000,8000000,7600000,0.75,180000,5200000,175
```

See `sample_data.csv` for a complete example.

#### Option B: Manual Entry

1. Navigate to a company's detail page
2. Click "Add Metrics"
3. Enter quarterly financial data manually
4. Click "Add Metrics"

### 3. View Analytics

1. Navigate to a company's detail page
2. View the **Health Score** (0-100 scale)
3. Review **Health Score Factors** to understand what drives the score
4. Examine **Quarterly Metrics** table for historical data
5. Export to Excel for further analysis

### 4. Export Data

**Export Single Company:**
- Navigate to company detail page
- Click "Export to Excel"
- Download the formatted Excel file

**Export Entire Portfolio:**
- From the navigation menu, click "Export Portfolio"
- Download comprehensive Excel file with all companies

## Project Structure

```
vc-portfolio-system/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── routes.py            # API endpoints and web routes
│   ├── parser.py            # Data parsing logic
│   ├── excel_handler.py     # Excel import/export
│   ├── analytics.py         # Due diligence analytics
│   └── templates/           # HTML templates
│       ├── base.html
│       ├── index.html       # Dashboard
│       ├── company.html     # Company detail page
│       └── upload.html      # Upload interface
├── database/                # SQLite database (auto-created)
├── uploads/                 # Uploaded files (auto-created)
├── exports/                 # Generated Excel files (auto-created)
├── config.py               # Application configuration
├── requirements.txt        # Python dependencies
├── run.py                  # Application entry point
├── sample_data.csv         # Sample data file
├── CLAUDE.md              # AI assistant guide
└── README.md              # This file
```

## Database Schema

### Companies Table
- `id`: Primary key
- `name`: Company name (unique)
- `industry`: Industry sector
- `stage`: Investment stage
- `investment_date`: Date of initial investment
- `description`: Company description
- `created_at`, `updated_at`: Timestamps

### QuarterlyMetrics Table
- `id`: Primary key
- `company_id`: Foreign key to Companies
- `year`: Year (e.g., 2024)
- `quarter`: Quarter (1-4)
- `revenue`: Quarterly revenue
- `arr`: Annual Recurring Revenue
- `carr`: Committed Annual Recurring Revenue
- `larr`: Linear Annual Recurring Revenue
- `gross_margin`: Gross margin (0-1)
- `burn_rate`: Monthly burn rate
- `cash_balance`: Cash on hand
- `customer_count`: Total customers
- `notes`: Additional notes
- `created_at`, `updated_at`: Timestamps

### Documents Table
- `id`: Primary key
- `company_id`: Foreign key to Companies
- `filename`: Stored filename
- `original_filename`: Original upload name
- `file_type`: File extension
- `file_size`: Size in bytes
- `year`, `quarter`: Associated period
- `document_type`: Type of document
- `upload_date`: Upload timestamp

## API Endpoints

### Companies
- `GET /api/companies` - List all companies
- `POST /api/companies` - Create new company
- `GET /api/companies/<id>` - Get company details
- `PUT /api/companies/<id>` - Update company
- `DELETE /api/companies/<id>` - Delete company

### Metrics
- `GET /api/companies/<id>/metrics` - Get company metrics
- `POST /api/companies/<id>/metrics` - Add/update metrics
- `PUT /api/metrics/<id>` - Update specific metric
- `DELETE /api/metrics/<id>` - Delete metric

### Analytics
- `GET /api/companies/<id>/health` - Get health score
- `GET /api/companies/<id>/trends` - Get growth trends
- `GET /api/portfolio/overview` - Get portfolio overview

### File Operations
- `POST /api/upload` - Upload file
- `GET /api/companies/<id>/export` - Export company to Excel
- `GET /api/portfolio/export` - Export portfolio to Excel

## Health Score Methodology

The health score (0-100) is calculated based on five factors:

1. **Revenue Growth (25 points)**: Quarter-over-quarter revenue growth
   - >20% growth: 25 points
   - 10-20% growth: 20 points
   - 0-10% growth: 15 points

2. **ARR Growth (25 points)**: Quarter-over-quarter ARR growth
   - >20% growth: 25 points
   - 10-20% growth: 20 points
   - 0-10% growth: 15 points

3. **Gross Margin (20 points)**: Profitability indicator
   - ≥70%: 20 points
   - 50-70%: 15 points
   - 30-50%: 10 points

4. **Cash Runway (15 points)**: Months of runway based on cash/burn
   - ≥18 months: 15 points
   - 12-18 months: 12 points
   - 6-12 months: 8 points

5. **Customer Growth (15 points)**: Quarter-over-quarter customer growth
   - >15% growth: 15 points
   - 5-15% growth: 10 points
   - 0-5% growth: 5 points

**Status Levels:**
- 80-100: Excellent
- 60-79: Good
- 40-59: Fair
- 20-39: Needs Attention
- 0-19: Critical

## File Upload Guidelines

### Excel/CSV Files

**Required Columns:**
- `Year`: Integer (e.g., 2024)
- `Quarter`: Integer (1, 2, 3, or 4)

**Optional Columns:**
- `Revenue`: Float
- `ARR`: Float
- `cARR`: Float
- `LARR`: Float
- `Gross Margin`: Float (0-1, where 0.7 = 70%)
- `Burn Rate`: Float
- `Cash Balance`: Float
- `Customer Count`: Integer
- `Notes`: Text

**Tips:**
- Column names are case-insensitive
- Spaces in column names are converted to underscores
- At least one financial metric (Revenue, ARR, cARR, or LARR) is required per row

### PDF Files

PDF parsing is experimental and best-effort. For reliable data import, use Excel or CSV format.

## Configuration

Edit `config.py` to customize:

- `SQLALCHEMY_DATABASE_URI`: Database connection (default: SQLite)
- `UPLOAD_FOLDER`: Directory for uploaded files
- `EXPORT_FOLDER`: Directory for exported Excel files
- `MAX_CONTENT_LENGTH`: Maximum upload file size (default: 16MB)
- `ALLOWED_EXTENSIONS`: Permitted file types

## Development

### Running in Development Mode

The application runs in debug mode by default when using `python run.py`. This enables:
- Auto-reload on code changes
- Detailed error pages
- Debug toolbar

### Database Migrations

The database is automatically created on first run. To reset the database:

```bash
rm -rf database/
python run.py  # Database will be recreated
```

### Testing with Sample Data

1. Start the application
2. Add a test company (e.g., "TechStartup Inc")
3. Upload `sample_data.csv` for that company
4. View the automatically populated metrics

## Production Deployment

For production deployment:

1. **Use a production database** (PostgreSQL recommended)
   ```python
   # config.py
   SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/dbname'
   ```

2. **Disable debug mode**
   ```python
   # run.py
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

3. **Use a production WSGI server** (e.g., Gunicorn)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

4. **Set up reverse proxy** (e.g., Nginx)

5. **Enable HTTPS** with SSL certificates

6. **Configure file storage** (consider S3 or similar for uploads/exports)

## Security Considerations

- Input validation is performed on all uploaded files
- SQL injection protection via SQLAlchemy ORM
- File upload restrictions (type and size)
- Secure filename handling with `werkzeug.secure_filename`

**For production:**
- Add authentication and authorization
- Implement CSRF protection
- Enable HTTPS
- Set secure session cookies
- Regular security updates

## Troubleshooting

### Database errors
```bash
# Delete and recreate database
rm -rf database/
python run.py
```

### Import errors
```bash
# Ensure virtual environment is activated and dependencies installed
source venv/bin/activate
pip install -r requirements.txt
```

### Port already in use
```bash
# Change port in run.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'feat: add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

This project is proprietary software for internal use.

## Support

For issues, questions, or feature requests, please contact the development team or create an issue in the repository.

---

**Version**: 1.0.0
**Last Updated**: 2025-11-24
