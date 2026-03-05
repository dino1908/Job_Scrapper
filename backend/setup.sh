#!/bin/bash

echo "Setting up Job Scrapper Backend..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers (for LinkedIn scraping)
echo "Installing Playwright browsers..."
playwright install chromium

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file for non-secret config values."
fi

# Create .env.secrets file if it doesn't exist
if [ ! -f .env.secrets ]; then
    echo "Creating .env.secrets file from template..."
    cp .env.secrets.example .env.secrets
    echo "Please edit .env.secrets and add your API keys."
fi

# Create data directory
mkdir -p data

echo "Setup complete!"
echo "Next steps:"
echo "1. Edit .env.secrets and add your API keys"
echo "2. Activate venv: source venv/bin/activate"
echo "3. Run server: uvicorn app.main:app --reload"
