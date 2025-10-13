# Adaptive Zero Trust IoT Security Framework

A comprehensive security framework for Small Office/Home Office (SOHO) IoT networks that provides automatic device onboarding, continuous trust evaluation, and intelligent threat response through honeypot redirection.

## 🎯 Project Overview

This framework addresses the security challenges of IoT devices in SOHO networks by implementing:

- **Secure Device Onboarding**: Automatic certificate-based identity management
- **Zero Trust Architecture**: Continuous verification and least-privilege access
- **Behavioral Learning**: AI-driven analysis of device communication patterns  
- **Dynamic Trust Scoring**: Real-time assessment of device trustworthiness
- **Intelligent Response**: Automatic quarantine and honeypot redirection
- **Forensic Analysis**: Comprehensive attack pattern analysis

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IoT Device    │───▶│  Onboarding AP   │───▶│ Certificate     │
│                 │    │  (Raspberry Pi)  │    │ Authority       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌──────────────────┐            │
         │              │ Trust Management │            │
         │              │    & Policies    │            │
         │              └──────────────────┘            │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Production      │    │  SDN Controller  │    │   Honeypot      │
│ Network         │◀───│ (Ryu Framework)  │───▶│  Environment    │
│                 │    │                  │    │   (Docker)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
adaptive_zero_trust_iot_framework/
├── src/
│   ├── onboarding/
│   │   └── onboarding_service.py      # Flask web service for device enrollment
│   ├── trust_management/
│   │   └── trust_manager.py           # Continuous trust evaluation
│   ├── sdn_controller/
│   │   └── iot_controller.py          # Ryu-based SDN controller
│   ├── honeypot/
│   │   └── honeypot_manager.py        # Docker honeypot management
│   ├── database/
│   │   └── db_manager.py              # SQLite database operations
│   └── utils/
│       └── cert_manager.py            # Certificate Authority management
├── config/
│   └── config.py                      # System configuration
├── certificates/                      # CA and device certificates
├── logs/                             # System logs
├── honeypot_logs/                    # Honeypot interaction logs
├── data/                             # Database files
├── main.py                           # Main orchestrator
├── install.sh                        # Installation script
├── requirements.txt                  # Python dependencies
└── docker-compose.yml               # Honeypot container setup
```

## 🚀 Installation & Setup

### Prerequisites
- Raspberry Pi 4 (or compatible Linux system)
- Python 3.8+
- Docker
- WiFi adapter (for AP mode)

### Installation Steps

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd adaptive_zero_trust_iot_framework
chmod +x install.sh
./install.sh
```

2. **Configure network settings:**
```bash
# Edit config/config.py with your network parameters
nano config/config.py
```

3. **Start the framework:**
```bash
python3 main.py
```

## 📋 Configuration

### Key Configuration Parameters

```python
# Network Configuration
ONBOARDING_SSID = "IoT-Onboard"
ONBOARDING_IP_RANGE = "192.168.50.0/24"
QUARANTINE_IP_RANGE = "192.168.40.0/24"
HONEYPOT_IP = "192.168.40.10"

# Security Configuration
ONBOARDING_KEY = "PiSecret123"
INITIAL_TRUST_SCORE = 50
MIN_TRUST_THRESHOLD = 30

# Timing Configuration
LEARNING_PERIOD_MINUTES = 20
TRUST_EVALUATION_INTERVAL = 300
ATTESTATION_INTERVAL = 600
```

## 🔄 System Workflow

### Phase 1: Device Onboarding
1. IoT device connects to "IoT-Onboard" WiFi network
2. Device generates RSA key pair and CSR
3. Device sends onboarding request with shared key
4. System validates request and issues X.509 certificate
5. Device receives credentials for production network

### Phase 2: Behavior Learning
1. Device traffic monitored for 20-30 minutes
2. Communication patterns analyzed and recorded
3. Least-privilege network policies generated
4. Baseline behavior profile established

### Phase 3: Continuous Monitoring
1. Real-time trust score evaluation every 5 minutes
2. Device attestation challenges every 10 minutes  
3. Anomaly detection using behavioral baselines
4. Policy enforcement through SDN controller

### Phase 4: Threat Response
1. Low trust devices automatically quarantined
2. Traffic redirected to isolated honeypot environment
3. Attack patterns analyzed and logged
4. Forensic data collected for security analysis

## 🛡️ Security Features

### Zero Trust Implementation
- **Never Trust, Always Verify**: Continuous device authentication
- **Least Privilege Access**: Minimal required network permissions
- **Microsegmentation**: Isolated device communication paths

### Advanced Threat Detection
- **Behavioral Analysis**: ML-based anomaly detection
- **Dynamic Trust Scoring**: Multi-factor risk assessment
- **Real-time Response**: Automatic threat containment

### Forensic Capabilities
- **Honeypot Analysis**: Detailed attack pattern study
- **Event Correlation**: Comprehensive security logging
- **Threat Intelligence**: Attack signature generation

## 📊 Monitoring & Management

### Web Interface
- System status dashboard: `http://raspberry-pi:5000/status`
- Device management interface
- Real-time trust score monitoring
- Event log analysis

### Key Metrics
- Total devices onboarded
- Active vs. quarantined devices
- Trust score distributions
- Attack patterns detected

### Log Analysis
```bash
# View system logs
tail -f logs/framework.log

# Monitor honeypot interactions
tail -f honeypot_logs/cowrie.json

# Check database events
sqlite3 data/iot_framework.db "SELECT * FROM events ORDER BY timestamp DESC LIMIT 10;"
```

## 🔧 API Endpoints

### Onboarding Service
- `POST /onboard` - Device enrollment endpoint
- `GET /status` - System status and statistics
- `GET /health` - Health check

### Device Management
- Device trust score updates
- Policy management
- Quarantine control

## 🧪 Testing & Validation

### Simulated Attack Scenarios
1. **Botnet Communication**: Device attempts C&C connections
2. **Port Scanning**: Malicious network reconnaissance  
3. **Data Exfiltration**: Unauthorized data transmission
4. **Lateral Movement**: Inter-device attack attempts

### Validation Metrics
- Detection accuracy (false positives/negatives)
- Response time to threats
- System performance impact
- User experience quality

## 🚨 Troubleshooting

### Common Issues
1. **Certificate Generation Errors**: Check OpenSSL installation
2. **Docker Container Issues**: Verify Docker service status
3. **Network Configuration**: Ensure proper DHCP/DNS setup
4. **Database Permissions**: Check file system permissions

### Debug Mode
```bash
# Run with detailed logging
DEBUG=1 python3 main.py

# Check component status
python3 -c "from src.honeypot.honeypot_manager import HoneypotManager; hm = HoneypotManager(); print(hm.get_honeypot_status())"
```

## 📚 Research Applications

This framework serves as a research platform for:
- IoT security architecture evaluation
- Zero trust implementation studies
- Behavioral analysis algorithm development
- Attack pattern research
- Network policy optimization

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/enhancement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/enhancement`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📖 Citation

If you use this framework in your research, please cite:

```bibtex
@misc{adaptive_zero_trust_iot,
  title={Adaptive Zero Trust Security Framework for SOHO IoT Networks},
  author={[Your Name]},
  year={2025},
  url={https://github.com/[username]/adaptive-zero-trust-iot-framework}
}
```

## 📞 Support

For questions or issues:
- Create GitHub issue for bugs/features
- Consult documentation for setup help
- Review logs for troubleshooting

---

**⚡ Built for securing the IoT ecosystem with intelligent, adaptive defense mechanisms.**
