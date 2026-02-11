#!/usr/bin/env bash
# build.sh — Render build script
# Runs on every deploy to install deps, migrate, and seed demo data

set -o errexit

pip install --upgrade pip
pip install -r OCS/requirements.txt

cd OCS

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Seed demo data (creates admin user + 20 sample assets)
# --reset ensures clean data on each deploy (Render has ephemeral filesystem)
python manage.py seed_demo --reset
