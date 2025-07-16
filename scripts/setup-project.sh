#!/bin/bash

echo "🔧 Setting up Website Audit Tool Project..."

# Make scripts executable
chmod +x scripts/start-backend.sh
chmod +x scripts/setup-project.sh

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Create backend directory if it doesn't exist
if [ ! -d "backend" ]; then
    echo "📁 Creating backend directory..."
    mkdir backend
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "backend/requirements.txt" ]; then
    echo "📝 Creating requirements.txt..."
    cat > backend/requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
aiohttp==3.9.1
beautifulsoup4==4.12.2
pydantic==2.5.0
python-multipart==0.0.6
redis==5.0.1
requests==2.31.0
lxml==4.9.3
EOF
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "🔐 Creating .env.local..."
    cat > .env.local << EOF
# Backend API Configuration
BACKEND_URL=http://localhost:8000

# Optional: Add other environment variables as needed
NEXT_PUBLIC_API_URL=http://localhost:3000/api
EOF
fi

# Create .gitignore additions
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << EOF
# Dependencies
node_modules/
backend/venv/
backend/__pycache__/

# Environment variables
.env.local
.env.production

# Build outputs
.next/
dist/
build/

# Logs
*.log
logs/

# OS generated files
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Python specific
*.pyc
*.pyo
*.pyd
__pycache__/
.Python
pip-log.txt
pip-delete-this-directory.txt

# Redis
dump.rdb
EOF
fi

echo "✅ Project setup complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Run: ./scripts/start-backend.sh (to start Python API)"
echo "2. Run: npm run dev (to start frontend)"
echo "3. Visit: http://localhost:3000"
echo ""
echo "📊 Available commands:"
echo "- npm run backend          # Start backend only"
echo "- npm run dev-full         # Start both frontend and backend"
echo "- npm run check-backend    # Check if backend is running"
