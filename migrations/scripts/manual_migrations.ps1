# Simple script for manual database migrations
# No interactive terminal needed

Write-Host "Looking for containers..." -ForegroundColor Cyan
docker ps

Write-Host "`nRun the following commands manually:" -ForegroundColor Yellow

Write-Host "`n# First initialize the database" -ForegroundColor Cyan
Write-Host "docker exec petmate flask db init" -ForegroundColor White

Write-Host "`n# Create the initial migration" -ForegroundColor Cyan
Write-Host "docker exec petmate flask db migrate -m 'Initial migration'" -ForegroundColor White

Write-Host "`n# Apply the migrations" -ForegroundColor Cyan
Write-Host "docker exec petmate flask db upgrade" -ForegroundColor White

Write-Host "`n# Create admin user (optional)" -ForegroundColor Cyan
Write-Host "docker exec petmate flask create-admin" -ForegroundColor White

Write-Host "`nNote: This script has been updated to use your specific container names." -ForegroundColor Yellow 