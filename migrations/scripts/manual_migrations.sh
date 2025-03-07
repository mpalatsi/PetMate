#!/bin/bash
# Simple script for manual database migrations
# No interactive terminal needed

echo "Looking for containers..."
docker ps

echo -e "\nRun the following commands manually:"

echo -e "\n# First initialize the database"
echo "docker exec petmate flask db init"

echo -e "\n# Create the initial migration"
echo "docker exec petmate flask db migrate -m 'Initial migration'"

echo -e "\n# Apply the migrations"
echo "docker exec petmate flask db upgrade"

echo -e "\n# Create admin user (optional)"
echo "docker exec petmate flask create-admin"

echo -e "\nNote: This script has been updated to use your specific container names." 