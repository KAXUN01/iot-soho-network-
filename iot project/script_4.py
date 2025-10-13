# Create onboarding service (Flask web server)
onboarding_service = '''"""
IoT Device Onboarding Service
Flask web service for secure device enrollment
"""
from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cert_manager import CertificateManager
from database.db_manager import create_database, add_device, log_event, get_device_by_mac
from config.config import *

app = Flask(__name__)
cert_manager = CertificateManager()

# Initialize database
create_database(DATABASE_PATH)

@app.route('/onboard', methods=['POST'])
def onboard_device():
    """Handle device onboarding requests"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['mac_address', 'public_key_pem', 'onboard_key', 'device_info']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        # Verify onboarding key
        if data['onboard_key'] != ONBOARDING_KEY:
            log_event(DATABASE_PATH, data['mac_address'], 'ONBOARD_FAILED', 
                     'Invalid onboarding key', 'WARNING')
            return jsonify({
                'success': False,
                'error': 'Invalid onboarding key'
            }), 403
        
        # Check if device already exists
        existing_device = get_device_by_mac(DATABASE_PATH, data['mac_address'])
        if existing_device:
            return jsonify({
                'success': False,
                'error': 'Device already onboarded'
            }), 409
        
        # Generate unique device ID
        device_id = f"IoT-{uuid.uuid4().hex[:8]}"
        
        # Create device certificate
        device_cert_pem = cert_manager.create_device_certificate(
            device_id, data['public_key_pem']
        )
        
        if not device_cert_pem:
            return jsonify({
                'success': False,
                'error': 'Failed to create device certificate'
            }), 500
        
        # Store device in database
        success = add_device(DATABASE_PATH, device_id, data['mac_address'], device_cert_pem)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to store device information'
            }), 500
        
        # Log successful onboarding
        log_event(DATABASE_PATH, device_id, 'ONBOARD_SUCCESS', 
                 f"Device {data['device_info'].get('type', 'Unknown')} successfully onboarded")
        
        # Prepare response with certificates and network credentials
        response = {
            'success': True,
            'device_id': device_id,
            'device_certificate': device_cert_pem,
            'ca_certificate': cert_manager.get_ca_certificate_pem(),
            'network_config': {
                'production_ssid': 'IoT-Production',  # Switch to production network
                'production_password': 'SecureIoT2024',
                'gateway_ip': '192.168.10.1'
            },
            'learning_period_minutes': LEARNING_PERIOD_MINUTES,
            'message': 'Device onboarded successfully. Switching to production network for behavior learning.'
        }
        
        print(f"Device {device_id} ({data['mac_address']}) onboarded successfully")
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Onboarding error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get system status and statistics"""
    try:
        import sqlite3
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get device statistics
        cursor.execute("SELECT COUNT(*) FROM devices")
        total_devices = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
        active_devices = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM devices WHERE quarantined = TRUE")
        quarantined_devices = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'ANOMALY_DETECTED'")
        anomaly_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'system_status': 'operational',
            'statistics': {
                'total_devices': total_devices,
                'active_devices': active_devices,
                'quarantined_devices': quarantined_devices,
                'anomalies_detected': anomaly_count
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'system_status': 'error',
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting IoT Onboarding Service...")
    print(f"Onboarding key: {ONBOARDING_KEY}")
    print(f"Database path: {DATABASE_PATH}")
    app.run(host='0.0.0.0', port=5000, debug=True)
'''

with open(f"{project_name}/src/onboarding/onboarding_service.py", "w") as f:
    f.write(onboarding_service)
    
print("Created onboarding service: src/onboarding/onboarding_service.py")