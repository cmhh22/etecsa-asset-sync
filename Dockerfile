FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY OCS/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==22.0.0 whitenoise==6.7.0

# Copy project
COPY OCS/ .

# Create logs directory
RUN mkdir -p /app/logs

# Collect static files
RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput 2>/dev/null || true

# Expose port
EXPOSE 8000

# Production server
CMD ["gunicorn", "OCS.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
