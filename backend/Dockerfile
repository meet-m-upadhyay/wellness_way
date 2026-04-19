# Use slim python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
COPY requirements-ml.txt .

RUN pip install --no-cache-dir uv && \
    uv pip install --no-cache-dir --system -r requirements.txt && \
    uv pip install --no-cache-dir --system -r requirements-ml.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the app
# Use shell form for variable expansion and -u for unbuffered logs
CMD python -u start_backend.py
