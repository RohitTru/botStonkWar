FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libffi-dev \
    build-essential \
    libssl-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . .

# Create and activate the virtual environment, then install dependencies
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port (use the value from the .env if available)
EXPOSE ${APP_PORT}

# Set the entrypoint to activate the virtual environment and run the app
CMD ["/bin/bash", "-c", "source venv/bin/activate && python app.py"]
