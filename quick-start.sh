#!/bin/bash

echo "🚀 Neurom Website Checker - Quick Start Script"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "✅ Python and Node.js are installed"

# Setup Backend
echo ""
echo "🐍 Setting up Python Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install fastapi uvicorn aiohttp beautifulsoup4 pydantic

echo "✅ Backend setup complete!"

# Setup Frontend
echo ""
echo "⚛️ Setting up Next.js Frontend..."
cd ..

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete!"

echo ""
echo "🎉 Setup Complete! Now you can:"
echo ""
echo "1. Start Backend:  cd backend && python simple_main.py"
echo "2. Start Frontend: npm run dev"
echo ""
echo "Or use VS Code tasks:"
echo "- Press Ctrl+Shift+P"
echo "- Type 'Tasks: Run Task'"
echo "- Select '🚀 Start Both Servers'"
echo ""
echo "URLs:"
echo "- Frontend: http://localhost:3000"
echo "- Backend:  http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
