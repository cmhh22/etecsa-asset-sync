# Architecture

## System Overview

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
│    │  or SQLite │  │  Excel   │  │   Classifier     │          │
│    │ (Hardware) │  │ (Finance)│  │   (HR/Excel)     │          │
│    └────────────┘  └──────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Data Layer

**Database (OCS Inventory)**
- Primary source of truth for IT assets
- Supports **SQLite** (default/free) and **MySQL** (production)
- Tables: `accountinfo`, `hardware`, managed by OCS Inventory NG
- Contains: hardware specs, BIOS info, network config, last inventory date

**Finance Excel (AR01 Report)**
- Format: `.xlsx` with columns `Inventory No.`, `Building`, `Office`
- Updated monthly by Finance department
- Source of truth for physical asset locations

**HR Locations Classifier**
- Format: `.xlsx` mapping office codes to building names
- Columns: `ID`, `Location`, `Building`
- Maintained by HR department

### 2. Services Layer

#### DataSources (`inventario/services/data_sources.py`)
ETL module for loading external data:
```python
class DataSourceManager:
    get_ar01_data()           # Reads Finance Excel → DataFrame
    get_clasificador_data()   # Reads HR Excel → DataFrame
    get_ocs_assets()          # Queries DB via Django ORM → AccountInfo objects
```

#### Processor (`inventario/services/processors.py`)
Core business logic for TAG synchronization:
```python
class TAGProcessor:
    process_tags(assets, ar01_df, clasificador_df)
    # Returns: (updated_count, error_count, report_data)
    
    # Algorithm:
    # 1. For each asset, lookup inventory number in AR01
    # 2. If found, get edificio + oficina
    # 3. Resolve edificio name from clasificador
    # 4. Generate TAG = f"{edificio}-{oficina}"
    # 5. Update asset.tag field
    # 6. Track anomalies (missing, duplicates, orphans)
```

#### Analytics Engine (`inventario/services/analytics.py`)
AI-powered insights using NumPy and statistical methods:
```python
class AssetAnalyticsEngine:
    _detect_anomalies()        # Z-score outliers, duplicates, orphans
    _compute_data_quality()    # Weighted composite score (0-100)
    _analyze_distributions()   # Entropy-based balance metrics
    _generate_predictions()    # Heuristic sync estimates
```

**Anomaly Detection**:
- **Z-score outliers**: Buildings with asset count > 2 std devs from mean
- **Duplicates**: Same inventory number across multiple records
- **Missing TAGs**: Assets without TAG field populated
- **Orphan records**: Assets in DB not in AR01, and vice versa
- **Invalid patterns**: Office codes not matching HR classifier

**Data Quality Scoring**:
```
Quality Score = 0.30 × Completeness 
              + 0.25 × Consistency 
              + 0.25 × Uniqueness 
              + 0.20 × Validity
```
- **Completeness**: % of assets with all required fields populated
- **Consistency**: % of TAGs matching `Building-Office` format
- **Uniqueness**: % of inventory numbers without duplicates  
- **Validity**: % of office codes existing in HR classifier

**Distribution Balance** (Entropy):
```
Balance = e^H / N
where H = -Σ(p_i × log(p_i))  # Shannon entropy
      N = number of categories
```
- Score 0.0-1.0 (0=all assets in one category, 1=perfectly balanced)

#### Reporter (`inventario/services/reporters.py`)
Excel report generation:
```python
class ExcelReporter:
    generate_report(report_data) → .xlsx file
    
    # Sheets:
    # 1. Empty (empty inventory numbers)
    # 2. VM (virtual machines)
    # 3. Duplicates (duplicate inventory numbers)
    # 4. No TAG after update
    # 5. Not in AR01
    # 6. In AR01 but not in DB
    # 7. Not in classifier
```

### 3. Presentation Layer

#### Views (`inventario/views.py`)
- `login_view()` — Authentication
- `dashboard_view()` — Main statistics overview
- `show_assets()` — Asset detail table  
- `show_reports()` — Reports list
- `sync_tags()` — Trigger TAG sync
- `analytics_view()` — AI analytics dashboard
- `api_analytics()` — JSON API endpoint

#### Templates (`templates/`)
- `base.html` — Sidebar layout, Bootstrap 5.3
- `dashboard.html` — DataTables for asset browsing
- `analytics.html` — Chart.js visualizations (doughnut, bar, ring)
- `reportes.html` — Excel report downloads

### 4. Management Commands

#### `sync_tags` Command
```bash
python manage.py sync_tags
```
- Runs TAG processor synchronously
- Outputs summary to console
- Saves Excel report to `OCS/Reportes.xlsx`

#### `analyze_assets` Command
```bash
python manage.py analyze_assets [--json] [--output FILE]
```
- Runs analytics engine
- Prints metrics or exports JSON
- Useful for CI/CD monitoring

#### `seed_demo` Command
```bash
python manage.py seed_demo [--reset]
```
- Creates 20 sample assets, 4 municipalities, 6 buildings
- Creates admin user: `admin` / `admin123`
- Populates demo Excel files

## Database Schema

```
┌─────────────────┐       ┌──────────────┐       ┌─────────────┐
│  Municipio      │◄──────┤  Edificio    │◄──────┤ AccountInfo │
├─────────────────┤       ├──────────────┤       ├─────────────┤
│ id              │       │ id           │       │ id          │
│ nombre          │       │ nombre       │       │ tag         │
└─────────────────┘       │ municipio_id │       │ noinventario│
                          └──────────────┘       │ edificio_id │
                                                 │ usuario     │
                                                 │ ...         │
                                                 └─────────────┘
          ┌───────────────┐
┌─────────┤  Local        │
│         ├───────────────┤
│         │ id            │
│         │ nombre        │
│         │ edificio_id   │
│         └───────────────┘
│
│         ┌─────────────┐
└─────────┤ CentroCosto │
          ├─────────────┤
          │ id          │
          │ nombre      │
          │ local_id    │
          └─────────────┘
```

**Relationships**:
- `Municipio` 1:N `Edificio` (one municipality has many buildings)
- `Edificio` 1:N `AccountInfo` (one building has many assets)
- `Edificio` 1:N `Local` (one building has many offices)
- `Local` 1:N `CentroCosto` (one office has many cost centers)

## Security Features

### Production Settings (`DEBUG=False`)
```python
# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# XSS protection
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# SSL redirect
SECURE_SSL_REDIRECT = True (optional via env var)
```

### Authentication
- Django's built-in `django.contrib.auth`
- `@login_required` decorators on all views
- CSRF protection on forms

### Environment-based Secrets
```bash
# .env file (not committed)
SECRET_KEY=your-secret-key-here
DB_PASSWORD=your-db-password
DEBUG=False
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

```yaml
jobs:
  lint:
    - flake8 OCS/inventario OCS/conftest.py
    - isort --check-only OCS/inventario
    - black --check OCS/inventario
  
  test:
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    steps:
      - python -m pytest --cov=inventario
  
  security:
    - pip-audit --desc -r OCS/requirements.txt
  
  docker:
    - docker build -t etecsa-asset-sync:test .
```

**Triggers**:
- Every push to `main`
- Every pull request
- Manual dispatch (`workflow_dispatch`)

## Performance Considerations

### Database Optimization
- `select_related()` on ForeignKey fields to reduce N+1 queries
```python
assets = AccountInfo.objects.select_related('edificio', 'edificio__municipio').all()
```

### Pandas Bulk Operations
- Excel files loaded once into memory
- Vectorized operations using Pandas `.merge()`, `.apply()`
- Batch updates to Django ORM

### Analytics Caching
- Analytics results can be cached for 1 hour with Redis (optional)
- Heavy computation (z-score, entropy) done in NumPy arrays

### Static Files
- **Development**: `DEBUG=True`, Django serves via `django.contrib.staticfiles`
- **Production**: `DEBUG=False`, WhiteNoise serves with compression and caching

## Testing Strategy

### Unit Tests (`test_models.py`)
- Model field validation
- Relationship integrity (CASCADE deletes)
- String representations

### Integration Tests (`test_views.py`)
- Authentication flows
- Protected view access
- Form submissions
- API responses

### Service Tests (`test_analytics.py`)
- Anomaly detection accuracy
- Data quality score calculations
- Distribution balance metrics
- Prediction outputs

### Fixtures (`conftest.py`)
```python
@pytest.fixture
def sample_user():
    return User.objects.create_user(username='test', password='test123')

@pytest.fixture
def auth_client(client, sample_user):
    client.login(username='test', password='test123')
    return client
```

## Deployment Architecture

### Docker (Recommended)

```yaml
version: '3.9'
services:
  mysql:
    image: mysql:8.0
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
  
  web:
    build: .
    command: gunicorn OCS.wsgi:application --bind 0.0.0.0:8000 --workers 3
    depends_on:
      mysql:
        condition: service_healthy
    ports:
      - "8000:8000"
```

**Production flow**:
1. `docker-compose up -d` starts MySQL + Gunicorn
2. Health check ensures MySQL ready before Django starts
3. WhiteNoise serves static files with Gzip compression
4. Gunicorn spawns 3 workers for concurrent requests

### PaaS (Railway, Render, Fly.io)

**Build**:
```bash
pip install -r OCS/requirements.txt
python OCS/manage.py collectstatic --noinput
```

**Start**:
```bash
cd OCS && gunicorn OCS.wsgi:application --bind 0.0.0.0:$PORT
```

**Environment Variables**:
- `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS` (important for HTTPS domains)

## Monitoring & Logging

### Structured Logging
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'level': 'INFO'},
        'file': {'class': 'logging.FileHandler', 'filename': 'logs/app.log'},
    },
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO'},
        'inventario': {'handlers': ['console', 'file'], 'level': 'DEBUG'},
    },
}
```

**Log files**:
- `OCS/logs/app.log` — All Django activity
- Includes: TAG sync results, anomaly counts, errors

### Health Checks
```python
# views.py
def health_check(request):
    return JsonResponse({'status': 'ok', 'db': check_db_connection()})
```

## Future Enhancements

- [ ] Redis caching for analytics results
- [ ] Celery for async TAG sync jobs
- [ ] Prometheus metrics exporter
- [ ] Elasticsearch for full-text search
- [ ] GraphQL API for flexible queries
- [ ] Real-time WebSocket updates for sync progress
- [ ] Multi-tenancy for other ETECSA provinces
