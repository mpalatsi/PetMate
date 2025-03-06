# PowerShell script to reset the PostgreSQL data volume

Write-Host "WARNING: This will delete ALL data in your PostgreSQL database!" -ForegroundColor Red
Write-Host "Are you sure you want to continue? (y/n)" -ForegroundColor Yellow
$confirm = Read-Host

if ($confirm -ne "y") {
    Write-Host "Operation cancelled." -ForegroundColor Cyan
    exit
}

# Find and stop the running containers
Write-Host "Stopping running containers..." -ForegroundColor Cyan
& docker ps -a --filter "name=petmate" --format "{{.Names}}" | ForEach-Object {
    & docker stop $_
}

# Find and remove the PostgreSQL data volume
Write-Host "Removing PostgreSQL data volume..." -ForegroundColor Cyan
& docker volume ls --filter "name=petmate_postgres_data" --format "{{.Name}}" | ForEach-Object {
    & docker volume rm $_
}

# Restart the containers
Write-Host "Restarting containers with new database..." -ForegroundColor Cyan
& docker compose up -d

Write-Host "PostgreSQL database has been reset." -ForegroundColor Green
Write-Host "You may need to run database migrations to recreate the schema." -ForegroundColor Yellow 