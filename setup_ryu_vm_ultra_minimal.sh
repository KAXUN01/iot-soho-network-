#!/bin/bash
# Ultra-minimal setup for very old Ubuntu versions
# No virtualenv, no pip3, uses only system packages

set -e

echo "🛡️  Ultra-Minimal Ryu VM Setup (Legacy Ubuntu)"
echo "=============================================="

# Install only what's absolutely available
echo "📦 Installing basic packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-dev
sudo apt-get install -y git curl wget sqlite3 openssl
sudo apt-get install -y build-essential libssl-dev libffi-dev

# Try to install pip using get-pip.py
echo "🔧 Installing pip manually..."
if ! command -v pip3 &> /dev/null; then
    echo "📥 Downloading get-pip.py..."
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python3 get-pip.py --user
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Install Docker (system package)
echo "🐳 Installing Docker..."
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER

# Install system packages for dependencies
echo "🌐 Installing system packages..."
sudo apt-get install -y python3-flask python3-cryptography python3-docker || echo "⚠️  Some packages not available"
sudo apt-get install -y python3-ryu || echo "⚠️  System Ryu not available"

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

# Create directories
echo "📁 Creating project directories..."
mkdir -p logs honeypot_logs certificates data

# Install Python packages using pip (user install)
echo "📦 Installing Python packages..."
export PATH="$HOME/.local/bin:$PATH"
pip3 install --user flask==2.3.3 cryptography==41.0.4 docker==6.1.3

# Try to install Ryu
if ! command -v ryu-manager &> /dev/null; then
    echo "🌐 Installing Ryu via pip..."
    pip3 install --user ryu==4.34 || pip3 install --user ryu || echo "⚠️  Ryu installation failed"
fi

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

# Create startup script (no virtual environment)
echo "📝 Creating startup script..."
cat > start_framework.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/iot project/adaptive_zero_trust_iot_framework"

# Add user pip to PATH
export PATH="$HOME/.local/bin:$PATH"

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
cat > test_basic.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add user pip to PATH
sys.path.insert(0, os.path.expanduser('~/.local/lib/python3.*/site-packages'))

def test_imports():
    try:
        import flask
        print("✅ Flask available")
    except ImportError as e:
        print(f"❌ Flask error: {e}")
        return False
    
    try:
        import cryptography
        print("✅ Cryptography available")
    except ImportError as e:
        print(f"❌ Cryptography error: {e}")
        return False
    
    try:
        import docker
        print("✅ Docker available")
    except ImportError as e:
        print(f"❌ Docker error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🧪 Testing basic imports...")
    if test_imports():
        print("✅ Basic test passed!")
    else:
        print("❌ Basic test failed!")
        sys.exit(1)
EOF

chmod +x test_basic.py

# Create manual installation guide
cat > MANUAL_SETUP.md << 'EOF'
# Manual Setup Guide for Legacy Ubuntu

If the automated setup fails, follow these manual steps:

## 1. Install Python packages manually:
```bash
# Install pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --user
export PATH="$HOME/.local/bin:$PATH"

# Install packages
pip3 install --user flask==2.3.3
pip3 install --user cryptography==41.0.4
pip3 install --user docker==6.1.3
pip3 install --user ryu==4.34
```

## 2. Install system dependencies:
```bash
sudo apt-get install -y python3-flask python3-cryptography python3-docker python3-ryu
```

## 3. Start the framework:
```bash
cd "iot project/adaptive_zero_trust_iot_framework"
export PATH="$HOME/.local/bin:$PATH"
python3 main.py &
PYTHONPATH="$(pwd)" ryu-manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
```

## 4. Test endpoints:
- Health: http://$(hostname -I):5000/health
- Status: http://$(hostname -I):5000/status
EOF

echo ""
echo "✅ Ultra-minimal setup complete!"
echo "=============================================================="
echo "📋 Next steps:"
echo "1. Add SSH key to GitHub (if not done)"
echo "2. Test: python3 test_basic.py"
echo "3. Start: ./start_framework.sh"
echo ""
echo "🔧 Endpoints:"
echo "   Health: http://$(hostname -I | awk '{print $1}'):5000/health"
echo "   Status: http://$(hostname -I | awk '{print $1}'):5000/status"
echo "   OpenFlow: $(hostname -I | awk '{print $1}'):6653"
echo ""
echo "📖 If setup fails, see MANUAL_SETUP.md for manual steps"
echo "=============================================================="
