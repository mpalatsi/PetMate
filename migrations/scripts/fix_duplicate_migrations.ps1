# PowerShell script to fix duplicate migration revisions

Write-Host "Fixing duplicate migration revision issue..." -ForegroundColor Cyan

# Use the specific container names
$container = "petmate"
$dbContainer = "petmate_db"

Write-Host "Using web container: $container" -ForegroundColor Green
Write-Host "Using database container: $dbContainer" -ForegroundColor Green

# Check migration history
Write-Host "Checking migration history..." -ForegroundColor Cyan
docker exec $container flask db history

# List migration files to find duplicates
Write-Host "`nListing migration files to find duplicates..." -ForegroundColor Yellow
docker exec $container sh -c "ls -la /app/migrations/versions/"

Write-Host "`nLooking for revision 8395c7dd69b4..." -ForegroundColor Cyan
docker exec $container sh -c "grep -l '8395c7dd69b4' /app/migrations/versions/*.py"

Write-Host "`n== SOLUTIONS ==`n" -ForegroundColor Green

Write-Host "OPTION 1: Mark the problematic revision as resolved (safest if it's just a warning)" -ForegroundColor Yellow
Write-Host "Run: docker exec $container flask db stamp head" -ForegroundColor White

Write-Host "`nOPTION 2: Reset the database and migrations (if data can be recreated)" -ForegroundColor Yellow
Write-Host "1. Back up any important data" -ForegroundColor White
Write-Host "2. Run: docker-compose down -v" -ForegroundColor White
Write-Host "3. Run: docker-compose up -d" -ForegroundColor White
Write-Host "4. Run: docker exec $container flask db init" -ForegroundColor White
Write-Host "5. Run: docker exec $container flask db migrate" -ForegroundColor White
Write-Host "6. Run: docker exec $container flask db upgrade" -ForegroundColor White

Write-Host "`nOPTION 3: Find and manually remove the duplicate file (for advanced users)" -ForegroundColor Yellow
Write-Host "1. Based on the file listing above, identify which file is the duplicate" -ForegroundColor White
Write-Host "2. Run: docker exec $container sh -c 'mv /app/migrations/versions/[duplicate_filename].py /app/migrations/versions/[duplicate_filename].py.bak'" -ForegroundColor White
Write-Host "3. Run: docker exec $container flask db stamp head" -ForegroundColor White
Write-Host "4. Run: docker exec $container flask db upgrade" -ForegroundColor White 