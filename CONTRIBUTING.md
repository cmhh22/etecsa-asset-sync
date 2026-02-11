# Contributing to ETECSA Asset Sync

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/etecsa-asset-sync.git
cd etecsa-asset-sync/OCS

# 2. Create virtual environment
python -m venv ../env
# Windows: ..\env\Scripts\activate
# Linux/Mac: source ../env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — for quick demo, set DB_ENGINE=django.db.backends.sqlite3

# 5. Run migrations and seed demo data
python manage.py migrate
python manage.py seed_demo

# 6. Start the development server
python manage.py runserver
```

## Running Tests

```bash
cd OCS
python -m pytest                                        # Run all tests
python -m pytest -v                                     # Verbose output
python -m pytest --cov=inventario --cov-report=term     # With coverage
python -m pytest inventario/tests/test_analytics.py -v  # Specific module
```

## Code Quality

Before submitting changes, run the linters:

```bash
cd OCS
flake8 inventario/ --max-line-length=120 --exclude=migrations,__pycache__
isort inventario/ --check-only --profile black
black inventario/ --check --line-length=120
```

To auto-format:
```bash
isort inventario/ --profile black
black inventario/ --line-length=120
```

## Docker

```bash
docker-compose up -d --build     # Build and run
docker-compose exec web python manage.py seed_demo  # Seed demo data
docker-compose logs -f web       # Watch logs
docker-compose down              # Stop
```

## Project Structure

- `inventario/services/` — Business logic (ETL, sync, analytics)
- `inventario/tests/` — pytest test suite
- `inventario/management/commands/` — Django CLI commands
- `templates/` — Bootstrap 5.3 HTML templates

## Pull Request Guidelines

1. Create a feature branch from `main`
2. Keep changes focused on a single feature or fix
3. Include or update tests for any new functionality
4. Ensure all tests pass and linters are clean
5. Write a clear description of what the PR does and why
