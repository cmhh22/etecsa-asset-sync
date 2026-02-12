# Free Deployment on PythonAnywhere (No Credit Card)

PythonAnywhere is the **only 100% free option without a credit card** that fully supports Django.

> **⚠️ IMPORTANT**: MySQL is NOT available on free accounts. This guide uses **SQLite** which works perfectly and is included for free.

## Which Database to Use?

### ✅ SQLite (RECOMMENDED for Free Tier)
- **100% Free**, no limits
- Already configured in your project
- Perfect for demos, portfolios, and small/medium projects
- No additional configuration needed
- **FOLLOW THIS GUIDE** 👇

### ❌ MySQL (Paid Plans Only)
- Requires upgrade ($5/month minimum)
- Only needed for projects with >100GB of data
- Not required for this project

---

## Step 1: Create an Account (5 minutes)

1. Go to https://www.pythonanywhere.com/registration/register/beginner/
2. Complete the form (just email, username, password)
3. Verify your email
4. Log in at https://www.pythonanywhere.com

## Step 2: Clone the Project

1. On the PythonAnywhere Dashboard, go to the **"Consoles"** tab
2. Click on **"Bash"** to open a terminal
3. Run these commands:

```bash
# Clone the repository
git clone https://github.com/cmhh22/etecsa-asset-sync.git

# Navigate to the project directory
cd etecsa-asset-sync/OCS
```

## Step 3: Create a Virtual Environment

```bash
# Create virtualenv with Python 3.12
mkvirtualenv --python=/usr/bin/python3.12 etecsa-env

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables (SQLite)

```bash
cd ~/etecsa-asset-sync/OCS

# Create .env file
nano .env
```

Paste the following (replace `your_username` with your PythonAnywhere username):

```bash
# Django Settings
SECRET_KEY=django-insecure-generate-a-secure-one-here-$(openssl rand -base64 32)
DEBUG=False
ALLOWED_HOSTS=your_username.pythonanywhere.com

# Database Configuration - SQLite (FREE TIER)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# Script Configuration
EXCEL_ECONOMIA=demo_data/AR01_demo.xlsx
EXCEL_CLASIFICADOR=demo_data/clasificador_demo.xlsx
TABLA_ACCOUNTINFO=accountinfo
COLUMNA_INVENTARIO=fields_3
ARCHIVO_REGISTRO=Registros.txt

# Production Security
CSRF_TRUSTED_ORIGINS=http://your_username.pythonanywhere.com
SECURE_SSL_REDIRECT=False
```

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

> **📝 Note**: SQLite creates the `db.sqlite3` file automatically. No additional configuration needed.

## Step 5: Migrate and Prepare

```bash
cd ~/etecsa-asset-sync/OCS

# Activate virtualenv (if not already active)
workon etecsa-env

# Migrate database (creates db.sqlite3 automatically)
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Username: admin
# Email: your@email.com
# Password: admin123 (or your preferred password)

# Seed demo data
python manage.py seed_demo

# Collect static files
python manage.py collectstatic --noinput
```

## Step 6: Configure Web App

1. Dashboard → **"Web"** tab
2. Click **"Add a new web app"**
3. Select **"Manual configuration"** (NOT the Django wizard)
4. Python version: **3.12**

### Configure Code & Virtualenv:

On the Web App configuration page:

**Code section:**
- **Source code**: `/home/your_username/etecsa-asset-sync/OCS`
- **Working directory**: `/home/your_username/etecsa-asset-sync/OCS`

**Virtualenv section:**
- **Path**: `/home/your_username/.virtualenvs/etecsa-env`

### Configure WSGI:

1. Click on the **"WSGI configuration file"** link (something like `/var/www/your_username_pythonanywhere_com_wsgi.py`)
2. **Delete all existing content**
3. Paste the following:

```python
import os
import sys

# Add project to path
path = '/home/your_username/etecsa-asset-sync/OCS'
if path not in sys.path:
    sys.path.append(path)

# Configure Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'OCS.settings'

# Load environment variables from .env
from pathlib import Path
from decouple import config

# Load WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. Replace `your_username` with your actual username
5. **Save** (button at the top right)

### Configure Static Files:

On the same configuration page, scroll to **"Static files"**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/your_username/etecsa-asset-sync/OCS/staticfiles` |

Click **"Save"** after each entry.

## Step 7: Reload and Test

1. Scroll to the top of the Web page
2. Click the green **"Reload your_username.pythonanywhere.com"** button
3. Wait ~10 seconds
4. Click your URL: `http://your_username.pythonanywhere.com`

**Login**: admin / admin123 (or the password you set)

---

## Troubleshooting

### Error "Something went wrong :("

Go to the **"Log files"** section on your Web tab:
- Click **"Error log"** to see specific errors

**Common errors:**

1. **ModuleNotFoundError**:
   - Verify the virtualenv is active: `workon etecsa-env`
   - Reinstall: `pip install -r requirements.txt`

2. **OperationalError: unable to open database file**:
   - Check permissions: `chmod 664 db.sqlite3`
   - Verify `.env` has `DB_ENGINE=django.db.backends.sqlite3`

3. **CSRF verification failed**:
   - In `.env`: `CSRF_TRUSTED_ORIGINS=http://your_username.pythonanywhere.com` (no `https://`)

4. **Static files not loading**:
   - Run: `python manage.py collectstatic --noinput`
   - Verify the "Static files" configuration in the Web tab

### Re-deploying Changes

Every time you update the code on GitHub:

```bash
# In a Bash console
cd ~/etecsa-asset-sync
git pull origin main
cd OCS
workon etecsa-env
python manage.py migrate
python manage.py collectstatic --noinput
```

Then in the Web tab: **"Reload"**

---

## Free Tier Limitations

| Limitation | Impact |
|------------|--------|
| **No HTTPS** | No SSL on `your_username.pythonanywhere.com` (HTTP only) |
| **512MB storage** | Sufficient for this project (~50MB used) |
| **SQLite Database** | Perfect for demos. No size limit (within 512MB storage) |
| **No MySQL** | Not available on free tier (but SQLite works perfectly) |
| **2 consoles** | Sufficient for development |
| **CPU 100s/day** | Daily limit reached only with heavy traffic |
| **Whitelisted internet** | Can only access approved sites from code |

✅ **Perfect for portfolio/demo purposes.** For production with thousands of concurrent users, a paid plan would be needed.

---

## Updating the Project After Changes

1. Bash console:
   ```bash
   cd ~/etecsa-asset-sync
   git pull origin main
   cd OCS
   workon etecsa-env
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

2. Web tab → **"Reload"**

---

## Database Backup (SQLite)

```bash
# In a Bash console
cd ~/etecsa-asset-sync/OCS
cp db.sqlite3 backup_db_$(date +%Y%m%d).sqlite3

# Or download it from the Files tab on the Dashboard
```

---

## Useful Links

- **Your app**: http://your_username.pythonanywhere.com
- **Dashboard**: https://www.pythonanywhere.com/user/your_username/
- **Help**: https://help.pythonanywhere.com/
- **Forums**: https://www.pythonanywhere.com/forums/

---

## Example Final URL

If your username is `cmhh22`:
- **App**: http://cmhh22.pythonanywhere.com
- **Login**: admin / admin123
- **Analytics**: http://cmhh22.pythonanywhere.com/analytics/
