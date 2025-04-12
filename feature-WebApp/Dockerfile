# Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ .
RUN npm run build

# Build backend
FROM python:3.9-slim AS backend-builder
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Final stage
FROM python:3.9-slim
WORKDIR /app

# Install Node.js and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    nodejs \
    npm \
    default-libmysqlclient-dev \
    netcat-traditional && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pm2 && \
    rm -rf /var/lib/apt/lists/*

# Copy frontend from builder
COPY --from=frontend-builder /app/package*.json ./
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/node_modules ./node_modules

# Copy backend from builder
COPY --from=backend-builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=backend-builder /app/ ./backend/

# Create a healthcheck script
RUN echo '#!/bin/sh\n\
nc -z localhost 3000 && nc -z localhost 5000\n\
' > /healthcheck.sh && chmod +x /healthcheck.sh

# Set environment variables
ENV NODE_ENV=production
ENV APP_PORT=5000
ENV PORT=3000

# Expose ports
EXPOSE 3000 5000

# Start both services using PM2
CMD pm2 start "npm start" --name frontend && cd backend && python3 app/main.py

# Use netcat for healthcheck (already installed with netcat-traditional)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD /healthcheck.sh
