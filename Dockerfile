FROM python:3.10-slim

# Set timezone
ENV TZ=Asia/Bangkok
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p logs

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set proper permissions
RUN chmod +x main.py

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s \
  CMD python -c "import os; exit(0 if os.path.exists('sl_manager.log') else 1)"

# Run the Stop Loss Manager
CMD ["python3", "main.py"] 
