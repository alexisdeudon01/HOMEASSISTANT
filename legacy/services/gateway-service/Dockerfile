FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the environment export script
COPY ../../scripts/export-env.sh /scripts/export-env.sh
RUN chmod +x /scripts/export-env.sh

# Copy protocols directory
COPY ../protocols /app/protocols

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run the application with environment variables loaded
CMD ["/bin/bash", "-c", "source /scripts/export-env.sh && uvicorn main:app --host 0.0.0.0 --port 8000"]
