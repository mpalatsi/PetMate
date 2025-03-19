FROM python:3.11-slim

# Add labels for GitHub Container Registry
LABEL org.opencontainers.image.source=https://github.com/your-username/petmate
LABEL org.opencontainers.image.description="PetMate - A pet playdate matching application"
LABEL org.opencontainers.image.licenses=MIT

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create necessary directories
RUN mkdir -p uploads/profile_pictures uploads/pet_images uploads/playdate_photos uploads/gallery

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=production

# Expose the port the app runs on
EXPOSE 5000

# Use gunicorn with gevent worker for consistency
CMD ["gunicorn", "--worker-class", "gevent", "-w", "1", "--bind", "0.0.0.0:5000", "--timeout", "120", "wsgi:app"] 