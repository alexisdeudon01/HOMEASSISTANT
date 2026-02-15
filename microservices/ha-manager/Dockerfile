FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a script to export environment variables
COPY scripts/export-env.sh /usr/local/bin/export-env.sh
RUN chmod +x /usr/local/bin/export-env.sh

# Expose port
EXPOSE 8000

# Run the application with environment variables loaded
CMD ["/bin/bash", "-c", "source /usr/local/bin/export-env.sh && python main.py"]
