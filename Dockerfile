# SPDX-License-Identifier: CC-BY-SA-4.0

FROM python:3.14-slim

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Install system dependencies for yt-dlp
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==2.2.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry: no virtualenv in container
RUN poetry config virtualenvs.create false

# Install dependencies (production only)
RUN poetry install --without dev --no-root --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/

# Create temp directory with proper permissions
RUN mkdir -p /tmp/yt-downloader-bot && chown appuser:appuser /tmp/yt-downloader-bot

# Switch to non-root user
USER appuser

# Set Python path
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Health check: verify the bot process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "bot.main" > /dev/null || exit 1

# Run the bot
CMD ["python", "-m", "bot.main"]
