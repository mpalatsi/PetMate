#!/bin/bash
# Shell script to fix duplicate migration revisions

echo "Fixing duplicate migration revision issue..."

# Use the specific container names
container="petmate"
dbContainer="petmate_db"

echo "Using web container: $container"
echo "Using database container: $dbContainer"

# Check migration history
echo "Checking migration history..."
docker exec $container flask db history

# List migration files to find duplicates
echo -e "\nListing migration files to find duplicates..."
docker exec $container sh -c "ls -la /app/migrations/versions/"

echo -e "\nLooking for revision 8395c7dd69b4..."
docker exec $container sh -c "grep -l '8395c7dd69b4' /app/migrations/versions/*.py"

echo -e "\n== SOLUTIONS ==\n"

echo "OPTION 1: Mark the problematic revision as resolved (safest if it's just a warning)"
echo "Run: docker exec $container flask db stamp head"

echo -e "\nOPTION 2: Reset the database and migrations (if data can be recreated)"
echo "1. Back up any important data"
echo "2. Run: docker-compose down -v"
echo "3. Run: docker-compose up -d"
echo "4. Run: docker exec $container flask db init"
echo "5. Run: docker exec $container flask db migrate"
echo "6. Run: docker exec $container flask db upgrade"

echo -e "\nOPTION 3: Find and manually remove the duplicate file (for advanced users)"
echo "1. Based on the file listing above, identify which file is the duplicate"
echo "2. Run: docker exec $container sh -c 'mv /app/migrations/versions/[duplicate_filename].py /app/migrations/versions/[duplicate_filename].py.bak'"
echo "3. Run: docker exec $container flask db stamp head"
echo "4. Run: docker exec $container flask db upgrade" 