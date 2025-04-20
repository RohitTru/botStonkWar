FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Create and activate the virtual environment
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    # Upgrade pip and install dependencies from the requirements file
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port (use the value from the .env if available)
EXPOSE ${APP_PORT}

# Set the entrypoint to activate the virtual environment and run the app
CMD ["/bin/bash", "-c", "source venv/bin/activate && python app.py"]
