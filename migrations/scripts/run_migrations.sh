#!/bin/bash
# Shell script to run database migrations

echo "Running database migrations..."

# Use the specific container name
container="petmate"

echo "Using web container: $container"

# Run the migrations
echo "Creating database tables..."
docker exec $container flask db upgrade

# If the above fails, try the standard database initialization
if [ $? -ne 0 ]; then
    echo "Migrations failed, trying standard database initialization..."
    docker exec $container flask db init
    docker exec $container flask db migrate -m "Initial migration"
    docker exec $container flask db upgrade
fi

# Create test admin user if needed
echo "Would you like to create a test admin user? (y/n)"
read createAdmin

if [ "$createAdmin" = "y" ]; then
    echo "Creating test admin user..."
    docker exec $container flask create-admin
fi

echo "Database setup complete!" 