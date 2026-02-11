# ETECSA Asset Sync

<p align="center">
  <img src="docs/banner.png" alt="ETECSA Asset Sync" width="600">
</p>

<p align="center">
  <a href="#features"><strong>Features</strong></a> ·
  <a href="#architecture"><strong>Architecture</strong></a> ·
  <a href="#quick-start"><strong>Quick Start</strong></a> ·
  <a href="#demo"><strong>Demo</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/django-5.1-green?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/mysql-8.0-orange?logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/pandas-2.2-purple?logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/docker-ready-blue?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=github-actions&logoColor=white" alt="CI">
  <img src="https://img.shields.io/badge/tests-45+-success?logo=pytest&logoColor=white" alt="Tests">
</p>

---

## Overview

**ETECSA Asset Sync** is a data automation tool built for **ETECSA** (Empresa de Telecomunicaciones de Cuba S.A.) — Cienfuegos province. It automates the process of cross-referencing IT asset inventory data across multiple departmental databases (**IT, HR, Finance**) and municipal offices, replacing a fully manual workflow.

The system was **deployed in production** and successfully processed hundreds of assets across all municipal offices in Cienfuegos province.

### The Problem

Operators at ETECSA had to manually:
- Look up each computer's inventory number in the **OCS Inventory** database
- Cross-reference it with the **Finance department's AR01 report** (Excel)
- Find the corresponding **office/building** in the **HR Locations Classifier** (Excel)
- Update the TAG field in the database with the correct `Building-Office` format
- Identify discrepancies: duplicates, missing records, orphaned entries

This process was **time-consuming, error-prone**, and required navigating 3 different data sources for each asset.

### The Solution

A Python script that:
1. **Reads** all assets from the OCS Inventory MySQL database
2. **Cross-references** each inventory number against the Finance Excel report
3. **Resolves** office/building information from the HR Locations Classifier
4. **Updates** TAG fields in bulk with the format `Building-OfficeName`
5. **Generates** comprehensive Excel reports identifying anomalies

Plus a **Django web interface** for operators to trigger syncs and view reports.

---

## Features

- **Multi-source data reconciliation** — Joins MySQL + 2 Excel sources automatically
- **Bulk TAG updates** — Updates hundreds of records in seconds
- **Anomaly detection reports** — Identifies:
  - Empty inventory numbers
  - Virtual machines (MV)
  - Duplicate inventory entries (sorted by HARDWARE_ID)
  - Assets in DB not found in AR01
  - Assets in AR01 not found in DB
  - Office codes not in the classifier
- **Excel report generation** — Multi-sheet `.xlsx` with auto-fitted columns
- **AI-powered analytics** — Anomaly detection, data quality scoring, and predictive insights:
  - Z-score based outlier detection per building
  - Composite data quality score (completeness, consistency, uniqueness, validity)
  - Entropy-based distribution balance analysis
  - Sync effort predictions and coverage projections
- **Web dashboard** — Modern Bootstrap 5.3 UI with Chart.js visualizations
- **Management commands** — `sync_tags` and `analyze_assets` CLI tools
- **45+ automated tests** — pytest suite covering models, views, and analytics
- **CI/CD pipeline** — GitHub Actions with lint, test matrix, security audit, and Docker build
- **Environment-based config** — Credentials and paths via `.env` file
- **Production-ready settings** — HSTS, secure cookies, XSS protection when `DEBUG=False`
- **Structured logging** — Timestamped logs to file and console

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Django Web Interface                        │
│  ┌────────┐ ┌───────────┐ ┌──────────┐ ┌───────────────────┐   │
│  │ Login  │ │ Dashboard │ │ Reports  │ │  AI Analytics     │   │
│  └────────┘ └─────┬─────┘ └────┬─────┘ └────────┬──────────┘   │
│                   │            │                │              │
│    ┌──────────────▼────────────▼────────────────▼──────────┐   │
│    │              Services Layer                           │   │
│    │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐   │   │
│    │  │DataSources │ │ Processor  │ │ AnalyticsEngine  │   │   │
│    │  │  (ETL)     │ │ (Sync)     │ │ (AI / NumPy)     │   │   │
│    │  └─────┬──────┘ └─────┬──────┘ └────────┬─────────┘   │   │
│    └────────┼──────────────┼─────────────────┼─────────────┘   │
│             │              │                 │                 │
│    ┌────────▼───┐  ┌───────▼──┐  ┌───────────▼──────┐          │
│    │   MySQL    │  │  AR01    │  │   Locations      │          │
│    │  OCS Inv.  │  │  Excel   │  │   Classifier     │          │
│    │ (Hardware) │  │ (Finance)│  │   (HR/Excel)     │          │
│    └────────────┘  └──────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- MySQL 8.0+ (or Docker)

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/etecsa-asset-sync.git
cd etecsa-asset-sync

# Start MySQL + Django (Gunicorn production server)
docker-compose up -d --build

# Seed demo data
docker-compose exec web python manage.py seed_demo

# Access the app
open http://localhost:8000
# Login: admin / admin123
```

### Option 2: Manual Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/etecsa-asset-sync.git
cd etecsa-asset-sync/OCS

# Create virtual environment
python -m venv ../env
# Windows:
..\env\Scripts\activate
# Linux/Mac:
source ../env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — for quick demo without MySQL, set:
#   DB_ENGINE=django.db.backends.sqlite3
#   DB_NAME=db.sqlite3

# Run migrations and seed demo data
python manage.py migrate
python manage.py seed_demo

# Start the development server
python manage.py runserver
# Login at http://localhost:8000 with admin / admin123
```

### Management Commands

```bash
cd OCS

# Run the TAG sync (cross-reference MySQL + Excel sources)
python manage.py sync_tags

# Run AI analytics (anomaly detection + data quality)
python manage.py analyze_assets
python manage.py analyze_assets --json --output report.json

# Seed/reset demo data
python manage.py seed_demo
python manage.py seed_demo --reset

# Legacy script (still functional)
python script_actualizar_TAG.py
```

---

## AI Analytics

The built-in analytics engine (`inventario/services/analytics.py`) provides intelligent insights without external AI services:

| Feature | Method | Output |
|---------|--------|--------|
| **Anomaly Detection** | Z-score outlier analysis, pattern matching | Duplicate inventories, missing TAGs, orphan records, building outliers |
| **Data Quality Score** | Weighted composite (completeness 30%, consistency 25%, uniqueness 25%, validity 20%) | 0-100 score with A-F grade |
| **Distribution Analysis** | Entropy-based balance measurement | TAG status, building distribution, user/category breakdowns |
| **Predictions** | Heuristic estimation based on current data | Sync time estimates, coverage projections, prioritized recommendations |

Access analytics via:
- **Web UI** → `/analytics/` (interactive dashboard with Chart.js visualizations)
- **REST API** → `/api/analytics/` (JSON response)
- **CLI** → `python manage.py analyze_assets`

---

## Testing

The project includes **45+ automated tests** organized across three test modules:

```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=inventario --cov-report=term-missing

# Run specific test module
python -m pytest inventario/tests/test_analytics.py -v
```

| Module | Tests | Coverage |
|--------|-------|----------|
| `test_analytics.py` | 20+ | Anomaly detection, data quality, distributions, predictions |
| `test_views.py` | 15+ | Auth flows, protected views, API endpoints, sync |
| `test_models.py` | 10+ | Model relations, cascade deletes, string representations |

---

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on every push and PR:

```
┌─────────┐     ┌──────────────────┐     ┌──────────┐     ┌────────┐
│  Lint   │────▶│  Test (3.11/3.12) │────▶│ Security │────▶│ Docker │
│ flake8  │     │  pytest + MySQL   │     │ pip-audit│     │ build  │
│ isort   │     │  + coverage       │     └──────────┘     └────────┘
│ black   │     └──────────────────┘
└─────────┘
```

- **Lint**: flake8, isort, black (code style enforcement)
- **Test**: Matrix across Python 3.11 & 3.12 with MySQL 8.0 service container
- **Security**: pip-audit for dependency vulnerability scanning
- **Docker**: Validates container builds successfully

---

## Demo

The project includes demo data files in `OCS/demo_data/` so you can test the sync workflow without access to ETECSA's actual databases.

| View | Description |
|------|-------------|
| **Login** | Authentication page for operators |
| **Asset Table** | Browse all assets with TAG, building, inventory number |
| **Reports** | View generated Excel reports by category (duplicates, missing, etc.) |
| **Sync** | One-click button to run the cross-reference sync |

---

## Project Structure

```
etecsa-asset-sync/
├── OCS/                              # Django project root
│   ├── manage.py
│   ├── script_actualizar_TAG.py      # Legacy sync engine
│   ├── conftest.py                   # Shared pytest fixtures
│   ├── pytest.ini                    # Test configuration
│   ├── .env.example                  # Environment template
│   ├── requirements.txt
│   ├── OCS/                          # Django settings
│   │   ├── settings.py               # Production-ready config
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── inventario/                   # Main Django app
│   │   ├── models.py                 # Asset, Building, Office models
│   │   ├── views.py                  # Dashboard, API, analytics views
│   │   ├── admin.py                  # Admin registration (6 models)
│   │   ├── urls.py                   # URL routing
│   │   ├── forms.py                  # Auth forms
│   │   ├── services/                 # Business logic layer
│   │   │   ├── data_sources.py       # Excel ETL (AR01, Classifier)
│   │   │   ├── processors.py         # TAG sync processor
│   │   │   ├── reporters.py          # Excel report generator
│   │   │   └── analytics.py          # AI analytics engine
│   │   ├── management/commands/      # CLI commands
│   │   │   ├── sync_tags.py          # TAG sync command
│   │   │   ├── analyze_assets.py     # AI analytics command
│   │   │   └── seed_demo.py          # Demo data seeder
│   │   └── tests/                    # Test suite (45+ tests)
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_analytics.py
│   ├── templates/                    # Bootstrap 5.3 templates
│   │   ├── base.html                 # Sidebar layout
│   │   ├── dashboard.html            # Chart.js dashboard
│   │   ├── analytics.html            # AI analytics dashboard
│   │   └── ...                       # Login, register, reports
│   ├── demo_data/                    # Sample Excel files
│   └── logs/                         # Application logs
├── .github/workflows/ci.yml          # GitHub Actions CI pipeline
├── docker-compose.yml
├── Dockerfile
├── .dockerignore
├── .gitignore
├── CONTRIBUTING.md
└── README.md
```

---

## Deployment

The project is production-ready with:

- **Gunicorn** WSGI server (replaces Django's dev server)
- **WhiteNoise** for static file serving without Nginx
- **Security hardening** auto-enabled when `DEBUG=False` (HSTS, secure cookies, XSS protection)
- **Docker** multi-container setup with MySQL health checks

### Deploy with Docker (Production)

```bash
# 1. Edit docker-compose.yml — change SECRET_KEY and MYSQL_ROOT_PASSWORD
# 2. Build and run
docker-compose up -d --build

# 3. Run migrations + seed data
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_demo
docker-compose exec web python manage.py collectstatic --noinput
```

### Deploy to Railway / Render / Fly.io

1. Push to GitHub
2. Connect the repo to your hosting platform
3. Set environment variables from `.env.example`
4. Set build command: `pip install -r OCS/requirements.txt`
5. Set start command: `cd OCS && gunicorn OCS.wsgi:application --bind 0.0.0.0:$PORT`
6. Add `CSRF_TRUSTED_ORIGINS=https://your-domain.com` to env vars

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12 |
| **Web Framework** | Django 5.1 |
| **Database** | MySQL 8.0 |
| **Data Processing** | Pandas 2.2, NumPy 2.1, OpenPyXL |
| **AI / Analytics** | NumPy (z-score), entropy analysis, composite scoring |
| **Frontend** | Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4 |
| **Testing** | pytest, pytest-django, pytest-cov (45+ tests) |
| **CI/CD** | GitHub Actions (lint → test → security → docker) |
| **Code Quality** | flake8, black, isort |
| **Production** | Gunicorn, WhiteNoise |
| **Containerization** | Docker, Docker Compose |
| **Configuration** | python-decouple |

---

## Context

This project was developed and deployed at **ETECSA Cienfuegos** (Cuba's national telecom company) to automate IT asset inventory management across the province. It replaced a manual process that required operators to cross-reference data across three different departmental systems for each asset.

The production deployment successfully processed all computer assets across municipal offices in the Cienfuegos province, significantly reducing the time and errors associated with manual TAG assignment.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

Developed with real-world deployment experience at ETECSA Cienfuegos.
