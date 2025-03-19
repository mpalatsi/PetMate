FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

# Add labels for GitHub Container Registry
LABEL org.opencontainers.image.source=https://github.com/your-username/petmate
LABEL org.opencontainers.image.description="PetMate - A pet playdate matching application"
LABEL org.opencontainers.image.licenses=MIT

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

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