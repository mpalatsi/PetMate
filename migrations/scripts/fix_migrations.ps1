# PowerShell script to fix multiple migration heads

Write-Host "Fixing multiple migration heads issue..." -ForegroundColor Cyan

# Use the specific container names
$container = "petmate"

Write-Host "Using web container: $container" -ForegroundColor Green

# Show current migration heads
Write-Host "Checking current migration heads..." -ForegroundColor Cyan
docker exec $container flask db heads

# Create a merge migration to combine multiple heads
Write-Host "`nCreating a merge migration to combine multiple heads..." -ForegroundColor Yellow
docker exec $container flask db merge -m "Merge multiple heads"

# Apply the new merge migration
Write-Host "`nApplying the new merge migration..." -ForegroundColor Cyan
docker exec $container flask db upgrade

# Verify that the issue is resolved
Write-Host "`nVerifying migration status..." -ForegroundColor Cyan
docker exec $container flask db current

Write-Host "`nMigration fix complete! The multiple heads should now be merged." -ForegroundColor Green
Write-Host "If you still encounter issues, you may need to manually specify which revision to use:" -ForegroundColor Yellow
Write-Host "docker exec $container flask db upgrade <specific_revision_id>" -ForegroundColor White 