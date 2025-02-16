FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        pkg-config \
        python3-dev \
        libpq-dev \
        libssl-dev \
        libffi-dev \
        libblas-dev \
        liblapack-dev \
        libatlas-base-dev \
        gfortran \
        cmake \
        # For lxml
        libxml2-dev \
        libxslt-dev \
        # For Pillow
        libjpeg-dev \
        zlib1g-dev \
        # For Playwright
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        libwayland-client0 \
        # For Tkinter (if needed)
        python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Celery and Flower
RUN pip install --no-cache-dir celery[redis] flower

# Install Playwright browsers
RUN playwright install --with-deps chromium
RUN playwright install-deps

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/db data/url_cache logs

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
