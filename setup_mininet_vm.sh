#!/bin/bash
# Setup script for Mininet VM (Network Emulation)
# Run this on the VM that will run Mininet to connect to the Ryu controller

set -e

echo "🌐 Setting up Mininet VM for IoT Network Emulation"
echo "=================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3 and development tools
echo "🐍 Installing Python 3 and development tools..."
sudo apt-get install -y python3 python3-pip python3-venv python3-dev
sudo apt-get install -y git curl wget

# Install Mininet and dependencies
echo "🌐 Installing Mininet and OpenVSwitch..."
sudo apt-get install -y mininet openvswitch-switch openvswitch-common
sudo apt-get install -y iperf3 wireshark tcpdump

# Install additional network tools
echo "🔧 Installing network tools..."
sudo apt-get install -y net-tools iputils-ping traceroute
sudo apt-get install -y nmap netcat-openbsd



# Create test scripts directory
mkdir -p mininet_tests
cd mininet_tests

# Create Mininet test script
echo "📝 Creating Mininet test scripts..."
cat > test_iot_network.py << 'EOF'
#!/usr/bin/env python3
"""
Mininet test script for IoT Zero Trust Framework
Connects to remote Ryu controller and creates IoT device topology
"""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
import sys

def create_iot_network(controller_ip, controller_port=6653):
    """Create IoT network topology with remote controller"""
    
    print(f"🌐 Creating IoT network with controller at {controller_ip}:{controller_port}")
    
    # Create network with remote controller
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        autoSetMacs=True,
        autoStaticArp=True
    )
    
    # Add remote controller
    controller = net.addController(
        'ryu',
        controller=RemoteController,
        ip=controller_ip,
        port=controller_port,
        protocols='OpenFlow13'
    )
    
    # Create IoT devices (hosts)
    print("📱 Adding IoT devices...")
    
    # Smart home devices
    smart_thermostat = net.addHost('thermostat', ip='192.168.10.10/24', mac='00:00:00:00:00:01')
    smart_camera = net.addHost('camera', ip='192.168.10.11/24', mac='00:00:00:00:00:02')
    smart_doorbell = net.addHost('doorbell', ip='192.168.10.12/24', mac='00:00:00:00:00:03')
    smart_speaker = net.addHost('speaker', ip='192.168.10.13/24', mac='00:00:00:00:00:04')
    
    # Potentially compromised devices
    old_router = net.addHost('old_router', ip='192.168.10.20/24', mac='00:00:00:00:00:05')
    iot_sensor = net.addHost('sensor', ip='192.168.10.21/24', mac='00:00:00:00:00:06')
    
    # Gateway/Internet
    gateway = net.addHost('gateway', ip='192.168.10.1/24', mac='00:00:00:00:00:07')
    
    # Create switch
    print("🔌 Adding OpenFlow switch...")
    switch = net.addSwitch('s1', protocols='OpenFlow13')
    
    # Connect devices to switch
    print("🔗 Connecting devices...")
    net.addLink(thermostat, switch)
    net.addLink(camera, switch)
    net.addLink(doorbell, switch)
    net.addLink(speaker, switch)
    net.addLink(old_router, switch)
    net.addLink(sensor, switch)
    net.addLink(gateway, switch)
    
    return net

def test_connectivity(net):
    """Test basic connectivity between devices"""
    print("🧪 Testing network connectivity...")
    
    # Test ping between devices
    print("📡 Testing ping connectivity...")
    net.pingAll()
    
    # Test specific IoT device communication
    print("🏠 Testing IoT device communication...")
    thermostat = net.get('thermostat')
    camera = net.get('camera')
    gateway = net.get('gateway')
    
    # Test thermostat to camera communication
    result = thermostat.cmd('ping -c 3 192.168.10.11')
    print(f"Thermostat -> Camera: {'✅ Success' if '0% packet loss' in result else '❌ Failed'}")
    
    # Test camera to gateway communication
    result = camera.cmd('ping -c 3 192.168.10.1')
    print(f"Camera -> Gateway: {'✅ Success' if '0% packet loss' in result else '❌ Failed'}")

def simulate_iot_traffic(net):
    """Simulate typical IoT device traffic patterns"""
    print("📊 Simulating IoT traffic patterns...")
    
    thermostat = net.get('thermostat')
    camera = net.get('camera')
    gateway = net.get('gateway')
    
    # Simulate thermostat sending temperature data
    print("🌡️  Simulating thermostat data transmission...")
    thermostat.cmd('echo "Temperature: 22.5°C" | nc -l 8080 &')
    
    # Simulate camera streaming
    print("📹 Simulating camera streaming...")
    camera.cmd('echo "Video stream data" | nc -l 8081 &')
    
    # Simulate suspicious activity (for testing trust scoring)
    print("⚠️  Simulating suspicious network activity...")
    old_router = net.get('old_router')
    old_router.cmd('nmap -sn 192.168.10.0/24 &')  # Network scan
    old_router.cmd('nc -l 4444 &')  # Listen on suspicious port

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 test_iot_network.py <controller_ip> [controller_port]")
        print("Example: python3 test_iot_network.py 192.168.1.100 6653")
        sys.exit(1)
    
    controller_ip = sys.argv[1]
    controller_port = int(sys.argv[2]) if len(sys.argv) > 2 else 6653
    
    setLogLevel('info')
    
    # Create network
    net = create_iot_network(controller_ip, controller_port)
    
    # Start network
    print("🚀 Starting network...")
    net.start()
    
    # Wait for controller connection
    print("⏳ Waiting for controller connection...")
    import time
    time.sleep(5)
    
    # Test connectivity
    test_connectivity(net)
    
    # Simulate traffic
    simulate_iot_traffic(net)
    
    print("\n🎯 Network is ready!")
    print("📋 Available commands in Mininet CLI:")
    print("  - pingall: Test all connectivity")
    print("  - h1 ping h2: Test specific host communication")
    print("  - h1 ifconfig: Show host network configuration")
    print("  - net: Show network topology")
    print("  - dump: Show network information")
    print("  - exit: Stop network and exit")
    print("\n🔍 Monitor the Ryu controller logs to see trust scoring in action!")
    
    # Start CLI
    CLI(net)
    
    # Cleanup
    print("🧹 Stopping network...")
    net.stop()

if __name__ == '__main__':
    main()
EOF

chmod +x test_iot_network.py

# Create simple connection test script
cat > test_controller_connection.py << 'EOF'
#!/usr/bin/env python3
"""
Simple script to test connection to Ryu controller
"""

import socket
import sys

def test_controller_connection(ip, port=6653):
    """Test if controller is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Controller at {ip}:{port} is reachable")
            return True
        else:
            print(f"❌ Controller at {ip}:{port} is not reachable")
            return False
    except Exception as e:
        print(f"❌ Error connecting to controller: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 test_controller_connection.py <controller_ip> [port]")
        sys.exit(1)
    
    controller_ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 6653
    
    test_controller_connection(controller_ip, port)
EOF

chmod +x test_controller_connection.py

# Create startup script
cat > start_mininet.sh << 'EOF'
#!/bin/bash
# Mininet startup script

CONTROLLER_IP="$1"
CONTROLLER_PORT="${2:-6653}"

if [ -z "$CONTROLLER_IP" ]; then
    echo "Usage: ./start_mininet.sh <controller_ip> [controller_port]"
    echo "Example: ./start_mininet.sh 192.168.1.100 6653"
    exit 1
fi

echo "🌐 Starting Mininet with controller at $CONTROLLER_IP:$CONTROLLER_PORT"

# Test controller connection first
echo "🔍 Testing controller connection..."
python3 test_controller_connection.py "$CONTROLLER_IP" "$CONTROLLER_PORT"

if [ $? -eq 0 ]; then
    echo "🚀 Starting IoT network simulation..."
    sudo python3 test_iot_network.py "$CONTROLLER_IP" "$CONTROLLER_PORT"
else
    echo "❌ Cannot connect to controller. Please check:"
    echo "   1. Controller IP is correct"
    echo "   2. Controller is running"
    echo "   3. Firewall allows port $CONTROLLER_PORT"
    echo "   4. Network connectivity between VMs"
fi
EOF

chmod +x start_mininet.sh

# Create quick test script
cat > quick_test.sh << 'EOF'
#!/bin/bash
# Quick connectivity test

CONTROLLER_IP="$1"

if [ -z "$CONTROLLER_IP" ]; then
    echo "Usage: ./quick_test.sh <controller_ip>"
    exit 1
fi

echo "🧪 Quick connectivity test..."
echo "Controller IP: $CONTROLLER_IP"

# Test basic connectivity
echo "📡 Testing basic connectivity..."
ping -c 3 "$CONTROLLER_IP" && echo "✅ Ping successful" || echo "❌ Ping failed"

# Test controller port
echo "🔌 Testing controller port..."
python3 test_controller_connection.py "$CONTROLLER_IP" 6653

# Test with simple Mininet
echo "🌐 Testing with simple Mininet topology..."
sudo mn --topo single,3 --mac --controller=remote,ip="$CONTROLLER_IP",port=6653 --switch ovsk,protocols=OpenFlow13 --test pingall
EOF

chmod +x quick_test.sh

echo ""
echo "✅ Mininet VM setup complete!"
echo "=============================================================="
echo "📋 Next steps:"
echo "1. Note your VM IP: $(hostname -I | awk '{print $1}')"
echo "2. Get the Ryu VM IP from the controller setup"
echo "3. Test connection: ./quick_test.sh <ryu_vm_ip>"
echo "4. Start full simulation: ./start_mininet.sh <ryu_vm_ip>"
echo ""
echo "🧪 Available test scripts:"
echo "   - quick_test.sh <controller_ip>: Basic connectivity test"
echo "   - start_mininet.sh <controller_ip>: Full IoT simulation"
echo "   - test_controller_connection.py <controller_ip>: Port test"
echo ""
echo "🌐 Example usage:"
echo "   ./quick_test.sh 192.168.1.100"
echo "   ./start_mininet.sh 192.168.1.100 6653"
echo "=============================================================="
