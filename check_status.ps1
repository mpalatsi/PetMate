# PowerShell script to check the status of the Docker containers and PostgreSQL database

Write-Host "Checking Docker container status..." -ForegroundColor Cyan
docker ps -a --filter "name=petmate"

# Get web container name
$webContainer = docker ps --filter "name=petmate" --filter "name=web" --format "{{.Names}}"
$dbContainer = docker ps --filter "name=petmate" --filter "name=db" --format "{{.Names}}"

if (-not $webContainer) {
    Write-Host "Web container not found or not running." -ForegroundColor Red
} else {
    Write-Host "`nWeb container logs (last 10 lines):" -ForegroundColor Cyan
    docker logs --tail 10 $webContainer
}

if (-not $dbContainer) {
    Write-Host "`nDatabase container not found or not running." -ForegroundColor Red
} else {
    Write-Host "`nDatabase container status:" -ForegroundColor Cyan
    
    # Check if the database is running and tables exist
    $tablesExist = docker exec -it $dbContainer psql -U petmate -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users');" 2>&1
    
    if ($tablesExist -match "t") {
        Write-Host "Database is running and users table exists." -ForegroundColor Green
        
        # Check number of users
        $userCount = docker exec -it $dbContainer psql -U petmate -c "SELECT COUNT(*) FROM users;" 2>&1
        if ($userCount -match "\d+") {
            Write-Host "Number of users in database: $($Matches[0])" -ForegroundColor Green
        }
    } else {
        Write-Host "Database is running but users table does not exist. You need to run migrations." -ForegroundColor Yellow
    }
}

Write-Host "`nDatabase connection information:" -ForegroundColor Cyan
Write-Host "Host: db" -ForegroundColor White
Write-Host "Port: 5432" -ForegroundColor White
Write-Host "Database: petmate" -ForegroundColor White
Write-Host "Username: petmate" -ForegroundColor White
Write-Host "Password: [from your production.env file]" -ForegroundColor White

Write-Host "`nTo run database migrations, use:" -ForegroundColor Yellow
Write-Host ".\run_migrations.ps1" -ForegroundColor White 