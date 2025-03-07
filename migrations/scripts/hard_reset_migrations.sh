#!/bin/bash
# Shell script to completely reset and recreate database migrations
# CAUTION: This will delete all data and recreate the database from scratch
# --------------------------------------------------------

echo "=== DATABASE HARD RESET SCRIPT ==="
echo "WARNING: This script will DELETE ALL DATA in your database!"
echo "It should only be used as a last resort when all other fixes fail."
echo "---------------------------------------------"

echo -e "\nAre you ABSOLUTELY SURE you want to proceed? Type 'YES DELETE ALL DATA' to continue:"
read confirmation

if [ "$confirmation" != "YES DELETE ALL DATA" ]; then
    echo "Canceled. No changes were made."
    exit 0
fi

# Define containers
container="petmate"
dbContainer="petmate_db"

echo "Using web container: $container" 
echo "Using database container: $dbContainer"

# Check if containers are running
webRunning=$(docker ps | grep $container)
dbRunning=$(docker ps | grep $dbContainer)

if [ -z "$webRunning" ] || [ -z "$dbRunning" ]; then
    echo "Error: One or both containers not found or not running."
    echo "Please start your containers with 'docker-compose up -d' first."
    exit 1
fi

# Backup migrations folder
echo -e "\nStep 1: Backing up migrations folder..."
timestamp=$(date +"%Y%m%d_%H%M%S")
docker exec $container sh -c "if [ -d /app/migrations ]; then cp -r /app/migrations /app/migrations_backup_$timestamp; fi"

# Drop all tables
echo -e "\nStep 2: Dropping all tables in the database..."
docker exec $dbContainer psql -U petmate -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" petmate

# Remove existing migrations
echo -e "\nStep 3: Removing existing migrations folder..."
docker exec $container sh -c "rm -rf /app/migrations"

# Create fresh migrations
echo -e "\nStep 4: Initializing new migrations..."
docker exec $container flask db init

# Create first migration
echo -e "\nStep 5: Creating initial migration..."
docker exec $container flask db migrate -m "Fresh start after reset"

# Apply migration
echo -e "\nStep 6: Applying migration..."
docker exec $container flask db upgrade

# Verify database
echo -e "\nStep 7: Verifying database setup..."
tablesCheck=$(docker exec $dbContainer psql -U petmate -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" petmate 2>&1)

if [[ $tablesCheck == *"users"* ]]; then
    echo -e "\nSUCCESS: Tables created successfully!"
    echo "Do you want to create an admin user? (y/n)"
    read createAdmin
    
    if [ "$createAdmin" = "y" ]; then
        echo "Creating admin user..."
        docker exec $container flask create-admin
    fi
    
    echo -e "\nDatabase reset completed successfully!"
else
    echo -e "\nWARNING: Tables may not have been created properly."
    echo "Database tables found:"
    docker exec $dbContainer psql -U petmate -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" petmate
fi

echo -e "\n=== HARD RESET COMPLETE ===" 