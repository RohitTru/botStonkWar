FROM python:3.10-slim

WORKDIR /app

# Install system dependencies and Rust
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    curl \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && curl https://sh.rustup.rs -sSf | bash -s -- -y \
    && . "$HOME/.cargo/env" && rustup update stable \
    && ln -s /root/.cargo/bin/rustc /usr/local/bin/rustc \
    && ln -s /root/.cargo/bin/cargo /usr/local/bin/cargo

# Upgrade pip
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

EXPOSE ${APP_PORT}

CMD ["flask", "run", "--host=0.0.0.0", "--port=${APP_PORT}"]
