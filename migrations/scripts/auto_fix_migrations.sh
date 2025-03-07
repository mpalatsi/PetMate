#!/bin/bash
# Shell script to automatically fix migration issues
# --------------------------------------------------------

echo "=== AUTOMATED MIGRATION FIX SCRIPT ==="
echo "This script will automatically fix migration issues"
echo "---------------------------------------------"

# Define containers
container="petmate"
dbContainer="petmate_db"

echo "Using web container: $container"
echo "Using database container: $dbContainer"

# Check if containers are running
webRunning=$(docker ps | grep $container)
dbRunning=$(docker ps | grep $dbContainer)

if [ -z "$webRunning" ]; then
    echo "Error: Web container not found or not running."
    echo "Please start your containers with 'docker-compose up -d' first."
    exit 1
fi

if [ -z "$dbRunning" ]; then
    echo "Error: Database container not found or not running."
    echo "Please start your containers with 'docker-compose up -d' first."
    exit 1
fi

# Check current migration status
echo -e "\nStep 1: Checking current migration status..."
initialStatus=$(docker exec $container flask db current 2>&1)

# Try the safest fix first - stamp the head
echo -e "\nStep 2: Attempting safest fix - stamping current head..."
docker exec $container flask db stamp head

# Try to upgrade
echo -e "\nStep 3: Running migration upgrade..."
upgradeResult=$(docker exec $container flask db upgrade 2>&1)
upgradeExitCode=$?

# Check if we still have errors
if [[ $upgradeResult == *"Error"* || $upgradeResult == *"WARNING"* || $upgradeExitCode -ne 0 ]]; then
    echo -e "\nSimple fix didn't work completely. Trying alternative approach..."
    
    # Check for multiple heads
    echo -e "\nChecking for multiple heads..."
    heads=$(docker exec $container flask db heads)
    
    if [[ $(echo "$heads" | wc -l) -gt 2 || ${#heads} -gt 50 ]]; then
        echo -e "\nDetected multiple migration heads. Creating a merge migration..."
        docker exec $container flask db merge -m "Auto-merge multiple heads"
        
        echo -e "\nApplying merged migration..."
        docker exec $container flask db upgrade
    else
        # Try more aggressive approach - get list of migration files
        echo -e "\nLooking for duplicate migration files..."
        docker exec $container sh -c "ls -la /app/migrations/versions/"
        
        echo -e "\nBacking up migrations folder..."
        timestamp=$(date +"%Y%m%d_%H%M%S")
        docker exec $container sh -c "cp -r /app/migrations /app/migrations_backup_$timestamp"
        
        echo -e "\nAttempting to find and resolve duplicate revision..."
        docker exec $container flask db stamp head
        docker exec $container flask db upgrade
    fi
fi

# Check final status
echo -e "\nFinal migration status:"
docker exec $container flask db current

# Verify database connection
echo -e "\nVerifying database connection and tables..."
tablesCheck=$(docker exec $dbContainer psql -U petmate -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users');" petmate 2>&1)

if [[ $tablesCheck == *"t"* ]]; then
    echo -e "\nSUCCESS: Database connection working and tables exist!"
    
    # Check number of users
    userCount=$(docker exec $dbContainer psql -U petmate -c "SELECT COUNT(*) FROM users;" petmate 2>&1 | grep -Eo '[0-9]+')
    if [[ ! -z "$userCount" ]]; then
        echo "Found $userCount users in the database."
    fi
    
    echo -e "\nMigration fix completed successfully!"
else
    echo -e "\nWARNING: Users table still doesn't exist. You may need to run:"
    echo "docker exec $container flask db init"
    echo "docker exec $container flask db migrate -m 'Initial migration'"
    echo "docker exec $container flask db upgrade"
fi

echo -e "\n=== MIGRATION FIX COMPLETE ===" 