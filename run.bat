@echo off
setlocal

echo 🚀 Starting Job Assistant with Docker...

:: Change directory to where the script is located
cd /d %~dp0

:: Check for environment files
if not exist backend\.env (
    echo ⚠️  backend\.env not found, creating from example...
    copy backend\.env.example backend\.env
)

if not exist backend\.env.secrets (
    echo ⚠️  backend\.env.secrets not found, creating from example...
    copy backend\.env.secrets.example backend\.env.secrets
    echo ❗ Please edit backend\.env.secrets and add your MISTRAL_API_KEY.
)

:: Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: Docker is not installed. Please install Docker to continue.
    exit /b 1
)

:: Build and start containers
echo 📦 Building and starting containers...
docker compose up -d --build
if %ERRORLEVEL% neq 0 (
    echo ⚠️  Falling back to old docker-compose command...
    docker-compose up -d --build
)

echo.
echo ✅ Job Assistant is running!
echo 📍 Frontend: http://localhost:3000
echo 📍 Backend API: http://localhost:8000
echo 📍 API Docs: http://localhost:8000/docs
echo.
echo To stop the application, run: docker compose down
echo To view logs, run: docker compose logs -f

pause
