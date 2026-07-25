# Dockerfile for Django Education System
# Multi-stage build for production optimization

# ==========================================
# Stage 1: Base image with dependencies
# ==========================================
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libfreetype6 \
    libpng16-16 \
    libjpeg62-turbo \
    libwebp7 \
    libtiff6 \
    libopenjp2-7 \
    libgif7 \
    libxml2 \
    libxslt1.1 \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libffi-dev \
    libcairo2 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# Stage 2: Build dependencies
# ==========================================
FROM base as builder

WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 3: Final production image
# ==========================================
FROM base as production

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -r django && useradd -r -g django django

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

# Copy project files
COPY --chown=django:django . .

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Entrypoint script
COPY --chown=django:django entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "edu_system.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--worker-class", "gthread", "--access-logfile", "-", "--error-logfile", "-"]
