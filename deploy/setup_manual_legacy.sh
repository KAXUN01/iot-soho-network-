#!/bin/bash
# Manual setup for very old Ubuntu - step by step
# This script will guide you through manual installation

echo "🛡️  Manual Setup for Legacy Ubuntu"
echo "=================================="

# Check what we have
echo "🔍 Checking system..."
echo "Python version: $(python3 --version)"
echo "Pip available: $(command -v pip3 || echo 'Not found')"
echo "Git available: $(command -v git || echo 'Not found')"

# Install basic packages
echo "📦 Installing basic packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-dev git curl wget sqlite3 openssl
sudo apt-get install -y build-essential libssl-dev libffi-dev

# Install pip manually
echo "🔧 Installing pip manually..."
if ! command -v pip3 &> /dev/null; then
    echo "📥 Downloading get-pip.py..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Docker
echo "🐳 Installing Docker..."
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER

# Clone project (fix directory name issue)
echo "📥 Cloning project..."
if [ -d "iot-soho-network-" ]; then
    echo "📁 Project already exists, updating..."
    cd iot-soho-network-
    git pull origin main
else
    git clone https://github.com/KAXUN01/iot-soho-network-.git
    cd iot-soho-network-
fi

# Navigate to framework
cd "iot project/adaptive_zero_trust_iot_framework"

# Create directories
echo "📁 Creating directories..."
mkdir -p logs honeypot_logs certificates data

# Install Python packages manually
echo "📦 Installing Python packages..."
export PATH="$HOME/.local/bin:$PATH"

# Install packages one by one with error handling
echo "Installing Flask..."
pip3 install --user flask==2.3.3 || echo "⚠️  Flask installation failed"

echo "Installing Cryptography..."
pip3 install --user cryptography==41.0.4 || echo "⚠️  Cryptography installation failed"

echo "Installing Docker..."
pip3 install --user docker==6.1.3 || echo "⚠️  Docker installation failed"

echo "Installing Ryu..."
pip3 install --user ryu==4.34 || pip3 install --user ryu || echo "⚠️  Ryu installation failed"

# Set up SSH key
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "🔑 Setting up SSH key..."
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
fi

# Configure git
git remote set-url origin git@github.com:KAXUN01/iot-soho-network-.git

# Create simple startup script
echo "📝 Creating startup script..."
cat > start_simple.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/iot project/adaptive_zero_trust_iot_framework"

# Add user pip to PATH
export PATH="$HOME/.local/bin:$PATH"

echo "🚀 Starting Framework..."
echo "📡 Framework: http://$(hostname -I | awk '{print $1}'):5000"
echo "🔑 Onboarding key: PiSecret123"
echo ""

# Start framework
python3 main.py &
FRAMEWORK_PID=$!

# Wait a bit
sleep 3

# Start Ryu
echo "🌐 Starting Ryu Controller..."
if command -v ryu-manager &> /dev/null; then
    PYTHONPATH="$(pwd)" ryu-manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
else
    PYTHONPATH="$(pwd)" python3 -m ryu.manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
fi
RYU_PID=$!

echo "✅ Framework PID: $FRAMEWORK_PID"
echo "✅ Ryu PID: $RYU_PID"
echo "✅ OpenFlow: $(hostname -I | awk '{print $1}'):6653"

wait
EOF

chmod +x start_simple.sh

# Create test script
cat > test_manual.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add user packages to path
sys.path.insert(0, os.path.expanduser('~/.local/lib/python3.*/site-packages'))

def test_imports():
    try:
        import flask
        print("✅ Flask OK")
    except ImportError as e:
        print(f"❌ Flask: {e}")
        return False
    
    try:
        import cryptography
        print("✅ Cryptography OK")
    except ImportError as e:
        print(f"❌ Cryptography: {e}")
        return False
    
    try:
        import docker
        print("✅ Docker OK")
    except ImportError as e:
        print(f"❌ Docker: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🧪 Testing manual setup...")
    if test_imports():
        print("✅ Manual setup test passed!")
    else:
        print("❌ Manual setup test failed!")
        sys.exit(1)
EOF

chmod +x test_manual.py

echo ""
echo "✅ Manual setup complete!"
echo "=============================================================="
echo "📋 Next steps:"
echo "1. Add SSH key to GitHub (if not done)"
echo "2. Test: python3 test_manual.py"
echo "3. Start: ./start_simple.sh"
echo ""
echo "🔧 Endpoints:"
echo "   Health: http://$(hostname -I | awk '{print $1}'):5000/health"
echo "   Status: http://$(hostname -I | awk '{print $1}'):5000/status"
echo "   OpenFlow: $(hostname -I | awk '{print $1}'):6653"
echo "=============================================================="
