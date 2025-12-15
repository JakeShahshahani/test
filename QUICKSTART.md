# GreatPoint Ventures - Quick Deployment Guide

Deploy your portfolio management system in 15 minutes with a custom domain.

---

## 🚀 Fastest Path to Production

### Option 1: DigitalOcean (Recommended - $12/month)

**1. Create DigitalOcean Account**
- Sign up at digitalocean.com
- Add payment method
- Get $200 free credit (new accounts)

**2. Create Droplet**
```
- Click "Create" → "Droplets"
- Choose: Ubuntu 22.04 LTS
- Plan: Basic ($12/mo - 2GB RAM)
- Datacenter: Choose closest to you
- Authentication: SSH Key (recommended) or Password
- Hostname: greatpoint-portfolio
- Click "Create Droplet"
```

**3. Configure Your Domain**

At your domain registrar (Namecheap, GoDaddy, etc.):
```
Type: A Record
Name: portfolio (or @)
Value: YOUR_DROPLET_IP (from DigitalOcean dashboard)
TTL: 3600
```

**4. SSH Into Your Server**
```bash
ssh root@YOUR_DROPLET_IP
```

**5. Clone and Deploy**
```bash
cd /var/www
git clone https://github.com/YOUR_USERNAME/test.git greatpoint-portfolio
cd greatpoint-portfolio
chmod +x deploy.sh
./deploy.sh
```

**6. Configure Environment**
```bash
nano .env
```

Update these values:
```env
SECRET_KEY=GENERATE_RANDOM_STRING_HERE
DATABASE_URL=postgresql://greatpoint:CHANGE_PASSWORD@localhost:5432/greatpoint_portfolio
DOMAIN=portfolio.greatpointventures.com
APP_URL=https://portfolio.greatpointventures.com
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**7. Restart and Go Live**
```bash
systemctl restart greatpoint-portfolio
```

**8. Visit Your Site**
```
https://portfolio.greatpointventures.com
```

✅ **DONE! Your app is live!**

---

### Option 2: Heroku (Easiest - $7/month)

**1. Install Heroku CLI**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

**2. Create App**
```bash
cd ~/Desktop/test
heroku create greatpoint-portfolio
heroku addons:create heroku-postgresql:mini
```

**3. Configure Environment**
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

**4. Deploy**
```bash
git push heroku main
```

**5. Run Database Setup**
```bash
heroku run python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

**6. Add Custom Domain**
```bash
heroku domains:add portfolio.greatpointventures.com
```

Follow the DNS instructions provided, then:
```bash
heroku certs:auto:enable
```

**7. Visit Your Site**
```
https://portfolio.greatpointventures.com
```

✅ **DONE! Your app is live!**

---

### Option 3: Railway (Modern - $5/month)

**1. Sign Up at railway.app**

**2. New Project**
- Click "New Project"
- Select "Deploy from GitHub repo"
- Connect your repository
- Railway auto-detects Flask app

**3. Add PostgreSQL**
- Click "New" → "Database" → "PostgreSQL"
- Railway connects it automatically

**4. Set Environment Variables**
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

**5. Add Custom Domain**
- Go to "Settings" → "Domains"
- Add "portfolio.greatpointventures.com"
- Update your DNS with the CNAME provided

**6. Deploy**
- Push to your GitHub repo
- Railway auto-deploys

✅ **DONE! Your app is live!**

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure you have:

- [ ] **Domain name** purchased
- [ ] **GitHub repository** with your code
- [ ] **PostgreSQL-ready code** (included in deployment files)
- [ ] **SSL certificate** plan (Let's Encrypt is free)
- [ ] **Backup strategy** (automated backups recommended)

---

## 🔧 Post-Deployment Tasks

After deployment:

1. **Test all pages**
   - Portfolio Overview
   - Revenue & ARR
   - Company Metrics
   - Form Management
   - Company Database

2. **Set up monitoring**
   ```bash
   # View logs
   heroku logs --tail  # Heroku
   journalctl -u greatpoint-portfolio -f  # DigitalOcean
   ```

3. **Configure backups**
   ```bash
   # DigitalOcean
   sudo -u postgres pg_dump greatpoint_portfolio > backup.sql
   
   # Heroku
   heroku pg:backups:capture
   heroku pg:backups:download
   ```

4. **Update Google Form webhook**
   - Use: `https://portfolio.greatpointventures.com/api/form-submit`

5. **Test Google Form integration**
   - Submit test data
   - Verify it appears in dashboards

---

## 🆘 Quick Troubleshooting

### Application won't start
```bash
# DigitalOcean
sudo journalctl -u greatpoint-portfolio -n 50

# Heroku
heroku logs --tail
```

### Database connection error
```bash
# Check DATABASE_URL is set correctly
heroku config  # Heroku
cat .env  # DigitalOcean
```

### Domain not resolving
- Wait 24-48 hours for DNS propagation
- Verify DNS records are correct
- Use `dig portfolio.greatpointventures.com` to check

### SSL certificate error
```bash
# DigitalOcean
sudo certbot renew

# Heroku
heroku certs:auto:refresh
```

---

## 💰 Cost Breakdown

### DigitalOcean
- Droplet: $12/month
- Domain: ~$12/year
- SSL: Free (Let's Encrypt)
- **Total: ~$13/month**

### Heroku
- Dyno: $7/month
- PostgreSQL: $9/month (mini)
- Domain: ~$12/year
- SSL: Free (automatic)
- **Total: ~$17/month**

### Railway
- Service: ~$5/month
- PostgreSQL: Included
- Domain: ~$12/year
- SSL: Free (automatic)
- **Total: ~$6/month**

---

## 📞 Need Help?

Common resources:
- **DigitalOcean**: docs.digitalocean.com
- **Heroku**: devcenter.heroku.com
- **Let's Encrypt**: letsencrypt.org
- **Flask**: flask.palletsprojects.com

---

**Your GreatPoint Ventures portfolio management system should now be live and accessible at your custom domain!** 🎉
