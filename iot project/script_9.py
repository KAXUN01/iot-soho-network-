# Create installation and setup scripts
install_script = '''#!/bin/bash
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
'''

with open(f"{project_name}/install.sh", "w") as f:
    f.write(install_script)

# Create requirements.txt
requirements = '''flask==2.3.3
cryptography==41.0.4
ryu==4.34
docker==6.1.3
scapy==2.5.0
sqlite3
'''

with open(f"{project_name}/requirements.txt", "w") as f:
    f.write(requirements)

# Create Docker Compose for honeypots
docker_compose = '''version: '3.8'
services:
  cowrie-honeypot:
    image: cowrie/cowrie:latest
    container_name: iot-cowrie-honeypot
    ports:
      - "2222:2222"
      - "2223:2223"
    volumes:
      - "./honeypot_logs:/cowrie/var/log/cowrie"
    environment:
      - COWRIE_HOSTNAME=iot-device
      - COWRIE_LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - honeypot-network

  dionaea-honeypot:
    image: dinotools/dionaea:latest
    container_name: iot-dionaea-honeypot
    ports:
      - "21:21"
      - "8080:80"
      - "8443:443"
      - "135:135"
      - "445:445"
    volumes:
      - "./honeypot_logs:/opt/dionaea/var/log"
    restart: unless-stopped
    networks:
      - honeypot-network

networks:
  honeypot-network:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.40.0/24
'''

with open(f"{project_name}/docker-compose.yml", "w") as f:
    f.write(docker_compose)

print("Created installation files:")
print("  install.sh")
print("  requirements.txt") 
print("  docker-compose.yml")