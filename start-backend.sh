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

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
else
    echo "📦 Installing basic dependencies..."
    pip3 install fastapi uvicorn aiohttp beautifulsoup4 pydantic
fi

# Check if Redis is available (optional)
if command -v redis-server &> /dev/null; then
    echo "🔄 Starting Redis server..."
    redis-server --daemonize yes --port 6379 2>/dev/null || echo "⚠️  Redis already running or failed to start (optional)"
else
    echo "⚠️  Redis not found - caching will be disabled (optional)"
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:8000..."
echo "📊 API Documentation will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
