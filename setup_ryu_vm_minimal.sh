#!/bin/bash
# Minimal setup script for Ryu VM - No system upgrades
# Works with existing Ubuntu version without modifications

set -e

echo "🛡️  Minimal Ryu VM Setup (No System Upgrades)"
echo "==============================================="

# Install only essential packages (no upgrades)
echo "📦 Installing essential packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dev
sudo apt-get install -y git curl wget sqlite3 openssl
sudo apt-get install -y build-essential libssl-dev libffi-dev

# Install virtualenv for Python virtual environment
echo "🔧 Installing virtualenv..."
sudo apt-get install -y python3-virtualenv || pip3 install virtualenv

# Install Docker (system package only)
echo "🐳 Installing Docker..."
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER

# Install Ryu and dependencies from system packages
echo "🌐 Installing Ryu and dependencies..."
sudo apt-get install -y python3-flask python3-cryptography python3-docker
sudo apt-get install -y python3-ryu || echo "⚠️  System Ryu not available, will install via pip"

# Clone the project
if [ ! -d "iot-soho-network" ]; then
    echo "📥 Cloning project repository..."
    git clone https://github.com/KAXUN01/iot-soho-network-.git
    cd iot-soho-network
else
    echo "📁 Project already exists, updating..."
    cd iot-soho-network
    git pull origin main
fi

# Navigate to framework directory
cd "iot project/adaptive_zero_trust_iot_framework"

# Create virtual environment using virtualenv
echo "🔧 Creating Python virtual environment..."
python3 -m virtualenv .venv
source .venv/bin/activate

# Install minimal dependencies
echo "📦 Installing minimal dependencies..."
pip install --upgrade pip
pip install flask==2.3.3 cryptography==41.0.4 docker==6.1.3

# Try to install Ryu via pip if system package failed
if ! command -v ryu-manager &> /dev/null; then
    echo "🌐 Installing Ryu via pip..."
    pip install ryu==4.34 || pip install ryu
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs honeypot_logs certificates data

# Set up SSH key for GitHub
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

# Create simple startup script
echo "📝 Creating startup script..."
cat > start_framework.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/iot project/adaptive_zero_trust_iot_framework"

# Activate virtual environment
source .venv/bin/activate

echo "🚀 Starting Adaptive Zero Trust IoT Framework..."
echo "📡 Framework: http://$(hostname -I | awk '{print $1}'):5000"
echo "🔑 Onboarding key: PiSecret123"
echo ""

# Start framework
python3 main.py &
FRAMEWORK_PID=$!

# Wait for framework to start
sleep 3

# Start Ryu controller
echo "🌐 Starting Ryu SDN Controller..."
if command -v ryu-manager &> /dev/null; then
    PYTHONPATH="$(pwd)" ryu-manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
else
    PYTHONPATH="$(pwd)" python3 -m ryu.manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
fi
RYU_PID=$!

echo "✅ Framework PID: $FRAMEWORK_PID"
echo "✅ Ryu Controller PID: $RYU_PID"
echo "✅ OpenFlow port: 6653"
echo ""
echo "To stop: kill $FRAMEWORK_PID $RYU_PID"

# Keep running
wait
EOF

chmod +x start_framework.sh

# Create simple test script
cat > test_simple.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

def test_basic():
    try:
        import flask
        print("✅ Flask OK")
    except:
        print("❌ Flask missing")
        return False
    
    try:
        import cryptography
        print("✅ Cryptography OK")
    except:
        print("❌ Cryptography missing")
        return False
    
    try:
        import docker
        print("✅ Docker OK")
    except:
        print("❌ Docker missing")
        return False
    
    return True

if __name__ == '__main__':
    if test_basic():
        print("✅ Basic test passed!")
    else:
        print("❌ Basic test failed!")
        sys.exit(1)
EOF

chmod +x test_simple.py

echo ""
echo "✅ Minimal setup complete!"
echo "=============================================================="
echo "📋 Next steps:"
echo "1. Add SSH key to GitHub (if not done)"
echo "2. Test: python3 test_simple.py"
echo "3. Start: ./start_framework.sh"
echo ""
echo "🔧 Endpoints:"
echo "   Health: http://$(hostname -I | awk '{print $1}'):5000/health"
echo "   Status: http://$(hostname -I | awk '{print $1}'):5000/status"
echo "   OpenFlow: $(hostname -I | awk '{print $1}'):6653"
echo "=============================================================="
