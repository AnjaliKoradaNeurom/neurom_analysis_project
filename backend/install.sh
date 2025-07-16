#!/bin/bash

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y wget gnupg unzip curl python3-pip

# Install Node.js and Lighthouse
echo "Installing Node.js and Lighthouse..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g lighthouse

# Install Chrome for Lighthouse
echo "Installing Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Redis (optional)
echo "Installing Redis..."
sudo apt-get install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

echo "Installation complete!"
echo "To start the API server, run: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
