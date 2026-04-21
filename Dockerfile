FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create log/data dirs
RUN mkdir -p logs data

# Non-root user for security
RUN useradd -m -u 1000 trader && chown -R trader:trader /app
USER trader

# Default: run the engine in live mode
ENTRYPOINT ["python", "-m", "src.engine"]
CMD ["--mode", "live", "--session", "default"]
