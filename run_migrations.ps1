# PowerShell script to run database migrations

Write-Host "Running database migrations..." -ForegroundColor Cyan

# Get the web container name
$container = docker ps --filter "name=petmate" --filter "name=web" --format "{{.Names}}"

if (-not $container) {
    Write-Host "Error: Web container not found. Make sure the containers are running." -ForegroundColor Red
    exit 1
}

Write-Host "Found web container: $container" -ForegroundColor Green

# Run the migrations
Write-Host "Creating database tables..." -ForegroundColor Cyan
docker exec -it $container flask db upgrade

# If the above fails, try the standard database initialization
if ($LASTEXITCODE -ne 0) {
    Write-Host "Migrations failed, trying standard database initialization..." -ForegroundColor Yellow
    docker exec -it $container flask db init
    docker exec -it $container flask db migrate -m "Initial migration"
    docker exec -it $container flask db upgrade
}

# Create test admin user if needed
Write-Host "Would you like to create a test admin user? (y/n)" -ForegroundColor Yellow
$createAdmin = Read-Host

if ($createAdmin -eq "y") {
    Write-Host "Creating test admin user..." -ForegroundColor Cyan
    docker exec -it $container flask create-admin
}

Write-Host "Database setup complete!" -ForegroundColor Green 