#!/bin/bash
# Setup script for Docker Airflow environment

set -e

echo "=========================================="
echo "Setting up Docker Airflow Environment"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "  .env file not found!"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo " Created .env file. Please edit it with your API keys."
    else
        echo " .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if CV PDF exists at the configured path
CV_PATH="/Users/alexsandersilveira/Downloads/cv/Profile (6).pdf"
if [ -f "$CV_PATH" ]; then
    echo "📄 Copying CV PDF to data directory..."
    mkdir -p data
    cp "$CV_PATH" data/cv.pdf
    echo " CV PDF copied to data/cv.pdf"
else
    echo "  CV PDF not found at: $CV_PATH"
    echo "Please copy your CV PDF to data/cv.pdf manually"
    mkdir -p data
fi

# Set Airflow UID (for Linux compatibility, optional on macOS)
# On macOS, this is less critical but helps with file permissions
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export AIRFLOW_UID=$(id -u)
    echo " Set AIRFLOW_UID=$AIRFLOW_UID (Linux detected)"
else
    echo "ℹ  macOS detected - AIRFLOW_UID not required, but you can set it if needed"
    echo "   Run: export AIRFLOW_UID=$(id -u) before docker-compose up"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Make sure your .env file has all API keys set"
echo "2. Run: docker-compose up -d"
echo "3. Access Airflow UI at: http://localhost:8080"
echo "   Username: airflow"
echo "   Password: airflow"
echo ""

