# Use Python 3.10 slim image
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust for tokenizers
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y \
    && . "$HOME/.cargo/env" && rustup update stable \
    && ln -s /root/.cargo/bin/rustc /usr/local/bin/rustc \
    && ln -s /root/.cargo/bin/cargo /usr/local/bin/cargo

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port (will be overridden by docker-compose)
EXPOSE ${APP_PORT:-5004}

# Start the Flask application
CMD ["sh", "-c", "flask run --host=0.0.0.0 --port=${APP_PORT:-5004}"]
