# Use official Python 3.14 slim image
FROM python:3.14-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        libjpeg-dev \
        zlib1g-dev \
        libxml2-dev \
        libxslt1-dev \
        python3-dev \
        wget \
        curl \
        git \
        gcc \
        libpango1.0-0 \
        libcairo2 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        poppler-utils \
        && rm -rf /var/lib/apt/lists/*

# Install Rust (for python-bidi compilation)
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Create working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip first
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Collect static files (optional for Django)
RUN python manage.py collectstatic --noinput

# Expose port (Render uses $PORT env)
EXPOSE 10000

# Command to run Gunicorn
CMD exec gunicorn mysite.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3
