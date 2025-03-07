#!/bin/bash
# Shell script to fix multiple migration heads

echo "Fixing multiple migration heads issue..."

# Use the specific container names
container="petmate"

echo "Using web container: $container"

# Show current migration heads
echo "Checking current migration heads..."
docker exec $container flask db heads

# Create a merge migration to combine multiple heads
echo -e "\nCreating a merge migration to combine multiple heads..."
docker exec $container flask db merge -m "Merge multiple heads"

# Apply the new merge migration
echo -e "\nApplying the new merge migration..."
docker exec $container flask db upgrade

# Verify that the issue is resolved
echo -e "\nVerifying migration status..."
docker exec $container flask db current

echo -e "\nMigration fix complete! The multiple heads should now be merged."
echo "If you still encounter issues, you may need to manually specify which revision to use:"
echo "docker exec $container flask db upgrade <specific_revision_id>" 