FROM python:3.11-slim

# Runtime knobs — switch off bytecode, keep stdout unbuffered for log aggregation.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WEB_CONCURRENCY=2

WORKDIR /workspace

# Install system deps + build-essential for any wheels that need compiling.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project manifest first for better layer caching of dependencies.
COPY pyproject.toml ./

# Install runtime deps.
RUN pip install --no-cache-dir .

# Copy application source.
COPY app ./app

# Pre-create persistent data dir (mount or volume this in production).
RUN mkdir -p /workspace/data && chown -R 10001:10001 /workspace

# Non-root runtime user.
RUN useradd -u 10001 appuser || true && chown -R 10001:10001 /workspace
USER 10001

EXPOSE 8000

# Lightweight container-level healthcheck for plain Docker / Compose users.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/api/v1/health || exit 1

# Production entrypoint uses `uvicorn` with $WEB_CONCURRENCY workers.
# Exec form with explicit `sh -c` is required so `${PORT}` / `${WEB_CONCURRENCY}`
# get shell-expanded. Defaults guarantee a usable fallback even if the host
# platform (Railway, Render, Fly, plain Docker) does not inject them.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}"]
