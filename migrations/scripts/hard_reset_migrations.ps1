# PowerShell script to completely reset and recreate database migrations
# CAUTION: This will delete all data and recreate the database from scratch
# --------------------------------------------------------

Write-Host "=== DATABASE HARD RESET SCRIPT ===" -ForegroundColor Red
Write-Host "WARNING: This script will DELETE ALL DATA in your database!" -ForegroundColor Red
Write-Host "It should only be used as a last resort when all other fixes fail." -ForegroundColor Red
Write-Host "---------------------------------------------" -ForegroundColor Red

Write-Host "`nAre you ABSOLUTELY SURE you want to proceed? Type 'YES DELETE ALL DATA' to continue:" -ForegroundColor Yellow
$confirmation = Read-Host

if ($confirmation -ne "YES DELETE ALL DATA") {
    Write-Host "Canceled. No changes were made." -ForegroundColor Green
    exit 0
}

# Define containers
$container = "petmate"
$dbContainer = "petmate_db"

Write-Host "Using web container: $container" -ForegroundColor Cyan
Write-Host "Using database container: $dbContainer" -ForegroundColor Cyan

# Check if containers are running
$webRunning = docker ps | Select-String $container
$dbRunning = docker ps | Select-String $dbContainer

if (-not $webRunning -or -not $dbRunning) {
    Write-Host "Error: One or both containers not found or not running." -ForegroundColor Red
    Write-Host "Please start your containers with 'docker-compose up -d' first." -ForegroundColor Red
    exit 1
}

# Backup migrations folder
Write-Host "`nStep 1: Backing up migrations folder..." -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
docker exec $container sh -c "if [ -d /app/migrations ]; then cp -r /app/migrations /app/migrations_backup_$timestamp; fi"

# Drop all tables
Write-Host "`nStep 2: Dropping all tables in the database..." -ForegroundColor Cyan
docker exec $dbContainer psql -U petmate -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" petmate

# Remove existing migrations
Write-Host "`nStep 3: Removing existing migrations folder..." -ForegroundColor Cyan
docker exec $container sh -c "rm -rf /app/migrations"

# Create fresh migrations
Write-Host "`nStep 4: Initializing new migrations..." -ForegroundColor Cyan
docker exec $container flask db init

# Create first migration
Write-Host "`nStep 5: Creating initial migration..." -ForegroundColor Cyan
docker exec $container flask db migrate -m "Fresh start after reset"

# Apply migration
Write-Host "`nStep 6: Applying migration..." -ForegroundColor Cyan
docker exec $container flask db upgrade

# Verify database
Write-Host "`nStep 7: Verifying database setup..." -ForegroundColor Cyan
$tablesCheck = docker exec $dbContainer psql -U petmate -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" petmate 2>&1

if ($tablesCheck -match "users") {
    Write-Host "`nSUCCESS: Tables created successfully!" -ForegroundColor Green
    Write-Host "Do you want to create an admin user? (y/n)" -ForegroundColor Yellow
    $createAdmin = Read-Host
    
    if ($createAdmin -eq "y") {
        Write-Host "Creating admin user..." -ForegroundColor Cyan
        docker exec $container flask create-admin
    }
    
    Write-Host "`nDatabase reset completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nWARNING: Tables may not have been created properly." -ForegroundColor Yellow
    Write-Host "Database tables found:" -ForegroundColor Yellow
    docker exec $dbContainer psql -U petmate -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" petmate
}

Write-Host "`n=== HARD RESET COMPLETE ===" -ForegroundColor Red 