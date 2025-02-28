@echo off
echo PetMate Location Search Upgrade Process
echo ======================================
echo.

echo Step 1: Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error installing packages. Please check requirements.txt.
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo Step 2: Running database migration...
python migrate.py
if %ERRORLEVEL% NEQ 0 (
    echo Error during migration. Please check the error message.
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo Step 3: Geocoding existing playdates...
python geocode_playdates.py
if %ERRORLEVEL% NEQ 0 (
    echo Error during geocoding. Please check the error message.
    pause
    exit /b %ERRORLEVEL%
)
echo.

echo Upgrade process completed successfully!
echo Please restart your application to apply the changes.
echo.

pause 