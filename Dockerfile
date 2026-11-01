# ============================================================================
# AccessGuard — FastAPI Backend Dockerfile
# ============================================================================
# Multi-stage build for minimal production image
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — install dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies for asyncpg (PostgreSQL C client)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime — lean production image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Labels
LABEL maintainer="AccessGuard Team"
LABEL description="AccessGuard FastAPI Backend with PostgreSQL"
LABEL version="1.0.0"

# Install only the runtime PostgreSQL lib (no compiler)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r accessguard && useradd -r -g accessguard -d /app -s /sbin/nologin accessguard

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ .

# Own the app directory
RUN chown -R accessguard:accessguard /app

# Switch to non-root user
USER accessguard

# Environment defaults (override via docker-compose or -e flags)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=postgresql+asyncpg://accessguard:accessguard@db:5432/accessguard \
    APP_NAME=AccessGuard \
    APP_VERSION=1.0.0 \
    DEBUG=false

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

