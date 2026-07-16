FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies + Doppler CLI (secrets are injected at runtime via DOPPLER_TOKEN)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    gnupg \
    && curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

USER botuser

# Health check (REDIS_HOST/REDIS_PORT задаются в docker-compose окружении)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import os, redis; redis.Redis(host=os.environ.get('REDIS_HOST', 'redis'), port=int(os.environ.get('REDIS_PORT', '6379'))).ping()" || exit 1

# Run the bot with secrets from Doppler
CMD ["doppler", "run", "--", "python", "main.py"]
