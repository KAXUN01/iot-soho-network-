#!/bin/bash
# Setup script for Ryu VM (Controller + Framework) - Fixed for older Ubuntu
# Run this on the VM that will host the framework and Ryu controller

set -e

echo "🛡️  Setting up Ryu VM for Adaptive Zero Trust IoT Framework"
echo "=============================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3 and development tools (compatible with older Ubuntu)
echo "🐍 Installing Python 3 and development tools..."
sudo apt-get install -y python3 python3-pip python3-dev
sudo apt-get install -y git curl wget

# Try to install python3-venv, fallback if not available
echo "🔧 Installing Python virtual environment support..."
sudo apt-get install -y python3-venv || echo "⚠️  python3-venv not available, will use alternative method"
sudo apt-get install -y python3-distutils || echo "⚠️  python3-distutils not available, will use alternative method"

# Install system dependencies for the framework
echo "🔧 Installing system dependencies..."
sudo apt-get install -y sqlite3 openssl ca-certificates
sudo apt-get install -y build-essential libssl-dev libffi-dev

# Install Docker (for honeypots) - try different methods based on Ubuntu version
echo "🐳 Installing Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker already installed"
else
    # Try modern Docker installation first
    if curl -fsSL https://download.docker.com/linux/ubuntu/gpg 2>/dev/null | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null; then
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    else
        # Fallback to system Docker package
        echo "📦 Installing Docker from system packages..."
        sudo apt-get install -y docker.io
    fi
    sudo usermod -aG docker $USER
fi

# Install Ryu and dependencies - try system packages first
echo "🌐 Installing Ryu and network dependencies..."
sudo apt-get install -y python3-flask python3-cryptography || echo "⚠️  Some system packages not available, will use pip"

# Try to install Ryu from system packages
if ! command -v ryu-manager &> /dev/null; then
    echo "📦 Installing Ryu from system packages..."
    sudo apt-get install -y python3-ryu || echo "⚠️  System Ryu not available, will install via pip"
fi

# Install additional network tools
sudo apt-get install -y python3-scapy python3-requests || echo "⚠️  Some packages not available, will use pip"

# Clone the project (if not already cloned)
if [ ! -d "iot-soho-network-" ]; then
    echo "📥 Cloning project repository..."
    git clone https://github.com/KAXUN01/iot-soho-network-.git
    cd iot-soho-network-
else
    echo "📁 Project already exists, updating..."
    cd iot-soho-network-
    git pull origin main
fi

# Navigate to framework directory
cd "iot project/adaptive_zero_trust_iot_framework"

# Create virtual environment (with fallback for older Python)
echo "🔧 Setting up Python virtual environment..."
if python3 -m venv .venv 2>/dev/null; then
    echo "✅ Virtual environment created successfully"
else
    echo "⚠️  venv not available, using virtualenv..."
    # Try virtualenv as fallback
    sudo apt-get install -y python3-virtualenv || pip3 install virtualenv
    python3 -m virtualenv .venv
fi

source .venv/bin/activate

# Install project dependencies with compatibility fixes
echo "📦 Installing project dependencies..."
pip install --upgrade pip wheel

# Try to install setuptools with compatible version
pip install "setuptools==65.5.1" || pip install "setuptools<60" || pip install setuptools

# Install core dependencies
pip install flask==2.3.3 cryptography==41.0.4 docker==6.1.3

# Try to install Ryu via pip (fallback if system package fails)
echo "🌐 Installing Ryu via pip..."
if ! command -v ryu-manager &> /dev/null; then
    pip install ryu==4.34 || {
        echo "⚠️  Ryu installation via pip failed, trying alternative..."
        pip install ryu || echo "❌ Ryu installation failed completely"
    }
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs honeypot_logs certificates data

# Set up SSH key for GitHub (if not exists)
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "🔑 Setting up SSH key for GitHub..."
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    ssh-keygen -t ed25519 -C "ryu-vm@local" -f ~/.ssh/id_ed25519 -N ""
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519
    ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
    chmod 644 ~/.ssh/known_hosts
    echo "📋 Add this SSH key to your GitHub account:"
    echo "---"
    cat ~/.ssh/id_ed25519.pub
    echo "---"
    echo "GitHub → Settings → SSH and GPG keys → New SSH key"
fi

# Configure git remote to SSH
echo "🔗 Configuring Git remote..."
git remote set-url origin git@github.com:KAXUN01/iot-soho-network-.git

# Create startup script with error handling
echo "📝 Creating startup script..."
cat > start_framework.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/iot project/adaptive_zero_trust_iot_framework"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup again."
    exit 1
fi

source .venv/bin/activate

echo "🚀 Starting Adaptive Zero Trust IoT Framework..."
echo "📡 Framework will be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo "🔑 Onboarding key: PiSecret123"
echo ""

# Check if required commands exist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

if ! command -v ryu-manager &> /dev/null; then
    echo "⚠️  ryu-manager not found, trying to run from Python path..."
    PYTHONPATH="$(pwd)" python3 -m ryu.manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
    RYU_PID=$!
else
    echo "🌐 Starting Ryu SDN Controller..."
    PYTHONPATH="$(pwd)" ryu-manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
    RYU_PID=$!
fi

# Start the framework in background
python3 main.py &
FRAMEWORK_PID=$!

# Wait a moment for framework to start
sleep 5

echo "✅ Framework PID: $FRAMEWORK_PID"
echo "✅ Ryu Controller PID: $RYU_PID"
echo "✅ OpenFlow listening on port 6653"
echo ""
echo "To stop: kill $FRAMEWORK_PID $RYU_PID"
echo "Or run: pkill -f 'python.*main.py' && pkill -f 'ryu'"

# Keep script running
wait
EOF

chmod +x start_framework.sh

# Create a simple test script
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify setup
"""

import sys
import os

def test_imports():
    """Test if required modules can be imported"""
    try:
        import flask
        print("✅ Flask available")
    except ImportError:
        print("❌ Flask not available")
        return False
    
    try:
        import cryptography
        print("✅ Cryptography available")
    except ImportError:
        print("❌ Cryptography not available")
        return False
    
    try:
        import docker
        print("✅ Docker available")
    except ImportError:
        print("❌ Docker not available")
        return False
    
    try:
        import ryu
        print("✅ Ryu available")
    except ImportError:
        print("❌ Ryu not available")
        return False
    
    return True

def test_database():
    """Test database creation"""
    try:
        from src.database.db_manager import create_database
        from config.config import DATABASE_PATH
        create_database(DATABASE_PATH)
        print("✅ Database creation successful")
        return True
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Testing setup...")
    
    if test_imports() and test_database():
        print("✅ Setup test passed!")
    else:
        print("❌ Setup test failed!")
        sys.exit(1)
EOF

chmod +x test_setup.py

echo ""
echo "✅ Ryu VM setup complete!"
echo "=============================================================="
echo "📋 Next steps:"
echo "1. Add the SSH key to your GitHub account (if not done already)"
echo "2. Note your VM IP: $(hostname -I | awk '{print $1}')"
echo "3. Test setup: python3 test_setup.py"
echo "4. Start the framework: ./start_framework.sh"
echo ""
echo "🔧 Framework endpoints:"
echo "   Health: http://$(hostname -I | awk '{print $1}'):5000/health"
echo "   Status: http://$(hostname -I | awk '{print $1}'):5000/status"
echo "   Onboard: http://$(hostname -I | awk '{print $1}'):5000/onboard"
echo ""
echo "🌐 OpenFlow controller: $(hostname -I | awk '{print $1}'):6653"
echo "=============================================================="
