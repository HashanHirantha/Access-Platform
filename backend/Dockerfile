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

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2: Runtime — lean production image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="AccessGuard Team"
LABEL description="AccessGuard FastAPI Backend with PostgreSQL"
LABEL version="1.0.0"

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r accessguard && useradd -r -g accessguard -d /app -s /sbin/nologin accessguard

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN chown -R accessguard:accessguard /app

USER accessguard

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=postgresql+asyncpg://accessguard:accessguard@db:5432/accessguard \
    APP_NAME=AccessGuard \
    APP_VERSION=1.0.0 \
    DEBUG=false

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

