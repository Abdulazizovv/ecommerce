
# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    git \
    curl \
    wget \
    nano \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /usr/src/app
# Copy requirements file
COPY requirements.txt /usr/src/app/

# Create directories for static and media files
# These directories will be used to store static and media files
RUN mkdir -p /usr/src/app/static /usr/src/app/media

# Set permissions for static and media directories
RUN chmod -R 755 /usr/src/app/static && \
    chown -R www-data:www-data /usr/src/app/static

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# Copy the rest of the application code
COPY . /usr/src/app/
# Expose the port the app runs on
EXPOSE 8000

# Collect static files
RUN python manage.py collectstatic --noinput

# Create directory for gunicorn socket
RUN mkdir -p /var/run/gunicorn

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120", "--reload", "core.wsgi:application"]
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]