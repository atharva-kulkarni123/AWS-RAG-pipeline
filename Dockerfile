# ── Stage 1: dependency builder ──────────────────────────────────────────────
# Use a full Python image to compile any C extensions (psycopg2, etc.)
# then copy only the installed packages into the slim runtime image.
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed for psycopg2, cryptography etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY RAG-codebase/RAG-Retrieval/requirements.txt  retrieval-requirements.txt
COPY RAG-codebase/RAG-Ingestion/requirements.txt  ingestion-requirements.txt
COPY RAG-codebase/api/requirements.txt            api-requirements.txt

# Install all deps into a single prefix so we copy one dir
RUN pip install --upgrade pip && \
    pip install \
        --no-cache-dir \
        --prefix=/install \
        -r retrieval-requirements.txt \
        -r ingestion-requirements.txt \
        -r api-requirements.txt


# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user — never run app code as root inside a container
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Pull in OS runtime libs only (no gcc, no headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY RAG-codebase/RAG-Retrieval/ ./RAG-Retrieval/
COPY RAG-codebase/RAG-Ingestion/ ./RAG-Ingestion/
COPY RAG-codebase/api/           ./api/

# Secrets come from Secrets Manager at runtime — never bake
# .env files or credentials into the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/RAG-Retrieval:/app/RAG-Ingestion:/app"

USER appuser

# ALB health check hits port 8080
EXPOSE 8080

# Gunicorn manages worker processes; uvicorn is the ASGI worker.
# 2 workers × (2 × CPU + 1) is the standard formula for I/O-bound apps.
# ECS Fargate task = 1 vCPU → 3 workers is appropriate.
CMD ["gunicorn", "api.main:app", \
     "--workers", "3", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]