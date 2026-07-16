FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies + Doppler CLI (secrets are injected at runtime via DOPPLER_TOKEN)
# gpgv (не gnupg!) — в Debian trixie это отдельный пакет, инсталлятор Doppler проверяет подпись именно им
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    gpgv \
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

# Run the bot with secrets from Doppler
CMD ["doppler", "run", "--", "python", "main.py"]
