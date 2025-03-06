#!/bin/bash
# Shell script to run database migrations

echo "Running database migrations..."

# Get the web container name
container=$(docker ps --filter "name=petmate" --filter "name=web" --format "{{.Names}}")

if [ -z "$container" ]; then
    echo "Error: Web container not found. Make sure the containers are running."
    exit 1
fi

echo "Found web container: $container"

# Run the migrations
echo "Creating database tables..."
docker exec -it $container flask db upgrade

# If the above fails, try the standard database initialization
if [ $? -ne 0 ]; then
    echo "Migrations failed, trying standard database initialization..."
    docker exec -it $container flask db init
    docker exec -it $container flask db migrate -m "Initial migration"
    docker exec -it $container flask db upgrade
fi

# Create test admin user if needed
echo "Would you like to create a test admin user? (y/n)"
read createAdmin

if [ "$createAdmin" = "y" ]; then
    echo "Creating test admin user..."
    docker exec -it $container flask create-admin
fi

echo "Database setup complete!" 