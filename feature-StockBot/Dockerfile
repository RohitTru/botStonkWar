FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3.11-dev \
    libffi-dev \
    build-essential \
    libssl-dev \
    default-libmysqlclient-dev \
    cython3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . .

# Install Python dependencies globally (no venv)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port (use the value from the .env if available)
EXPOSE ${APP_PORT}

# Run the app
CMD ["python", "app.py"]
