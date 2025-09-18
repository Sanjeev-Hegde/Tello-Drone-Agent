@echo off
echo Starting Tello Drone Agent Web UI...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if we're in the webui directory
if not exist "package.json" (
    echo ERROR: package.json not found
    echo Please run this script from the webui directory
    pause
    exit /b 1
)

REM Check if node_modules exists, if not install dependencies
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
)

echo Starting React development server...
echo Web UI will be available at: http://localhost:3000
echo Make sure the drone agent is running on port 8080
echo.
echo Press Ctrl+C to stop the server
echo.

call npm start