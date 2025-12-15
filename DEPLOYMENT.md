# GreatPoint Ventures Portfolio Management - Production Deployment Guide

Complete guide for deploying your portfolio management application to production with a custom domain.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Platform Options](#platform-options)
3. [Domain Configuration](#domain-configuration)
4. [VPS Deployment (DigitalOcean/AWS)](#vps-deployment)
5. [Heroku Deployment](#heroku-deployment)
6. [Google Cloud Run Deployment](#google-cloud-run)
7. [Environment Variables](#environment-variables)
8. [Database Setup](#database-setup)
9. [SSL/HTTPS Setup](#ssl-https-setup)
10. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Quick Start

### Prerequisites
- A domain name (e.g., `portfolio.greatpointventures.com`)
- SSH access to a server OR cloud platform account
- Basic command line knowledge

### Deployment Checklist
- [ ] Domain purchased and DNS configured
- [ ] Server provisioned (DigitalOcean, AWS, etc.)
- [ ] SSL certificate installed
- [ ] Environment variables configured
- [ ] Database created and migrated
- [ ] Application deployed and running
- [ ] Custom domain pointing to application

---

## Platform Options

### Recommended Platforms

| Platform | Best For | Cost | Difficulty |
|----------|----------|------|------------|
| **DigitalOcean** | Small-medium teams | $12-24/mo | Medium |
| **AWS EC2** | Enterprise scale | $15-50/mo | Hard |
| **Heroku** | Quick deployment | $7-25/mo | Easy |
| **Google Cloud Run** | Serverless | Pay-per-use | Medium |
| **Railway** | Modern startups | $5-20/mo | Easy |

---

## Domain Configuration

### 1. Purchase Domain
Purchase your domain from:
- **Namecheap** (recommended)
- **Google Domains**
- **GoDaddy**
- **Cloudflare**

### 2. Configure DNS

For **DigitalOcean/AWS/VPS**:
```
Type: A Record
Name: portfolio (or @)
Value: YOUR_SERVER_IP
TTL: 3600
```

For **Heroku**:
```
Type: CNAME
Name: portfolio
Value: your-app-name.herokuapp.com
TTL: 3600
```

For **Cloudflare** (optional CDN):
1. Change nameservers to Cloudflare
2. Add A record pointing to your server IP
3. Enable "Proxy" (orange cloud)
4. Configure SSL to "Full (strict)"

---

## VPS Deployment (DigitalOcean/AWS)

### Step 1: Provision Server

**DigitalOcean Droplet:**
```bash
# Create a droplet
- Choose Ubuntu 22.04 LTS
- Select $12/month plan (2GB RAM minimum)
- Add SSH key
- Choose datacenter close to your users
```

**AWS EC2:**
```bash
# Launch EC2 instance
- AMI: Ubuntu 22.04 LTS
- Instance type: t3.small or larger
- Configure security group (ports 22, 80, 443)
- Add key pair
```

### Step 2: Initial Server Setup

SSH into your server:
```bash
ssh root@YOUR_SERVER_IP
```

Update system:
```bash
apt update && apt upgrade -y
```

Create a non-root user:
```bash
adduser greatpoint
usermod -aG sudo greatpoint
su - greatpoint
```

### Step 3: Deploy Application

Clone your repository:
```bash
cd /var/www
sudo git clone https://github.com/YOUR_USERNAME/test.git greatpoint-portfolio
cd greatpoint-portfolio
```

Run the deployment script:
```bash
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

### Step 4: Configure Environment

Edit `.env` file:
```bash
sudo nano .env
```

Update these values:
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-generate-random-string
DATABASE_URL=postgresql://greatpoint:YOUR_PASSWORD@localhost:5432/greatpoint_portfolio
DOMAIN=portfolio.greatpointventures.com
APP_URL=https://portfolio.greatpointventures.com
```

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Start Services

```bash
sudo systemctl restart greatpoint-portfolio
sudo systemctl restart nginx
sudo systemctl status greatpoint-portfolio
```

### Step 6: Verify Deployment

Check if app is running:
```bash
curl http://localhost:8000
```

Check logs:
```bash
sudo journalctl -u greatpoint-portfolio -f
```

Visit your domain:
```
https://portfolio.greatpointventures.com
```

---

## Heroku Deployment

### Step 1: Install Heroku CLI

```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

### Step 2: Create Heroku App

```bash
cd ~/Desktop/test
heroku create greatpoint-portfolio
```

### Step 3: Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:mini
```

### Step 4: Create `Procfile`

```bash
echo "web: gunicorn --config gunicorn_config.py app:app" > Procfile
```

### Step 5: Create `runtime.txt`

```bash
echo "python-3.11.7" > runtime.txt
```

### Step 6: Update `app.py` for Heroku

Add at the top of `app.py`:
```python
import os
from config import get_config

# Load configuration
config = get_config()
app.config.from_object(config)
```

### Step 7: Set Environment Variables

```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

### Step 8: Deploy

```bash
git add Procfile runtime.txt
git commit -m "Add Heroku deployment files"
git push heroku main
```

### Step 9: Run Database Migrations

```bash
heroku run python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Step 10: Configure Custom Domain

```bash
heroku domains:add portfolio.greatpointventures.com
```

Follow instructions to add DNS record, then:
```bash
heroku certs:auto:enable
```

Visit: `https://portfolio.greatpointventures.com`

---

## Google Cloud Run

### Step 1: Install Google Cloud SDK

```bash
curl https://sdk.cloud.google.com | bash
gcloud init
```

### Step 2: Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV FLASK_ENV=production

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

### Step 3: Create `.dockerignore`

```
venv/
*.pyc
__pycache__/
.env
.git/
*.db
```

### Step 4: Build and Deploy

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/greatpoint-portfolio
gcloud run deploy greatpoint-portfolio \
  --image gcr.io/YOUR_PROJECT_ID/greatpoint-portfolio \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Step 5: Add Custom Domain

```bash
gcloud run domain-mappings create \
  --service greatpoint-portfolio \
  --domain portfolio.greatpointventures.com
```

---

## Environment Variables

### Required Variables

```env
# Flask
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Domain
DOMAIN=portfolio.greatpointventures.com
APP_URL=https://portfolio.greatpointventures.com
```

### Optional Variables

```env
# Session
SESSION_COOKIE_SECURE=True

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@greatpointventures.com
SMTP_PASSWORD=your-app-password

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

---

## Database Setup

### PostgreSQL Installation (Ubuntu)

```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE greatpoint_portfolio;
CREATE USER greatpoint WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE greatpoint_portfolio TO greatpoint;
\q
```

### Update Connection String

```env
DATABASE_URL=postgresql://greatpoint:your-secure-password@localhost:5432/greatpoint_portfolio
```

### Run Migrations

```bash
cd /var/www/greatpoint-portfolio
source venv/bin/activate
export FLASK_ENV=production
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt (Free)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d portfolio.greatpointventures.com
```

Auto-renewal:
```bash
sudo certbot renew --dry-run
```

### Using Cloudflare (Easy)

1. Add your domain to Cloudflare
2. Change nameservers at your registrar
3. Enable "Full (strict)" SSL mode
4. Cloudflare handles certificate automatically

---

## Monitoring & Maintenance

### Check Application Status

```bash
sudo systemctl status greatpoint-portfolio
```

### View Logs

```bash
# Application logs
sudo journalctl -u greatpoint-portfolio -f

# Nginx access logs
sudo tail -f /var/log/nginx/greatpoint-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/greatpoint-error.log
```

### Restart Application

```bash
sudo systemctl restart greatpoint-portfolio
```

### Update Application

```bash
cd /var/www/greatpoint-portfolio
sudo git pull origin main
sudo systemctl restart greatpoint-portfolio
```

### Database Backup

```bash
sudo -u postgres pg_dump greatpoint_portfolio > backup_$(date +%Y%m%d).sql
```

### Set Up Automated Backups

Create backup script `/usr/local/bin/backup-greatpoint.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/greatpoint"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
sudo -u postgres pg_dump greatpoint_portfolio | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-greatpoint.sh
```

---

## Troubleshooting

### Application Not Starting

```bash
sudo journalctl -u greatpoint-portfolio -n 100 --no-pager
```

### Database Connection Error

```bash
sudo -u postgres psql -l  # List databases
netstat -an | grep 5432   # Check if PostgreSQL is running
```

### Nginx 502 Error

```bash
sudo nginx -t              # Test configuration
sudo systemctl status greatpoint-portfolio
sudo tail -f /var/log/nginx/greatpoint-error.log
```

### SSL Certificate Issues

```bash
sudo certbot certificates  # Check certificate status
sudo certbot renew        # Manually renew
```

---

## Security Checklist

- [ ] Changed default database password
- [ ] Generated secure SECRET_KEY
- [ ] Enabled firewall (ufw)
- [ ] Configured fail2ban
- [ ] Set up automatic security updates
- [ ] Restricted SSH access (key-only)
- [ ] Configured HTTPS/SSL
- [ ] Set up regular backups
- [ ] Enabled logging and monitoring
- [ ] Reviewed file permissions

---

## Cost Estimation

### Monthly Hosting Costs

**Small Deployment (5-10 users):**
- DigitalOcean: $12/mo
- Domain: $12/yr ($1/mo)
- SSL: Free (Let's Encrypt)
- **Total: ~$13/mo**

**Medium Deployment (20-50 users):**
- DigitalOcean: $24/mo
- Domain: $12/yr
- Database backups: $5/mo
- **Total: ~$30/mo**

**Enterprise Deployment:**
- AWS EC2: $50-100/mo
- RDS PostgreSQL: $30-50/mo
- Load Balancer: $20/mo
- Backups/Monitoring: $20/mo
- **Total: ~$120-190/mo**

---

## Support

For deployment issues:
1. Check application logs
2. Review Nginx error logs
3. Verify environment variables
4. Test database connection
5. Check DNS configuration

---

**Deployment Complete! Your GreatPoint Ventures Portfolio Management system is now live!** 🚀
