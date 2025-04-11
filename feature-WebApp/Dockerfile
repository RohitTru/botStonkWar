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
FROM node:18-alpine
WORKDIR /app

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip mysql-client mysql-dev gcc musl-dev python3-dev

# Set up Python virtual environment
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy backend code and requirements first
COPY backend/requirements.txt /app/backend/
WORKDIR /app/backend
RUN . /app/venv/bin/activate && pip3 install --no-cache-dir -r requirements.txt
WORKDIR /app

# Copy backend from builder
COPY --from=backend-builder /app/ ./backend/

# Copy frontend from builder
COPY --from=frontend-builder /app/package*.json ./
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/node_modules ./node_modules

# Install PM2 globally
RUN npm install -g pm2

# Create start script
RUN echo '#!/bin/sh\ncd /app && pm2 start "npm start" --name frontend && cd backend && . /app/venv/bin/activate && python3 app/main.py' > /app/start.sh
RUN chmod +x /app/start.sh

# Set environment variables
ENV NODE_ENV=production
ENV APP_PORT=5000
ENV PORT=3000

# Expose ports
EXPOSE 3000 5000

# Start both servers
CMD ["/app/start.sh"]
