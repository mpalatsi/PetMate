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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements for Docker
COPY requirements-docker.txt .

# Install Python dependencies in smaller chunks to isolate any failures
RUN pip install --no-cache-dir Flask==2.3.3 Flask-SQLAlchemy==3.1.1 Flask-Migrate==4.0.5 Flask-Login==0.6.3 Werkzeug==2.3.7
RUN pip install --no-cache-dir SQLAlchemy==2.0.23 Jinja2==3.1.2 itsdangerous==2.1.2 click==8.1.7
RUN pip install --no-cache-dir alembic==1.12.1 python-dotenv==1.0.0 
RUN pip install --no-cache-dir Pillow==9.5.0
RUN pip install --no-cache-dir email-validator==2.1.0.post1 gunicorn==21.2.0
RUN pip install --no-cache-dir psycopg2-binary==2.9.9
RUN pip install --no-cache-dir Flask-SocketIO==5.3.4 python-socketio==5.8.0 python-engineio==4.4.1
RUN pip install --no-cache-dir gevent==23.9.1 gevent-websocket==0.10.1 eventlet==0.33.3
RUN pip install --no-cache-dir requests==2.31.0 phonenumbers==8.13.31 bcrypt==4.1.2 beautifulsoup4==4.12.2

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