# Create main project configuration
config_content = """# Adaptive Zero Trust IoT Framework Configuration

# Network Configuration
ONBOARDING_SSID = "IoT-Onboard"
ONBOARDING_PASSWORD = ""  # Open network for initial connection
ONBOARDING_IP_RANGE = "192.168.50.0/24"
QUARANTINE_IP_RANGE = "192.168.40.0/24"
HONEYPOT_IP = "192.168.40.10"

# Security Configuration  
ONBOARDING_KEY = "PiSecret123"
CA_CERT_VALIDITY_DAYS = 3650
DEVICE_CERT_VALIDITY_DAYS = 365
INITIAL_TRUST_SCORE = 50
MIN_TRUST_THRESHOLD = 30

# Behavioral Learning
LEARNING_PERIOD_MINUTES = 20
TRUST_EVALUATION_INTERVAL = 300  # seconds
ATTESTATION_INTERVAL = 600  # seconds

# Database Configuration
DATABASE_PATH = "data/iot_framework.db"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "logs/framework.log"

# SDN Controller Configuration
RYU_HOST = "127.0.0.1"
RYU_PORT = 8080
OPENFLOW_PORT = 6653
"""

with open(f"{project_name}/config/config.py", "w") as f:
    f.write(config_content)
    
print("Created configuration file: config/config.py")