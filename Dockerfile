# Build frontend
FROM node:22-alpine AS frontend

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Runtime image
FROM python:3.14-slim AS runtime

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /usr/local/bin/uv

# Install Python dependencies from lockfile
# gcc is installed and purged in one layer so it never lands in a committed image layer
COPY backend/pyproject.toml backend/uv.lock ./
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    uv sync --frozen --no-dev --no-install-project && \
    apt-get purge -y --auto-remove gcc && \
    rm -rf /root/.cache /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --create-home appuser

# Copy backend source
COPY --chown=appuser:appuser backend/app ./app

# Copy built frontend into /app/static
COPY --chown=appuser:appuser --from=frontend /build/dist ./static

# Use uv-managed virtualenv for runtime binaries
ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
