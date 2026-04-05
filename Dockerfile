FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY notifications-manager/ ./notifications-manager/

# Create directories for data and models
RUN mkdir -p /app/data /app/models

# Set Python path
ENV PYTHONPATH=/app

EXPOSE 5000

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "notifications-manager.nm"]
