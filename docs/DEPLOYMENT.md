# Deployment Guide

This guide covers deploying **ETECSA Asset Sync** to production environments.

---

## Prerequisites

- Python 3.12+
- MySQL 8.0+ (or PostgreSQL 14+)
- Docker (optional, recommended)
- Git

---

## Option 1: Docker Deployment (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/cmhh22/etecsa-asset-sync.git
cd etecsa-asset-sync
```

### 2. Configure Environment

Edit `docker-compose.yml` and change:

```yaml
environment:
  SECRET_KEY: "your-production-secret-key-here"  # Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  MYSQL_ROOT_PASSWORD: "your-secure-password-here"
```

### 3. Build and Run

```bash
# Start MySQL + Django with Gunicorn
docker-compose up -d --build

# Wait for MySQL to be healthy (check with docker-compose logs mysql)

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# (Optional) Seed demo data
docker-compose exec web python manage.py seed_demo

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 4. Access the Application

- Web UI: `http://localhost:8000`
- Admin panel: `http://localhost:8000/admin`

### 5. Production Checklist

- [ ] Set strong `SECRET_KEY` (50+ random characters)
- [ ] Change `MYSQL_ROOT_PASSWORD`
- [ ] Set `DEBUG=False` in environment
- [ ] Configure `ALLOWED_HOSTS` (comma-separated domains)
- [ ] Enable `SECURE_SSL_REDIRECT=True` if behind HTTPS
- [ ] Set `CSRF_TRUSTED_ORIGINS` (e.g., `https://yourdomain.com`)
- [ ] Configure backup strategy for MySQL data volume
- [ ] Set up log rotation for `OCS/logs/app.log`

### 6. Updating

```bash
git pull origin main
docker-compose down
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

---

## Option 2: Railway Deployment

Railway offers free tier with MySQL included.

### 1. Push to GitHub

```bash
git push origin main
```

### 2. Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select `etecsa-asset-sync`

### 3. Add MySQL Service

1. Click **"New"** → **"Database"** → **"Add MySQL"**
2. Railway auto-generates `DATABASE_URL` environment variable

### 4. Configure Django Service

Click on your Django service → **Variables** tab:

```bash
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=*.up.railway.app
CSRF_TRUSTED_ORIGINS=https://*.up.railway.app
SECURE_SSL_REDIRECT=True

# Railway automatically provides:
# DATABASE_URL=mysql://user:pass@host:port/dbname
```

### 5. Set Build/Start Commands

**Settings** tab:
- **Build Command**: `pip install -r OCS/requirements.txt && cd OCS && python manage.py collectstatic --noinput`
- **Start Command**: `cd OCS && gunicorn OCS.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`
- **Root Directory**: Leave blank (repo root)

### 6. Run Migrations

Once deployed, open the **Railway CLI** or use the web terminal:

```bash
cd OCS
python manage.py migrate
python manage.py createsuperuser
```

### 7. Access Your App

Railway provides a public URL: `https://your-app.up.railway.app`

---

## Option 3: Render Deployment

Render offers free tier with PostgreSQL (MySQL not available on free tier).

### 1. Update Database Backend

Edit `OCS/OCS/settings.py`:

```python
# Change DB_ENGINE default
DB_ENGINE = config('DB_ENGINE', default='django.db.backends.postgresql')
```

Add `psycopg2-binary==2.9.9` to `OCS/requirements.txt`.

### 2. Create Render Services

1. Go to https://render.com
2. Click **"New"** → **"Web Service"**
3. Connect your GitHub repo `etecsa-asset-sync`

**Settings**:
- **Build Command**: `pip install -r OCS/requirements.txt && cd OCS && python manage.py collectstatic --noinput`
- **Start Command**: `cd OCS && gunicorn OCS.wsgi:application --bind 0.0.0.0:$PORT`
- **Environment**: Python 3.12

### 3. Add PostgreSQL Database

1. Render dashboard → **"New"** → **"PostgreSQL"**
2. Copy the **Internal Database URL**

### 4. Environment Variables

In your web service → **Environment** tab:

```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=postgres://user:pass@host:port/dbname  # From PostgreSQL service
CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
SECURE_SSL_REDIRECT=True
```

### 5. Run Migrations

Render **Shell** tab:

```bash
cd OCS
python manage.py migrate
python manage.py createsuperuser
```

---

## Option 4: Fly.io Deployment

Fly.io supports Docker deployments with free tier.

### 1. Install Fly CLI

```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Mac/Linux
curl -L https://fly.io/install.sh | sh
```

### 2. Login and Launch

```bash
fly auth login
fly launch

# Follow prompts:
# - Choose app name
# - Select region
# - Don't deploy yet (we need to configure)
```

### 3. Add MySQL (via external provider)

Fly.io doesn't provide managed MySQL. Options:
- Use **PlanetScale** (free MySQL)
- Use Fly.io Postgres instead

**For PlanetScale**:
1. Create free database at https://planetscale.com
2. Get connection string

### 4. Set Secrets

```bash
fly secrets set SECRET_KEY="your-secret-key"
fly secrets set DEBUG=False
fly secrets set ALLOWED_HOSTS=your-app.fly.dev
fly secrets set DATABASE_URL="mysql://user:pass@host:port/dbname"
fly secrets set CSRF_TRUSTED_ORIGINS=https://your-app.fly.dev
fly secrets set SECURE_SSL_REDIRECT=True
```

### 5. Deploy

```bash
fly deploy

# Run migrations
fly ssh console
cd OCS
python manage.py migrate
python manage.py createsuperuser
exit
```

---

## Option 5: Manual VPS Deployment (Ubuntu)

### 1. Server Setup

```bash
# SSH into your VPS
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.12 python3.12-venv python3-pip mysql-server nginx -y
```

### 2. Clone Repository

```bash
cd /var/www
sudo git clone https://github.com/cmhh22/etecsa-asset-sync.git
cd etecsa-asset-sync
```

### 3. Create Virtual Environment

```bash
python3.12 -m venv env
source env/bin/activate
pip install -r OCS/requirements.txt
pip install gunicorn
```

### 4. Configure MySQL

```bash
sudo mysql
```

```sql
CREATE DATABASE ocs_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ocs_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON ocs_db.* TO 'ocs_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Configure Application

```bash
cd OCS
cp .env.example .env
nano .env
```

Edit `.env`:
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip
DB_ENGINE=django.db.backends.mysql
DB_NAME=ocs_db
DB_USER=ocs_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
SECURE_SSL_REDIRECT=True
```

### 6. Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 7. Configure Gunicorn systemd Service

```bash
sudo nano /etc/systemd/system/etecsa-asset-sync.service
```

```ini
[Unit]
Description=ETECSA Asset Sync Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/etecsa-asset-sync/OCS
Environment="PATH=/var/www/etecsa-asset-sync/env/bin"
ExecStart=/var/www/etecsa-asset-sync/env/bin/gunicorn \
          --workers 3 \
          --bind 127.0.0.1:8000 \
          --timeout 120 \
          OCS.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable etecsa-asset-sync
sudo systemctl start etecsa-asset-sync
sudo systemctl status etecsa-asset-sync
```

### 8. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/etecsa-asset-sync
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/etecsa-asset-sync/OCS/staticfiles/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/etecsa-asset-sync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | Django secret key (50+ chars) |
| `DEBUG` | ❌ | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | ✅ | `localhost` | Comma-separated domains |
| `DB_ENGINE` | ❌ | `django.db.backends.mysql` | Database backend |
| `DB_NAME` | ✅ | `ocs_db` | Database name |
| `DB_USER` | ✅ | `root` | Database user |
| `DB_PASSWORD` | ✅ | — | Database password |
| `DB_HOST` | ❌ | `localhost` | Database host |
| `DB_PORT` | ❌ | `3306` | Database port |
| `DATABASE_URL` | ❌ | — | Overrides all DB_* vars (Railway, Render) |
| `CSRF_TRUSTED_ORIGINS` | ✅ | — | Comma-separated HTTPS origins |
| `SECURE_SSL_REDIRECT` | ❌ | `False` | Redirect HTTP to HTTPS |

---

## Backup Strategy

### MySQL Backup

```bash
# Backup
docker-compose exec mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD ocs_db > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T mysql mysql -u root -p$MYSQL_ROOT_PASSWORD ocs_db < backup_20240211.sql
```

### Application Code

```bash
git pull origin main  # Stay updated with remote
```

---

## Monitoring

### Health Check Endpoint

Add to `OCS/inventario/views.py`:

```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
```

Add to `OCS/inventario/urls.py`:
```python
path('health/', views.health_check, name='health'),
```

### Log Monitoring

```bash
# Docker logs
docker-compose logs -f web

# VPS logs
sudo journalctl -u etecsa-asset-sync -f

# Application logs
tail -f /var/www/etecsa-asset-sync/OCS/logs/app.log
```

---

## Troubleshooting

### Static Files Not Loading

```bash
# Re-collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check STATIC_ROOT in settings.py
```

### Database Connection Errors

```bash
# Test MySQL connectivity
docker-compose exec web python manage.py dbshell

# Check environment variables
docker-compose exec web env | grep DB_
```

### CSRF Verification Failed

- Ensure `CSRF_TRUSTED_ORIGINS` includes your domain with `https://`
- Example: `CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com`

### Migrations Not Applied

```bash
docker-compose exec web python manage.py showmigrations
docker-compose exec web python manage.py migrate --fake-initial  # If tables exist
```

---

## Performance Tuning

### Gunicorn Workers

```bash
# Formula: (2 × CPU cores) + 1
# Example: 4 cores → 9 workers
gunicorn --workers 9 --threads 2 OCS.wsgi:application
```

### Database Indexes

Check `OCS/inventario/models.py` for:
```python
class Meta:
    indexes = [
        models.Index(fields=['noinventario']),
        models.Index(fields=['tag']),
    ]
```

### Static File Compression

WhiteNoise automatically Gzips static files. Verify in browser DevTools:
```
Content-Encoding: gzip
```

---

## Security Hardening

### 1. Keep Dependencies Updated

```bash
pip list --outdated
pip install --upgrade package-name
pip freeze > OCS/requirements.txt
```

### 2. Run Security Audit

```bash
pip install pip-audit
pip-audit -r OCS/requirements.txt
```

### 3. Configure Firewall (VPS)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 4. Fail2Ban (VPS)

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

---

## Support

For issues or questions:
- Open an issue: https://github.com/cmhh22/etecsa-asset-sync/issues
- Check logs: `OCS/logs/app.log`
- Review documentation: `README.md`, `ARCHITECTURE.md`
