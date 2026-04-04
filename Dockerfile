# syntax=docker/dockerfile:1.6
# Pinned major image family; bump the digest periodically for security patches.
ARG PYTHON_VERSION=3.12

# ---------- build: compile wheels in an isolated venv ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements-docker.txt .

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements-docker.txt

# Drop .pyc files from the venv copy (slightly smaller layer)
RUN find /venv -name "*.pyc" -delete

# ---------- CI: full app deps + pytest inside this container image ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS ci-test

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY pytest.ini wsgi.py ./
COPY aceest ./aceest/
COPY tests ./tests/

ENV PYTHONPATH=/workspace

RUN pytest -q

# ---------- runtime: minimal attack surface, non-root (default build target) ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/venv/bin:$PATH"

# No package upgrades at runtime; image stays immutable aside from app data (SQLite file).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 aceest \
    && useradd \
        --uid 10001 \
        --gid aceest \
        --home /app \
        --shell /usr/sbin/nologin \
        --no-create-home \
        aceest \
    && mkdir -p /app \
    && chown aceest:aceest /app

WORKDIR /app

COPY --from=builder /venv /venv

COPY --chown=aceest:aceest wsgi.py .
COPY --chown=aceest:aceest aceest ./aceest/

USER aceest

EXPOSE 8000

# /health is unauthenticated JSON — suitable for orchestrator probes.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

# --preload: load app once before workers fork (faster warm-up, lower import overhead).
# Tune workers via docker run ... gunicorn ... or compose command override.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "60", "--worker-tmp-dir", "/dev/shm", "--preload", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
