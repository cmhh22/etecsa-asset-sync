# ETECSA Asset Sync

> 🏢 **Real-world IT asset management system deployed at ETECSA (Cuba's national telecom) in 2024**  
> Automates cross-referencing of MySQL + Excel data sources across IT, Finance, and HR departments

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/django-5.1-green?logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/mysql-8.0-orange?logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/docker-ready-blue?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/tests-45+-success?logo=pytest&logoColor=white" alt="Tests">
  <img src="https://img.shields.io/badge/CI-passing-brightgreen?logo=github-actions" alt="CI">
</p>

---

## Overview

**ETECSA Asset Sync** replaces a fully manual workflow at ETECSA Cienfuegos that required operators to cross-reference computer inventory data across 3 separate systems (OCS Inventory MySQL database, Finance Excel reports, HR location classifiers) to assign office/building tags to each asset.

**Production deployment:**
- The standalone Python script (`script_actualizar_TAG.py`) **is operational today** at ETECSA Cienfuegos
- Processes hundreds of assets across all municipal offices in the province
- Runs on scheduled basis to maintain data integrity

**This repository:**
- Preserves the original production script (still functional)
- Adds a Django web interface as a **portfolio demonstration**
- Includes AI-powered analytics with anomaly detection
- 45+ automated tests with CI/CD pipeline
- Production-ready Docker deployment

---

## Features

| Category | Capabilities |
|----------|-------------|
| **Data Integration** | Merges MySQL + 2 Excel sources (Finance AR01, HR Classifier) |
| **Bulk Updates** | Updates hundreds of TAG fields (`Building-Office` format) in seconds |
| **Anomaly Detection** | Identifies duplicates, missing records, orphans, outliers (z-score) |
| **AI Analytics** | Data quality scoring (0-100), entropy analysis, predictive insights |
| **Reporting** | Multi-sheet Excel reports with auto-fitted columns |
| **Web Dashboard** | Bootstrap 5.3 UI, Chart.js visualizations, REST API |
| **Testing** | 45+ pytest tests (models, views, analytics) + GitHub Actions CI |
| **Production Ready** | Gunicorn, WhiteNoise, HSTS, Docker, environment-based config |

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/cmhh22/etecsa-asset-sync.git
cd etecsa-asset-sync
docker-compose up -d --build
docker-compose exec web python manage.py seed_demo
# → http://localhost:8000 (admin / admin123)
```

### Option 2: Local Development

```bash
cd etecsa-asset-sync/OCS
python -m venv ../env && ..\env\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env  # Edit: DB_ENGINE=django.db.backends.sqlite3
python manage.py migrate && python manage.py seed_demo
python manage.py runserver
```

### Option 3: Deploy to Railway (Free Tier)

1. Push to GitHub
2. Railway.app → "New Project" → Select `etecsa-asset-sync`
3. Add MySQL database (auto-configures `DATABASE_URL`)
4. Set env vars: `SECRET_KEY`, `DEBUG=False`, `CSRF_TRUSTED_ORIGINS`
5. Build: `pip install -r OCS/requirements.txt && cd OCS && python manage.py collectstatic --noinput`
6. Start: `cd OCS && gunicorn OCS.wsgi:application --bind 0.0.0.0:$PORT`

---

## Project Structure

```
OCS/
├── script_actualizar_TAG.py      # ⚡ Original production script (still operational)
├── manage.py
├── inventario/
│   ├── models.py                 # Asset, Building, Municipio models
│   ├── views.py                  # Dashboard, analytics, API endpoints
│   ├── services/
│   │   ├── data_sources.py       # ETL for Excel + MySQL
│   │   ├── processors.py         # TAG sync logic
│   │   ├── reporters.py          # Excel report generator
│   │   └── analytics.py          # AI engine (z-score, entropy, quality scoring)
│   ├── management/commands/
│   │   ├── sync_tags.py          # CLI: python manage.py sync_tags
│   │   ├── analyze_assets.py     # CLI: python manage.py analyze_assets --json
│   │   └── seed_demo.py          # CLI: python manage.py seed_demo
│   └── tests/                    # 45+ pytest tests
├── templates/                    # Bootstrap 5.3 + Chart.js UI
└── demo_data/                    # Sample Excel files for testing
```

---

## Management Commands

```bash
cd OCS

# Run TAG synchronization (cross-reference MySQL + Excel)
python manage.py sync_tags

# Run AI analytics (anomaly detection + data quality)
python manage.py analyze_assets --json --output report.json

# Seed demo data (20 assets, 4 municipalities, admin user)
python manage.py seed_demo --reset
```

---

## AI Analytics Engine

Built-in intelligence without external APIs:

| Feature | Method | Output |
|---------|--------|--------|
| **Anomaly Detection** | Z-score outliers (>2σ) | Duplicates, missing TAGs, orphans, building outliers |
| **Data Quality** | Weighted composite | 0-100 score (A-F grade) based on completeness, consistency, uniqueness, validity |
| **Distribution Balance** | Shannon entropy | 0.0-1.0 score (0=all in one category, 1=perfectly balanced) |
| **Predictions** | Heuristic estimation | Sync time, coverage projections, prioritized recommendations |

**Access**:
- Web UI: `/analytics/` (interactive dashboard)
- REST API: `/api/analytics/` (JSON)
- CLI: `python manage.py analyze_assets`

---

## Tech Stack

- **Backend**: Python 3.12 + Django 5.1 + MySQL 8.0
- **Data Processing**: Pandas 2.2, NumPy 2.1, OpenPyXL
- **Frontend**: Bootstrap 5.3, Chart.js 4.4
- **Testing**: pytest (45+ tests), GitHub Actions CI
- **Production**: Gunicorn, WhiteNoise, Docker, HSTS
- **AI/Analytics**: NumPy (z-score), entropy analysis, composite scoring

---

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design, services layer, database schema, security
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** — Docker, Railway, Render, VPS (Ubuntu), environment variables

---

## Testing

```bash
# Run all tests
python -m pytest

# Coverage report
python -m pytest --cov=inventario --cov-report=term-missing

# Specific module
python -m pytest inventario/tests/test_analytics.py -v
```

GitHub Actions CI runs on every push: **Lint** → **Test** (Python 3.11/3.12 + MySQL) → **Security audit** → **Docker build**

---

## Production Context

**Deployed at ETECSA Cienfuegos (2024)**:
- Automated TAG assignment for all computer assets across municipal offices
- Replaced manual workflow requiring 3 operators
- Still operational today, runs on scheduled basis

**This GitHub repository**:
- Original production script preserved as-is
- Modern Django web interface as portfolio demonstration
- AI analytics, automated testing, CI/CD pipeline
- Showcases full-stack development + DevOps capabilities

---

## License

MIT License — see [LICENSE](LICENSE)

---

**Built with real-world production experience** | [GitHub Issues](https://github.com/cmhh22/etecsa-asset-sync/issues)
