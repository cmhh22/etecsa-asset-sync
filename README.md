# ETECSA Asset Sync

> 🏢 **Production IT asset management system deployed at ETECSA (Cuba's national telecom)**  
> Automates cross-referencing of database + Excel data sources across IT, Finance, and HR departments

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/django-5.1-green?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/sqlite%20%7C%20mysql-supported-orange?logo=sqlite&logoColor=white" alt="DB">
  <img src="https://img.shields.io/badge/docker-ready-blue?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/tests-45+-success?logo=pytest&logoColor=white" alt="Tests">
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-brightgreen?logo=github-actions" alt="CI">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">
</p>

---

## Overview

**ETECSA Asset Sync** is an IT asset management system deployed in production at ETECSA, Cuba's national telecommunications company. It automates the synchronization between the OCS Inventory database, financial reports (AR01), and the HR location classifier — eliminating the manual cross-referencing process that previously required operators to match assets one by one across three separate systems.

### Production Tool: The Script

The **standalone Python script** ([script_actualizar_TAG.py](OCS/script_actualizar_TAG.py)) is the core production tool that runs at ETECSA Cienfuegos:
- Connects to the OCS Inventory MySQL database
- Cross-references each asset with the Finance AR01 Excel report and the HR Location Classifier
- Generates TAGs in `Building-Office` format and updates the database in bulk
- Produces a multi-sheet Excel report with anomalies (duplicates, missing records, orphans)
- Processes hundreds of assets across all municipal offices in the province

### Web Demo: The Dashboard

The **Django web interface** was built as a portfolio extension to showcase the project with a visual layer:
- Interactive dashboard with real-time statistics and Chart.js visualizations
- AI-powered analytics engine (anomaly detection, data quality scoring, entropy analysis)
- Asset browsing with search and filtering
- Report generation and download
- **Note:** The web layer is a demonstration — the script is what runs in production

---

## Features

| Category | Capabilities |
|----------|-------------|
| **Data Integration** | Merges DB + 2 Excel sources (Finance AR01, HR Classifier) |
| **Bulk Updates** | Updates hundreds of TAG fields (`Building-Office` format) in seconds |
| **Anomaly Detection** | Identifies duplicates, missing records, orphans, outliers (z-score) |
| **AI Analytics** | Data quality scoring (0-100), entropy analysis, predictive insights |
| **Reporting** | Multi-sheet Excel reports with auto-fitted columns |
| **Web Dashboard** | Bootstrap 5.3 UI, Chart.js visualizations, REST API |
| **Testing** | 45+ pytest tests (models, views, analytics) + GitHub Actions CI |
| **Production Ready** | Gunicorn, WhiteNoise, HSTS, Docker, environment-based config |

---

## Quick Start

### Option 1: Local Development (Fastest)

```bash
git clone https://github.com/cmhh22/etecsa-asset-sync.git
cd etecsa-asset-sync/OCS
python -m venv ../env
# Windows:
..\env\Scripts\activate
# macOS/Linux:
source ../env/bin/activate

pip install -r requirements.txt
cp .env.example .env    # Uses SQLite by default — no extra setup
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
# → http://localhost:8000 (admin / admin123)
```

### Option 2: Docker

```bash
git clone https://github.com/cmhh22/etecsa-asset-sync.git
cd etecsa-asset-sync
docker-compose up -d --build
docker-compose exec web python manage.py seed_demo
# → http://localhost:8000 (admin / admin123)
```

### Option 3: Deploy Free on PythonAnywhere (No Credit Card)

📖 **[Full PythonAnywhere deployment guide](docs/PYTHONANYWHERE_DEPLOY.md)** (step-by-step)

---

## Project Structure

```
etecsa-asset-sync/
├── .github/workflows/ci.yml     # CI/CD pipeline (lint → test → security → docker)
├── Dockerfile                   # Production container
├── docker-compose.yml           # Multi-service orchestration
├── render.yaml                  # Render.com deployment blueprint
├── build.sh                     # Build script for PaaS platforms
├── docs/
│   ├── ARCHITECTURE.md          # System design & database schema
│   └── PYTHONANYWHERE_DEPLOY.md # Free deployment guide
└── OCS/
    ├── script_actualizar_TAG.py # ⚡ Original production script
    ├── manage.py
    ├── inventario/
    │   ├── models.py            # Asset, Building, Municipio models
    │   ├── views.py             # Dashboard, analytics, API endpoints
    │   ├── forms.py             # Login & registration forms
    │   ├── admin.py             # Django admin configuration
    │   ├── services/
    │   │   ├── data_sources.py  # ETL for Excel data
    │   │   ├── processors.py    # TAG sync engine (Django ORM)
    │   │   ├── reporters.py     # Excel report generator
    │   │   └── analytics.py     # AI engine (z-score, entropy, quality)
    │   ├── management/commands/
    │   │   ├── sync_tags.py     # CLI: python manage.py sync_tags
    │   │   ├── analyze_assets.py # CLI: python manage.py analyze_assets
    │   │   └── seed_demo.py     # CLI: python manage.py seed_demo
    │   └── tests/               # 45+ pytest tests
    ├── templates/               # Bootstrap 5.3 + Chart.js UI
    └── demo_data/               # Sample Excel files for testing
```

---

## Management Commands

```bash
cd OCS

# Synchronize TAGs (cross-reference DB + Excel)
python manage.py sync_tags
python manage.py sync_tags --dry-run       # Preview without changes

# AI analytics (anomaly detection + data quality)
python manage.py analyze_assets --json --output report.json

# Seed demo data (20 assets, 4 municipalities, admin user)
python manage.py seed_demo --reset
```

---

## AI Analytics Engine

Built-in intelligence without external APIs:

| Feature | Method | Output |
|---------|--------|--------|
| **Anomaly Detection** | Z-score outliers (>2σ) | Duplicates, missing TAGs, orphans |
| **Data Quality** | Weighted composite | 0-100 score (A-F grade) |
| **Distribution Balance** | Shannon entropy | 0.0-1.0 balance score |
| **Predictions** | Heuristic estimation | Sync time, coverage projections |

**Access:**
- Web UI: `/analytics/` — Interactive dashboard
- REST API: `/api/analytics/` — JSON endpoint
- CLI: `python manage.py analyze_assets`

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, Django 5.1, Django ORM |
| **Database** | SQLite (default/free) · MySQL 8.0 (optional) |
| **Data Processing** | Pandas 2.2, NumPy 2.1, OpenPyXL |
| **Frontend** | Bootstrap 5.3, Chart.js 4.4, DataTables |
| **Testing** | pytest (45+ tests), pytest-cov, flake8, black, isort |
| **CI/CD** | GitHub Actions (lint → test → security → docker) |
| **Production** | Gunicorn, WhiteNoise, Docker, HSTS |
| **Deployment** | PythonAnywhere (free), Render, Docker |

---

## Documentation

| Document | Description |
|----------|-------------|
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | System design, services layer, database schema, security |
| **[PYTHONANYWHERE_DEPLOY.md](docs/PYTHONANYWHERE_DEPLOY.md)** | 🆓 FREE deployment guide (no credit card) |

---

## Testing

```bash
cd OCS

# Run all tests
python -m pytest

# With coverage report
python -m pytest --cov=inventario --cov-report=term-missing

# Specific module
python -m pytest inventario/tests/test_analytics.py -v
```

**CI Pipeline** runs on every push: **Lint** (flake8, black, isort) → **Test** (Python 3.11/3.12) → **Security audit** → **Docker build**

---

## Authors

**Carlos Manuel Hernández Hernández**  
Cybernetics Student · Full-Stack Developer  
[GitHub](https://github.com/cmhh22)

**Ariel David Toledo Rojas**  
Cybernetics Student · Full-Stack Developer  
[GitHub](https://github.com/ArielDavid234)

---

## License

MIT License — see [LICENSE](LICENSE)

---

**Built with real-world production experience at ETECSA** | [GitHub Issues](https://github.com/cmhh22/etecsa-asset-sync/issues).
