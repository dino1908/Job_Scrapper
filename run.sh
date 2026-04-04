#!/bin/bash

# Ensure we're in the project root
cd "$(dirname "$0")"

echo "🚀 Starting Job Assistant with Docker..."

# Check for environment files
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found, creating from example..."
    cp backend/.env.example backend/.env
fi

if [ ! -f "backend/.env.secrets" ]; then
    echo "⚠️  backend/.env.secrets not found, creating from example..."
    cp backend/.env.secrets.example backend/.env.secrets
    echo "❗ Please edit backend/.env.secrets and add your MISTRAL_API_KEY."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker to continue."
    exit 1
fi

# Check if Docker Compose is installed (docker-compose or docker compose)
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo "❌ Error: Docker Compose is not installed."
    exit 1
fi

# Run the project
echo "📦 Building and starting containers..."
$COMPOSE up -d --build

echo ""
echo "✅ Job Assistant is running!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop the application, run: $COMPOSE down"
echo "To view logs, run: $COMPOSE logs -f"
