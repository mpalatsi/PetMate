@echo off
echo ===================================
echo PetMate Server Starter
echo ===================================
echo.

REM Check if port 5006 is in use
netstat -ano | findstr :5006 > nul
if %errorlevel% equ 0 (
    echo Port 5006 is in use. Killing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5006 ^| findstr LISTENING') do (
        echo Killing process with PID: %%a
        taskkill /F /PID %%a
        timeout /t 1 /nobreak > nul
    )
) else (
    echo Port 5006 is free.
)

echo.
echo ===================================
echo ADMIN ACCESS LINKS:
echo ===================================
echo Direct admin access: http://localhost:5006/admin/direct_access/admin_direct_8675309
echo Admin login page: http://localhost:5006/admin/admin_login
echo ===================================
echo.

echo Starting PetMate server...
echo.
python run.py 