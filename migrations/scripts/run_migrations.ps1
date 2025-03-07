# PowerShell script to run database migrations

Write-Host "Running database migrations..." -ForegroundColor Cyan

# Use the specific container name
$container = "petmate"

Write-Host "Using web container: $container" -ForegroundColor Green

# Run the migrations
Write-Host "Creating database tables..." -ForegroundColor Cyan
docker exec $container flask db upgrade

# If the above fails, try the standard database initialization
if ($LASTEXITCODE -ne 0) {
    Write-Host "Migrations failed, trying standard database initialization..." -ForegroundColor Yellow
    docker exec $container flask db init
    docker exec $container flask db migrate -m "Initial migration"
    docker exec $container flask db upgrade
}

# Create test admin user if needed
Write-Host "Would you like to create a test admin user? (y/n)" -ForegroundColor Yellow
$createAdmin = Read-Host

if ($createAdmin -eq "y") {
    Write-Host "Creating test admin user..." -ForegroundColor Cyan
    docker exec $container flask create-admin
}

Write-Host "Database setup complete!" -ForegroundColor Green 