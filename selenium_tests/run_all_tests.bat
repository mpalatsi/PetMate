@echo off
echo =====================================
echo PetMate Selenium Test Suite Runner
echo =====================================

:: Define the port the Flask server runs on
set FLASK_PORT=5001

:: Clear the screen
cls

:: Kill any process using port 5001 if needed (Optional - uncomment if needed)
:: for /f "tokens=5" %%p in ('netstat -ano | findstr :%FLASK_PORT% | findstr LISTENING') do (
::     echo Killing process with PID: %%p
::     taskkill /F /PID %%p
:: )

:: Start Flask server in a new console window
echo Starting Flask server on port %FLASK_PORT%...
start "PetMate Flask Server" cmd /c "python app.py"

:: Wait a moment for the server to start
echo Waiting for server to start...
timeout /t 5 /nobreak > nul

:: Run the Selenium tests
echo.
echo Running Selenium tests...
python alt_test.py

:: Save the exit code
set EXIT_CODE=%ERRORLEVEL%
echo.
echo Test run completed with exit code %EXIT_CODE%

echo.
echo Press any key to exit...
pause > nul

:: Exit with the same code as the test script
exit /b %EXIT_CODE% 