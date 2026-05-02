# -- Stage 1: Builder --
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# -- Stage 2: Runtime --
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser . .
COPY --chown=appuser:appuser .env.example .env

# Switch to non-root user
USER appuser

EXPOSE 8081

# Health check for Cloud Run / K8s liveness probes
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/health')" || exit 1

CMD ["python", "server.py"]
