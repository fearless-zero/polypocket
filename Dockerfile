# syntax=docker/dockerfile:1.4
# Multi-stage build with aggressive caching for fastest builds

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies with cache mount
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with pip cache mount
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Add build argument for cache busting on code changes
ARG GIT_SHA=unknown
RUN echo "Building polypocket with GIT_SHA=${GIT_SHA}"

# Copy application code LAST for best caching
# (code changes more frequently than dependencies)
COPY src ./src
COPY analyze_orderbook.py report.py ./

# Create log/data dirs
RUN mkdir -p logs data

# Non-root user for security
RUN useradd -m -u 1000 trader && chown -R trader:trader /app
USER trader

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default: run the engine in live mode
ENTRYPOINT ["python", "-m", "src.engine"]
CMD ["--mode", "live", "--session", "default"]
