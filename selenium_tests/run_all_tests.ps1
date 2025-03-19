# PowerShell script to run Selenium tests
Write-Host "====================================="
Write-Host "PetMate Selenium Test Suite Runner"
Write-Host "====================================="

# Flask server port - PetMate appears to use port 5001
$FLASK_PORT = 5001

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    try {
        $null = New-Object System.Net.Sockets.TcpClient -ArgumentList 'localhost', $Port
        return $true
    } 
    catch {
        return $false
    }
}

# Kill any process using the Flask port if needed
if (Test-PortInUse -Port $FLASK_PORT) {
    Write-Host "Port $FLASK_PORT is already in use. Attempting to free it..."
    # Find and kill the process using the port
    $process = Get-NetTCPConnection -LocalPort $FLASK_PORT -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
    if ($process) {
        $processInfo = Get-Process -Id $process -ErrorAction SilentlyContinue
        if ($processInfo) {
            Write-Host "Killing process: $($processInfo.ProcessName) (PID: $process)"
            Stop-Process -Id $process -Force
            Start-Sleep -Seconds 1
        }
    }
}

# Start Flask app in a new PowerShell window
Write-Host "Starting Flask server..."
Start-Process powershell -ArgumentList "-Command `"python app.py`"" -WindowStyle Normal

# Wait for server to start
Write-Host "Waiting for server to start..."
$maxAttempts = 15
$attempts = 0
$serverRunning = $false

while (-not $serverRunning -and $attempts -lt $maxAttempts) {
    $attempts++
    Write-Host "Checking if server is running (attempt $attempts/$maxAttempts)..."
    
    if (Test-PortInUse -Port $FLASK_PORT) {
        $serverRunning = $true
        Write-Host "Server detected running on port $FLASK_PORT."
    } 
    else {
        Start-Sleep -Seconds 1
    }
}

if (-not $serverRunning) {
    Write-Host "Failed to detect server after $maxAttempts attempts. Exiting."
    exit 1
}

# Run Selenium tests
Write-Host "`nRunning Selenium tests..."
python alt_test.py

# Save the exit code
$exitCode = $LASTEXITCODE
Write-Host "`nTest run completed with exit code $exitCode"

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Exit with the same code as the test script
exit $exitCode 