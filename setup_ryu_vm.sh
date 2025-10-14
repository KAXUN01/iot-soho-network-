#!/bin/bash
# Setup script for Ryu VM (Controller + Framework)
# Run this on the VM that will host the framework and Ryu controller

set -e

echo "🛡️  Setting up Ryu VM for Adaptive Zero Trust IoT Framework"
echo "=============================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3 and development tools
echo "🐍 Installing Python 3 and development tools..."
sudo apt-get install -y python3 python3-pip python3-venv python3-dev python3-distutils
sudo apt-get install -y git curl wget

# Install system dependencies for the framework
echo "🔧 Installing system dependencies..."
sudo apt-get install -y sqlite3 openssl ca-certificates
sudo apt-get install -y build-essential libssl-dev libffi-dev

# Install Docker (for honeypots)
echo "🐳 Installing Docker..."
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker $USER

# Install Ryu and dependencies
echo "🌐 Installing Ryu and network dependencies..."
sudo apt-get install -y python3-ryu python3-flask python3-cryptography python3-docker
sudo apt-get install -y python3-scapy python3-requests

# If system packages don't work, use pip with specific versions
echo "📚 Installing Python packages via pip..."
python3 -m pip install --upgrade pip wheel "setuptools==65.5.1"
python3 -m pip install flask==2.3.3 cryptography==41.0.4 docker==6.1.3

# Clone the project (if not already cloned)
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

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install project dependencies
echo "📦 Installing project dependencies..."
pip install --upgrade pip wheel "setuptools==65.5.1"
pip install flask==2.3.3 cryptography==41.0.4 docker==6.1.3

# Try to install Ryu via pip (fallback if system package fails)
pip install ryu==4.34 || echo "⚠️  Ryu installation via pip failed, using system package"

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

# Create startup script
echo "📝 Creating startup script..."
cat > start_framework.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/iot project/adaptive_zero_trust_iot_framework"
source .venv/bin/activate

echo "🚀 Starting Adaptive Zero Trust IoT Framework..."
echo "📡 Framework will be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo "🔑 Onboarding key: PiSecret123"
echo ""

# Start the framework in background
python3 main.py &
FRAMEWORK_PID=$!

# Wait a moment for framework to start
sleep 5

# Start Ryu controller
echo "🌐 Starting Ryu SDN Controller..."
PYTHONPATH="$(pwd)" ryu-manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
RYU_PID=$!

echo "✅ Framework PID: $FRAMEWORK_PID"
echo "✅ Ryu Controller PID: $RYU_PID"
echo "✅ OpenFlow listening on port 6653"
echo ""
echo "To stop: kill $FRAMEWORK_PID $RYU_PID"
echo "Or run: pkill -f 'python.*main.py' && pkill -f 'ryu-manager'"

# Keep script running
wait
EOF

chmod +x start_framework.sh

# Create systemd service (optional)
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/iot-framework.service > /dev/null << EOF
[Unit]
Description=Adaptive Zero Trust IoT Framework
After=network.target docker.service

[Service]
Type=forking
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start_framework.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service (optional - comment out if you prefer manual startup)
# sudo systemctl enable iot-framework.service

echo ""
echo "✅ Ryu VM setup complete!"
echo "=============================================================="
echo "📋 Next steps:"
echo "1. Add the SSH key to your GitHub account (if not done already)"
echo "2. Note your VM IP: $(hostname -I | awk '{print $1}')"
echo "3. Start the framework: ./start_framework.sh"
echo "4. Or start manually:"
echo "   cd 'iot project/adaptive_zero_trust_iot_framework'"
echo "   source .venv/bin/activate"
echo "   python3 main.py &"
echo "   PYTHONPATH=\$(pwd) ryu-manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &"
echo ""
echo "🔧 Framework endpoints:"
echo "   Health: http://$(hostname -I | awk '{print $1}'):5000/health"
echo "   Status: http://$(hostname -I | awk '{print $1}'):5000/status"
echo "   Onboard: http://$(hostname -I | awk '{print $1}'):5000/onboard"
echo ""
echo "🌐 OpenFlow controller: $(hostname -I | awk '{print $1}'):6653"
echo "=============================================================="
