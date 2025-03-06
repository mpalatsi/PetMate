# PetMate Deployment Guide

This guide provides instructions for deploying the PetMate application to production using Docker and Docker Compose, specifically targeting Unraid servers.

## Prerequisites

- Unraid server with Docker support
- Docker and Docker Compose installed on your development machine
- Git repository access (if applicable)

## Deployment Steps

### 1. Prepare Environment Variables

1. Copy the example environment file to create your production environment file:
   ```
   cp .env.example production.env
   ```

2. Edit the `production.env` file and update the following values with secure credentials:
   - `POSTGRES_PASSWORD`: A strong password for the PostgreSQL database
   - `SECRET_KEY`: A secure random string for Flask's secret key
   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `GITHUB_REPOSITORY`: Your GitHub username and repository name (e.g., `username/petmate`)
   - `IMAGE_TAG`: The version tag of the Docker image to use (e.g., `latest`, `1.0.0`)

### 2. Choose a Deployment Method

You have two options for deploying PetMate:

#### Option A: Using Pre-built Images from GitHub Container Registry

This is the recommended approach for production deployments. It uses Docker images that are automatically built and published to GitHub Container Registry when you create a new release.

1. Make sure you have access to the GitHub Container Registry images. If the repository is private, you'll need to authenticate:
   ```
   docker login ghcr.io -u YOUR_GITHUB_USERNAME
   ```

2. Start the containers using the production Docker Compose file:
   ```
   docker-compose --env-file production.env up -d
   ```

#### Option B: Building Locally

This approach is useful for development or if you need to make custom modifications.

1. Build and start the containers:
   ```
   docker-compose -f docker-compose.dev.yml --env-file production.env up --build -d
   ```

### 3. Deploy to Unraid Server

#### Option 1: Using Docker Compose on Unraid with GitHub Container Registry

1. Copy the project files to your Unraid server:
   ```
   scp -r docker-compose.yml production.env user@unraid-server:/path/on/unraid/petmate/
   ```

2. SSH into your Unraid server:
   ```
   ssh user@unraid-server
   ```

3. Navigate to the project directory and start the containers:
   ```
   cd /path/on/unraid/petmate
   docker-compose --env-file production.env up -d
   ```

#### Option 2: Using Unraid's Docker Manager

1. In the Unraid web interface, go to the Docker tab

2. For the PostgreSQL database:
   - Click "Add Container"
   - Repository: `postgres:15`
   - Name: `petmate-db`
   - Add the following environment variables:
     - `POSTGRES_USER`: `petmate`
     - `POSTGRES_PASSWORD`: Your secure password
     - `POSTGRES_DB`: `petmate`
   - Add a volume mapping for persistent data:
     - Host Path: `/mnt/user/appdata/petmate/postgres`
     - Container Path: `/var/lib/postgresql/data`

3. For the PetMate web application:
   - Click "Add Container"
   - Repository: Point to your built Docker image or use a private registry
   - Name: `petmate-web`
   - Add the environment variables from your production.env file
   - Add volume mappings:
     - Host Path: `/mnt/user/appdata/petmate/uploads`
     - Container Path: `/app/uploads`
   - Set the network mode to bridge and map port 5000

### 4. Database Migration

After deploying, you need to run database migrations:

```
docker exec -it petmate-web flask db upgrade
```

### 5. Create Admin User

Create an admin user for the application:

```
docker exec -it petmate-web flask create-admin
```

### 6. Accessing the Application

Access the application at `http://your-unraid-ip:5000`

## Maintenance

### Updating the Application

1. Pull the latest changes (if using Git):
   ```
   git pull origin main
   ```

2. Rebuild and restart the containers:
   ```
   docker-compose --env-file production.env up --build -d
   ```

### Backup

#### Database Backup

```
docker exec -t petmate-db pg_dump -U petmate petmate > backup_$(date +%Y-%m-%d_%H-%M-%S).sql
```

#### Uploads Backup

```
tar -czf uploads_backup_$(date +%Y-%m-%d_%H-%M-%S).tar.gz uploads/
```

## Troubleshooting

### Viewing Logs

```
docker-compose logs -f
```

### Database Connection Issues

If the web application cannot connect to the database:

1. Verify the database container is running:
   ```
   docker ps | grep petmate-db
   ```

2. Check the database logs:
   ```
   docker logs petmate-db
   ```

3. Ensure the `DATABASE_URL` environment variable is correctly set in the web container.

### Web Application Issues

1. Check the web application logs:
   ```
   docker logs petmate-web
   ```

2. Verify all required environment variables are set correctly.

## Local Development

For local development without Docker:

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   export FLASK_APP=wsgi.py
   export FLASK_ENV=development
   ```

4. Run the application:
   ```
   python run.py
   ```

## Creating and Using GitHub Releases

To create a new release that will automatically build and publish a Docker image:

1. Go to your GitHub repository
2. Click on "Releases" in the right sidebar
3. Click "Create a new release"
4. Enter a version tag (e.g., `v1.0.0`)
5. Add a title and description
6. Click "Publish release"

The GitHub Actions workflow will automatically build and publish a Docker image to GitHub Container Registry. You can then update your `production.env` file to use the new version:

```
IMAGE_TAG=1.0.0
```

And restart your containers:

```
docker-compose --env-file production.env up -d
``` 