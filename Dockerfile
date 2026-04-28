# ============================================================================
# STAGE 1: BUILDER
# ============================================================================
# This stage installs dependencies. We'll throw this away in the final image.
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Copy requirements first (Docker caches this layer if requirements don't change)
COPY requirements.txt .

# Install dependencies to a virtual environment
# --default-timeout=120 increases timeout from 15s to 120s (for slow networks)
# --retries 5 retries failed downloads up to 5 times
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements.txt

# ============================================================================
# STAGE 2: RUNTIME
# ============================================================================
# This is our final image - slim and clean
FROM python:3.11-slim

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

# Create a non-root user for security (Cloud Run best practice)
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy the virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code
# 📌 Important: We copy from my_flask_app because that's where run.py is
COPY ./my_flask_app /app

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check - tells Docker/Cloud Run if the container is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8080}/health')" || exit 1

# Create entrypoint script for proper signal handling
RUN echo '#!/bin/bash\nexec gunicorn \\\n    --bind 0.0.0.0:${PORT:-8080} \\\n    --workers 2 \\\n    --worker-class gevent \\\n    --timeout 120 \\\n    --access-logfile - \\\n    --error-logfile - \\\n    --log-level info \\\n    run:app' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# 🚀 Use entrypoint script (better signal handling than direct CMD)
ENTRYPOINT ["/app/entrypoint.sh"]
