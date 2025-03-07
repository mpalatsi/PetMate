# PowerShell script to rebuild and restart the Docker containers

Write-Host "Stopping existing containers..." -ForegroundColor Cyan
docker-compose down

Write-Host "Rebuilding the web container (no cache)..." -ForegroundColor Cyan
docker-compose build --no-cache web

Write-Host "Starting containers..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "Containers started. Showing logs..." -ForegroundColor Cyan
docker-compose logs -f
