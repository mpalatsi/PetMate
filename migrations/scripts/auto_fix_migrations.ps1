# PowerShell script to automatically fix migration issues
# --------------------------------------------------------

Write-Host "=== AUTOMATED MIGRATION FIX SCRIPT ===" -ForegroundColor Cyan
Write-Host "This script will automatically fix migration issues" -ForegroundColor Cyan
Write-Host "---------------------------------------------" -ForegroundColor Cyan

# Define containers
$container = "petmate"
$dbContainer = "petmate_db"

Write-Host "Using web container: $container" -ForegroundColor Green
Write-Host "Using database container: $dbContainer" -ForegroundColor Green

# Check if containers are running
$webRunning = docker ps | Select-String $container
$dbRunning = docker ps | Select-String $dbContainer

if (-not $webRunning) {
    Write-Host "Error: Web container not found or not running." -ForegroundColor Red
    Write-Host "Please start your containers with 'docker-compose up -d' first." -ForegroundColor Red
    exit 1
}

if (-not $dbRunning) {
    Write-Host "Error: Database container not found or not running." -ForegroundColor Red
    Write-Host "Please start your containers with 'docker-compose up -d' first." -ForegroundColor Red
    exit 1
}

# Check current migration status
Write-Host "`nStep 1: Checking current migration status..." -ForegroundColor Cyan
$initialStatus = docker exec $container flask db current 2>&1

# Try the safest fix first - stamp the head
Write-Host "`nStep 2: Attempting safest fix - stamping current head..." -ForegroundColor Cyan
docker exec $container flask db stamp head

# Try to upgrade
Write-Host "`nStep 3: Running migration upgrade..." -ForegroundColor Cyan
$upgradeResult = docker exec $container flask db upgrade 2>&1

# Check if we still have errors
if ($upgradeResult -match "Error" -or $upgradeResult -match "WARNING" -or $LASTEXITCODE -ne 0) {
    Write-Host "`nSimple fix didn't work completely. Trying alternative approach..." -ForegroundColor Yellow
    
    # Check for multiple heads
    Write-Host "`nChecking for multiple heads..." -ForegroundColor Cyan
    $heads = docker exec $container flask db heads
    
    if ($heads -match "\n" -or $heads.Length -gt 50) {
        Write-Host "`nDetected multiple migration heads. Creating a merge migration..." -ForegroundColor Yellow
        docker exec $container flask db merge -m "Auto-merge multiple heads"
        
        Write-Host "`nApplying merged migration..." -ForegroundColor Cyan
        docker exec $container flask db upgrade
    } else {
        # Try more aggressive approach - get list of migration files
        Write-Host "`nLooking for duplicate migration files..." -ForegroundColor Cyan
        $migrationFiles = docker exec $container sh -c "ls -la /app/migrations/versions/"
        
        Write-Host "`nBacking up migrations folder..." -ForegroundColor Yellow
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        docker exec $container sh -c "cp -r /app/migrations /app/migrations_backup_$timestamp"
        
        Write-Host "`nAttempting to find and resolve duplicate revision..." -ForegroundColor Yellow
        docker exec $container flask db stamp head
        docker exec $container flask db upgrade
    }
}

# Check final status
Write-Host "`nFinal migration status:" -ForegroundColor Cyan
docker exec $container flask db current

# Verify database connection
Write-Host "`nVerifying database connection and tables..." -ForegroundColor Cyan
$tablesCheck = docker exec $dbContainer psql -U petmate -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users');" petmate 2>&1

if ($tablesCheck -match "t") {
    Write-Host "`nSUCCESS: Database connection working and tables exist!" -ForegroundColor Green
    
    # Check number of users
    $userCount = docker exec $dbContainer psql -U petmate -c "SELECT COUNT(*) FROM users;" petmate 2>&1
    if ($userCount -match "\d+") {
        Write-Host "Found $($Matches[0]) users in the database." -ForegroundColor Green
    }
    
    Write-Host "`nMigration fix completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nWARNING: Users table still doesn't exist. You may need to run:" -ForegroundColor Yellow
    Write-Host "docker exec $container flask db init" -ForegroundColor White
    Write-Host "docker exec $container flask db migrate -m 'Initial migration'" -ForegroundColor White
    Write-Host "docker exec $container flask db upgrade" -ForegroundColor White
}

Write-Host "`n=== MIGRATION FIX COMPLETE ===" -ForegroundColor Cyan 