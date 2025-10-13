#!/usr/bin/env python3
"""
IoT Device Simulator for Testing the Adaptive Zero Trust Framework
Simulates various IoT device behaviors for framework validation
"""
import requests
import json
import time
import random
import socket
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class IoTDeviceSimulator:
    def __init__(self, device_type="SmartSensor", framework_ip="192.168.50.1"):
        self.device_type = device_type
        self.framework_ip = framework_ip
        self.onboarding_url = f"http://{framework_ip}:5000/onboard"

        # Generate device identity
        self.device_id = f"{device_type}-{random.randint(1000, 9999)}"
        self.mac_address = self._generate_mac()

        # Cryptographic materials
        self.private_key = None
        self.certificate = None
        self.ca_certificate = None

        print(f"🤖 IoT Device Simulator: {self.device_id}")
        print(f"   Type: {device_type}")
        print(f"   MAC: {self.mac_address}")
        print(f"   Framework: {framework_ip}")

    def _generate_mac(self):
        """Generate a realistic MAC address"""
        return "02:%02x:%02x:%02x:%02x:%02x" % (
            random.randint(0, 255), random.randint(0, 255),
            random.randint(0, 255), random.randint(0, 255),
            random.randint(0, 255)
        )

    def generate_keypair(self):
        """Generate RSA key pair for device"""
        print("🔑 Generating RSA key pair...")

        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        public_key_pem = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        return public_key_pem

    def onboard_device(self):
        """Attempt to onboard device with the framework"""
        print("📡 Starting device onboarding...")

        # Generate key pair
        public_key_pem = self.generate_keypair()

        # Prepare onboarding request
        onboard_request = {
            "mac_address": self.mac_address,
            "public_key_pem": public_key_pem,
            "onboard_key": "PiSecret123",  # Default onboarding key
            "device_info": {
                "type": self.device_type,
                "version": "1.0.0",
                "manufacturer": "SimulatedIoT Corp",
                "model": f"{self.device_type}-v1"
            }
        }

        try:
            response = requests.post(
                self.onboarding_url,
                json=onboard_request,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    self.device_id = result['device_id']
                    self.certificate = result['device_certificate']
                    self.ca_certificate = result['ca_certificate']

                    print(f"✅ Onboarding successful!")
                    print(f"   Device ID: {self.device_id}")
                    print(f"   Certificate issued: {len(self.certificate)} bytes")
                    return True
                else:
                    print(f"❌ Onboarding failed: {result['error']}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False

    def simulate_normal_behavior(self, duration_minutes=20):
        """Simulate normal IoT device behavior"""
        print(f"🟢 Simulating normal behavior for {duration_minutes} minutes...")

        end_time = time.time() + (duration_minutes * 60)

        while time.time() < end_time:
            # Simulate different device behaviors based on type
            if self.device_type == "SmartSensor":
                self._simulate_sensor_behavior()
            elif self.device_type == "SmartCamera":
                self._simulate_camera_behavior()
            elif self.device_type == "SmartThermostat":
                self._simulate_thermostat_behavior()
            else:
                self._simulate_generic_behavior()

            # Wait between activities
            time.sleep(random.randint(30, 120))

        print("✅ Normal behavior simulation completed")

    def simulate_malicious_behavior(self):
        """Simulate malicious IoT device behavior"""
        print("🔴 Simulating malicious behavior...")

        malicious_actions = [
            self._simulate_port_scanning,
            self._simulate_botnet_communication,
            self._simulate_data_exfiltration,
            self._simulate_lateral_movement
        ]

        for action in malicious_actions:
            try:
                action()
                time.sleep(random.randint(5, 15))
            except Exception as e:
                print(f"   Error in malicious action: {e}")

        print("🚨 Malicious behavior simulation completed")

    def _simulate_sensor_behavior(self):
        """Simulate smart sensor communications"""
        destinations = [
            ("api.smartsensor.com", 443),
            ("time.nist.gov", 123),
            ("8.8.8.8", 53)  # DNS
        ]

        dest = random.choice(destinations)
        print(f"   📊 Sensor data upload to {dest[0]}:{dest[1]}")
        self._make_connection(dest[0], dest[1])

    def _simulate_camera_behavior(self):
        """Simulate smart camera communications"""
        destinations = [
            ("streaming.cloudcam.com", 443),
            ("update.camera.com", 80),
            ("time.nist.gov", 123)
        ]

        dest = random.choice(destinations)
        print(f"   📹 Camera stream to {dest[0]}:{dest[1]}")
        self._make_connection(dest[0], dest[1])

    def _simulate_thermostat_behavior(self):
        """Simulate smart thermostat communications"""
        destinations = [
            ("api.smartthermo.com", 443),
            ("weather.api.com", 443),
            ("time.nist.gov", 123)
        ]

        dest = random.choice(destinations)
        print(f"   🌡️ Thermostat sync to {dest[0]}:{dest[1]}")
        self._make_connection(dest[0], dest[1])

    def _simulate_generic_behavior(self):
        """Simulate generic IoT device behavior"""
        destinations = [
            ("api.iotcloud.com", 443),
            ("time.nist.gov", 123),
            ("8.8.8.8", 53)
        ]

        dest = random.choice(destinations)
        print(f"   🔗 Generic connection to {dest[0]}:{dest[1]}")
        self._make_connection(dest[0], dest[1])

    def _simulate_port_scanning(self):
        """Simulate port scanning activity"""
        print("   🔍 Port scanning activity...")
        target_ip = f"192.168.10.{random.randint(1, 254)}"

        for port in [22, 23, 80, 443, 8080]:
            self._make_connection(target_ip, port, timeout=1)

    def _simulate_botnet_communication(self):
        """Simulate botnet C&C communication"""
        print("   🤖 Botnet C&C communication...")

        malicious_servers = [
            ("malicious-c2.com", 8080),
            ("evil-botnet.net", 443),
            ("bad-actor.org", 9999)
        ]

        dest = random.choice(malicious_servers)
        self._make_connection(dest[0], dest[1])

    def _simulate_data_exfiltration(self):
        """Simulate data exfiltration attempt"""
        print("   📤 Data exfiltration attempt...")

        exfil_destinations = [
            ("dropbox.com", 443),
            ("pastebin.com", 443),
            ("attacker-server.com", 8080)
        ]

        dest = random.choice(exfil_destinations)
        self._make_connection(dest[0], dest[1])

    def _simulate_lateral_movement(self):
        """Simulate lateral movement attempt"""
        print("   ↔️ Lateral movement attempt...")

        # Try to connect to other devices on network
        for i in range(3):
            target_ip = f"192.168.10.{random.randint(1, 254)}"
            self._make_connection(target_ip, 22)  # SSH
            self._make_connection(target_ip, 445)  # SMB

    def _make_connection(self, host, port, timeout=3):
        """Make a network connection (simulated)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

def main():
    """Main simulation function"""
    print("🚀 IoT Device Simulation Framework")
    print("===================================")

    # Device types to simulate
    device_types = ["SmartSensor", "SmartCamera", "SmartThermostat", "SmartLight"]

    print("\nSelect simulation mode:")
    print("1. Single device normal behavior")
    print("2. Single device malicious behavior") 
    print("3. Multiple device mixed behavior")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        device_type = random.choice(device_types)
        simulator = IoTDeviceSimulator(device_type)

        if simulator.onboard_device():
            simulator.simulate_normal_behavior(20)

    elif choice == "2":
        device_type = random.choice(device_types)
        simulator = IoTDeviceSimulator(device_type)

        if simulator.onboard_device():
            # Start with normal behavior
            simulator.simulate_normal_behavior(5)
            time.sleep(30)
            # Then turn malicious
            simulator.simulate_malicious_behavior()

    elif choice == "3":
        devices = []

        # Create multiple devices
        for i in range(3):
            device_type = random.choice(device_types)
            simulator = IoTDeviceSimulator(device_type)

            if simulator.onboard_device():
                devices.append(simulator)
                time.sleep(5)  # Stagger onboarding

        print(f"\n🎭 Running mixed behavior simulation with {len(devices)} devices...")

        # Run mixed behaviors
        for i, device in enumerate(devices):
            if i % 2 == 0:  # Half normal, half malicious
                print(f"\n{device.device_id} -> Normal behavior")
                device.simulate_normal_behavior(10)
            else:
                print(f"\n{device.device_id} -> Malicious behavior")
                device.simulate_normal_behavior(5)
                time.sleep(30)
                device.simulate_malicious_behavior()

    else:
        print("Invalid choice")
        return

    print("\n✅ Simulation completed!")

if __name__ == "__main__":
    main()
