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
- **Web dashboard** — Django-based UI with auth, data table, and report viewer
- **Environment-based config** — Credentials and paths via `.env` file
- **Structured logging** — Timestamped logs to file and console

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Django Web Interface                    │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │  Login   │  │ Asset Table  │  │  Reports Viewer    │  │
│  └──────────┘  └──────┬───────┘  └────────┬───────────┘  │
│                       │                    │              │
│              ┌────────▼────────────────────▼──────┐       │
│              │     sync_tags (Script Engine)      │       │
│              └───┬──────────┬──────────┬──────────┘       │
│                  │          │          │                  │
│         ┌────────▼───┐ ┌───▼────┐ ┌───▼──────────┐      │
│         │   MySQL    │ │ AR01   │ │ Locations    │      │
│         │ OCS Inv.   │ │ Excel  │ │ Classifier   │      │
│         │ (Hardware) │ │(Finance│ │ (HR/Excel)   │      │
│         └────────────┘ └────────┘ └──────────────┘      │
└──────────────────────────────────────────────────────────┘
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

# Start MySQL + Django
docker-compose up -d

# Run migrations and create demo data
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata demo_data/fixtures.json

# Access the app
open http://localhost:8000
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
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

### Running the Sync Script

```bash
cd OCS
python script_actualizar_TAG.py
```

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
├── OCS/                          # Django project root
│   ├── manage.py
│   ├── script_actualizar_TAG.py  # Core sync engine
│   ├── .env.example              # Environment template
│   ├── requirements.txt
│   ├── OCS/                      # Django settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── inventario/               # Main Django app
│   │   ├── models.py             # Asset, Building, Office models
│   │   ├── views.py              # Web views
│   │   ├── urls.py               # URL routing
│   │   └── forms.py              # Auth forms
│   ├── templates/                # HTML templates
│   └── demo_data/                # Sample Excel files for testing
├── docker-compose.yml
├── Dockerfile
├── .gitignore
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.12 |
| **Web Framework** | Django 5.1 |
| **Database** | MySQL 8.0 |
| **Data Processing** | Pandas, OpenPyXL |
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
