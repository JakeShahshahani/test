#!/bin/bash
# Deployment Script for GreatPoint Ventures Portfolio Management

set -e  # Exit on error

echo "=================================================="
echo "GreatPoint Ventures Portfolio - Production Deploy"
echo "=================================================="

# Configuration
APP_DIR="/var/www/greatpoint-portfolio"
VENV_DIR="$APP_DIR/venv"
DOMAIN="${DOMAIN:-portfolio.greatpointventures.com}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root or with sudo"
fi

echo ""
echo "Step 1: Installing system dependencies..."
apt-get update
apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    supervisor
print_success "System dependencies installed"

echo ""
echo "Step 2: Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR
print_success "Application directory created: $APP_DIR"

echo ""
echo "Step 3: Setting up Python virtual environment..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip
print_success "Virtual environment created"

echo ""
echo "Step 4: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping..."
fi

echo ""
echo "Step 5: Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE greatpoint_portfolio;" 2>/dev/null || print_warning "Database may already exist"
sudo -u postgres psql -c "CREATE USER greatpoint WITH PASSWORD 'change-this-password';" 2>/dev/null || print_warning "User may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE greatpoint_portfolio TO greatpoint;" 2>/dev/null
print_success "PostgreSQL database configured"

echo ""
echo "Step 6: Setting up environment variables..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warning "Created .env from .env.example - PLEASE UPDATE IT WITH YOUR VALUES!"
    else
        print_error ".env.example not found!"
    fi
else
    print_success ".env file already exists"
fi

echo ""
echo "Step 7: Running database migrations..."
export FLASK_ENV=production
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
print_success "Database tables created"

echo ""
echo "Step 8: Setting up Nginx..."
if [ -f "nginx.conf" ]; then
    cp nginx.conf /etc/nginx/sites-available/greatpoint-portfolio
    ln -sf /etc/nginx/sites-available/greatpoint-portfolio /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    print_success "Nginx configured"
else
    print_warning "nginx.conf not found, skipping..."
fi

echo ""
echo "Step 9: Setting up SSL certificate..."
print_warning "Running certbot for SSL certificate..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@greatpointventures.com || print_warning "Certbot failed, you may need to run it manually"

echo ""
echo "Step 10: Setting up systemd service..."
if [ -f "greatpoint-portfolio.service" ]; then
    cp greatpoint-portfolio.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable greatpoint-portfolio
    systemctl start greatpoint-portfolio
    print_success "Systemd service configured and started"
else
    print_warning "Service file not found, skipping..."
fi

echo ""
echo "Step 11: Setting file permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
print_success "File permissions set"

echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
echo "Your application should now be running at:"
echo "https://$DOMAIN"
echo ""
echo "Next steps:"
echo "1. Update .env file with your production values"
echo "2. Restart the service: systemctl restart greatpoint-portfolio"
echo "3. Check logs: journalctl -u greatpoint-portfolio -f"
echo ""
echo "To update the application:"
echo "cd $APP_DIR && git pull && systemctl restart greatpoint-portfolio"
echo ""
