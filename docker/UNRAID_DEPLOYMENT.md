# PetMate Deployment Guide for Unraid

This guide provides step-by-step instructions for deploying the PetMate application on an Unraid server using Docker.

## Prerequisites

- Unraid server with Docker support enabled
- Network access to your Unraid server
- Basic knowledge of terminal/SSH commands

## Deployment Steps

### 1. Prepare Deployment Files

The following files are essential for deployment:

- `docker/docker-compose.yml`: Main container configuration
- `docker/production.env`: Environment variables for production
- Support scripts:
  - `migrations/scripts/run_migrations.ps1`/`migrations/scripts/run_migrations.sh`: For database setup
  - `migrations/scripts/reset_db.ps1`: For resetting the database if needed
  - `migrations/scripts/check_status.ps1`: For checking container status

### 2. Transfer Files to Unraid Server

1. Create a directory on your Unraid server:
   ```bash
   mkdir -p /mnt/user/appdata/petmate
   ```

2. Transfer the necessary files:
   ```bash
   scp docker/docker-compose.yml docker/production.env migrations/scripts/run_migrations.sh user@unraid-server:/mnt/user/appdata/petmate/
   ```

3. Connect to your Unraid server:
   ```bash
   ssh user@unraid-server
   ```

4. Navigate to the deployment directory:
   ```bash
   cd /mnt/user/appdata/petmate
   ```

5. Rename the environment file:
   ```bash
   mv production.env .env
   ```

### 3. Configure Environment Variables

1. Edit the .env file to set secure values:
   ```bash
   nano .env
   ```

2. Update the following values:
   - `POSTGRES_PASSWORD`: Set a secure database password
   - `SECRET_KEY`: Set a secure random string
   - `GOOGLE_MAPS_API_KEY`: Your API key
   - `GITHUB_REPOSITORY`: Your GitHub username/repo

### 4. Start the Containers

1. Start the containers using Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Verify the containers are running:
   ```bash
   docker ps | grep petmate
   ```

### 5. Set Up the Database

1. Make the migration script executable:
   ```bash
   chmod +x run_migrations.sh
   ```

2. Run the database migrations:
   ```bash
   ./run_migrations.sh
   ```

3. Follow the prompts to set up the database and create an admin user if desired.

### 6. Access the Application

1. Access the application in your web browser:
   ```
   http://your-unraid-server-ip:5000
   ```

2. Log in with the admin account created during setup or register a new account.

## Maintenance Tasks

### Updating the Application

1. Pull the latest Docker image:
   ```bash
   docker-compose pull
   ```

2. Restart the containers:
   ```bash
   docker-compose up -d
   ```

3. Run migrations if needed:
   ```bash
   ./run_migrations.sh
   ```

### Backing Up the Database

1. Create a PostgreSQL dump:
   ```bash
   docker exec -t petmate_db pg_dump -U petmate petmate > petmate_backup_$(date +%Y-%m-%d).sql
   ```

2. Back up uploaded files:
   ```bash
   tar -czf uploads_backup_$(date +%Y-%m-%d).tar.gz uploads/
   ```

### Monitoring Logs

1. View web application logs:
   ```bash
   docker logs -f petmate_web
   ```

2. View database logs:
   ```bash
   docker logs -f petmate_db
   ```

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Verify container status:
   ```bash
   docker ps | grep petmate
   ```

2. Check database logs:
   ```bash
   docker logs petmate_db
   ```

3. Ensure the PostgreSQL password in your .env file matches the one used to initialize the database.

### Table Not Found Errors

If you see "relation does not exist" errors:

1. Run the migrations:
   ```bash
   ./run_migrations.sh
   ```

2. If migrations fail, you may need to reset the database:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ./run_migrations.sh
   ```

### Web Server Issues

1. Check the web server logs:
   ```bash
   docker logs petmate_web
   ```

2. Verify environment variables are correctly set:
   ```bash
   docker exec petmate_web env | grep DATABASE_URL
   ```

## Optimizing for Unraid

### Docker Auto-Start

Ensure the containers restart automatically:

1. Edit the Docker Compose file:
   ```yaml
   services:
     db:
       restart: unless-stopped
     web:
       restart: unless-stopped
   ```

### Data Persistence

Make sure data persists across container updates:

1. Use named volumes for PostgreSQL data:
   ```yaml
   volumes:
     postgres_data:
       name: petmate_postgres_data
   ```