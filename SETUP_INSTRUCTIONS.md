# VC Portfolio Management System - Setup Instructions

## COMPLETE SETUP GUIDE

### Step 1: Install Python (if not already installed)

1. Go to: https://www.python.org/downloads/
2. Download Python 3.8 or higher
3. Run the installer
4. **IMPORTANT (Mac):** Make sure Python is added to your PATH

### Step 2: Open Terminal/Cursor

**Mac:** Open Cursor or Terminal app

### Step 3: Navigate to Project Directory

```bash
cd ~/Desktop/test
```

(Or wherever you cloned the repository)

### Step 4: Create Virtual Environment

```bash
python3 -m venv venv
```

### Step 5: Activate Virtual Environment

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your command line.

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

Wait for installation to complete (30 seconds - 1 minute).

### Step 7: Run the Application

```bash
python3 app.py
```

### Step 8: Open in Browser

Open your web browser and go to:

```
http://localhost:5001
```

## What You'll See

The app will automatically create:
- A SQLite database (`portfolio.db`)
- 3 sample companies with metrics
- Sample quarterly revenue data

## Main Features

### 1. Portfolio Metrics Dashboard
**URL:** http://localhost:5001/dashboard/portfolio-metrics

Shows all companies with their:
- ARR
- Headcount
- Gross Profit and %
- S&M, R&D, G&A expenses
- EOP Cash and Runway

Click "Edit" to update any company's metrics.

### 2. Revenue Tracking Dashboard
**URL:** http://localhost:5001/dashboard/revenue-tracking

Shows:
- Latest quarterly revenue for each company
- Historical revenue data
- Revenue trends with charts
- Quarter-over-quarter growth

Click "View History" to see detailed trends.

### 3. Submit Revenue Form
**URL:** http://localhost:5001/form/submit-revenue

Portfolio companies use this form to submit quarterly revenue:
1. Select company
2. Enter year and quarter
3. Enter revenue amount
4. Submit

Data immediately appears on Revenue Tracking Dashboard.

### 4. Add Company
**URL:** http://localhost:5001/admin/add-company

Admin function to add new portfolio companies to the system.

## Testing the Application

### Test Scenario 1: View Sample Data

1. Go to Portfolio Metrics Dashboard
2. You should see 3 sample companies
3. Click "Edit" on any company
4. Try updating the metrics
5. Go back to dashboard - see updated values

### Test Scenario 2: Submit New Revenue

1. Go to Submit Revenue form
2. Select "TechCorp Inc"
3. Year: 2024, Quarter: 4
4. Revenue: 1000000
5. Submit
6. Go to Revenue Tracking Dashboard
7. Click "View History" for TechCorp Inc
8. See the new Q4 2024 revenue and chart

### Test Scenario 3: Add New Company

1. Go to Add Company
2. Enter: "My Startup Inc"
3. Submit
4. Go to Portfolio Metrics Dashboard
5. See the new company (with zero metrics)
6. Click "Edit" and add some metrics
7. Go to Submit Revenue
8. Submit revenue for your new company
9. Check Revenue Tracking Dashboard

## Troubleshooting

### Port 5001 already in use?

Edit `app.py`, change the last line from:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

To:
```python
app.run(debug=True, host='0.0.0.0', port=5002)
```

Then use `http://localhost:5002`

### Can't import Flask?

Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

Then reinstall:
```bash
pip install -r requirements.txt
```

### Database errors?

Delete the database and restart:
```bash
rm portfolio.db
python3 app.py
```

The app will recreate the database with sample data.

## Stopping the Application

Press **Control + C** in the terminal where the app is running.

## Next Time You Want to Run It

```bash
cd ~/Desktop/test
source venv/bin/activate
python3 app.py
```

Then open browser to `http://localhost:5001`

## File Structure

```
test/
├── app.py                    # Main application file (ALL CODE HERE)
├── templates/                # HTML templates
│   ├── base.html            # Base template with navigation
│   ├── portfolio_metrics.html
│   ├── revenue_tracking.html
│   ├── submit_revenue.html
│   ├── add_company.html
│   └── update_metrics.html
├── requirements.txt          # Python dependencies
├── portfolio.db             # SQLite database (auto-created)
└── SETUP_INSTRUCTIONS.md    # This file
```

## How It Works

1. **Database:** SQLite (file-based, no server needed)
2. **Backend:** Flask Python web framework
3. **Frontend:** HTML + CSS (inline) + JavaScript
4. **Data Flow:**
   - Forms submit data to Flask routes
   - Flask saves to SQLite database
   - Dashboards query database and render data
   - Charts use Chart.js library

## Customization

All code is in `app.py`. You can:
- Add new metrics to the `CompanyMetrics` model
- Create new dashboard views
- Modify the sample data in `init_db()` function
- Change styling in `templates/base.html`

## Support

If something doesn't work:
1. Make sure you're in the virtual environment `(venv)`
2. Check the terminal for error messages
3. Try deleting `portfolio.db` and restarting
4. Make sure port 5001 isn't being used by another app

---

**That's it! You now have a fully working VC portfolio management system.**
