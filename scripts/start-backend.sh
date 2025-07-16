#!/bin/bash

echo "🚀 Starting Neurom Website Analyzer Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if we're in the backend directory
if [ ! -f "main.py" ]; then
    echo "📁 Navigating to backend directory..."
    cd backend 2>/dev/null || {
        echo "❌ Backend directory not found. Please run this script from the project root or backend directory."
        exit 1
    }
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "📦 Installing basic dependencies..."
    pip install fastapi uvicorn aiohttp beautifulsoup4 pydantic python-multipart
fi

# Check if Redis is available (optional)
if command -v redis-server &> /dev/null; then
    echo "🔄 Starting Redis server..."
    redis-server --daemonize yes --port 6379 2>/dev/null || echo "⚠️  Redis already running or failed to start (optional)"
else
    echo "⚠️  Redis not found - caching will be disabled (optional)"
fi

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use. Attempting to kill existing process..."
    kill -9 $(lsof -ti:8000) 2>/dev/null || echo "Could not kill existing process"
    sleep 2
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:8000..."
echo "📊 API Documentation will be available at http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

# Start with auto-reload for development
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

# Deactivate virtual environment on exit
deactivate
