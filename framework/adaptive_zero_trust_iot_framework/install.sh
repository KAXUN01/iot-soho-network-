#!/bin/bash
# Installation script for Adaptive Zero Trust IoT Framework

echo "Installing Adaptive Zero Trust IoT Framework..."
echo "=============================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install flask sqlite3 cryptography threading signal json uuid datetime
pip3 install ryu docker scapy

# Install system dependencies  
echo "🔧 Installing system dependencies..."
sudo apt-get install -y hostapd dnsmasq iptables-persistent

# Install Docker (if not already installed)
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    sudo systemctl enable docker
    sudo systemctl start docker
    rm get-docker.sh
else
    echo "✓ Docker already installed"
fi

# Create required directories
echo "📁 Creating directories..."
mkdir -p data
mkdir -p logs
mkdir -p honeypot_logs
mkdir -p certificates

# Set proper permissions
chmod 755 data logs honeypot_logs certificates
chmod +x scripts/*.sh

echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. Configure your WiFi interface in config/config.py"
echo "2. Run: python3 main.py"
echo "3. Monitor logs in the logs/ directory"
