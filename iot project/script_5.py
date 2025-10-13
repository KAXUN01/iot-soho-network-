# Create trust management module
trust_manager_code = '''"""
Trust Management System
Continuous evaluation and scoring of device trustworthiness
"""
import sqlite3
import time
import threading
from datetime import datetime, timedelta
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import update_trust_score, log_event
from config.config import *

class TrustManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.running = False
        self.evaluation_thread = None
        
        # Trust scoring parameters
        self.trust_factors = {
            'normal_operation': +10,
            'unexpected_connection': -20,
            'failed_attestation': -30,
            'successful_attestation': +5,
            'anomaly_detected': -25,
            'honeypot_interaction': -50,
            'policy_violation': -15
        }
    
    def start_trust_evaluation(self):
        """Start continuous trust evaluation in background thread"""
        if not self.running:
            self.running = True
            self.evaluation_thread = threading.Thread(target=self._trust_evaluation_loop)
            self.evaluation_thread.daemon = True
            self.evaluation_thread.start()
            print("Trust evaluation service started")
    
    def stop_trust_evaluation(self):
        """Stop trust evaluation service"""
        self.running = False
        if self.evaluation_thread:
            self.evaluation_thread.join()
        print("Trust evaluation service stopped")
    
    def _trust_evaluation_loop(self):
        """Main trust evaluation loop"""
        while self.running:
            try:
                self.evaluate_all_devices()
                time.sleep(TRUST_EVALUATION_INTERVAL)
            except Exception as e:
                print(f"Trust evaluation error: {e}")
                time.sleep(30)  # Wait before retrying
    
    def evaluate_all_devices(self):
        """Evaluate trust scores for all active devices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all active devices
        cursor.execute("""
        SELECT device_id, mac_address, trust_score, last_seen 
        FROM devices 
        WHERE status = 'active' AND quarantined = FALSE
        """)
        
        devices = cursor.fetchall()
        conn.close()
        
        for device_id, mac_address, current_score, last_seen in devices:
            new_score = self.calculate_trust_score(device_id, current_score)
            
            if new_score != current_score:
                update_trust_score(self.db_path, device_id, new_score)
                log_event(self.db_path, device_id, 'TRUST_UPDATE', 
                         f"Trust score updated: {current_score} -> {new_score}")
                
                # Check if device should be quarantined
                if new_score < MIN_TRUST_THRESHOLD:
                    self.quarantine_device(device_id)
    
    def calculate_trust_score(self, device_id, current_score):
        """Calculate new trust score based on recent events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent events (last 24 hours)
        cursor.execute("""
        SELECT event_type, COUNT(*) as count
        FROM events
        WHERE device_id = ? 
        AND timestamp > datetime('now', '-24 hours')
        GROUP BY event_type
        """, (device_id,))
        
        recent_events = cursor.fetchall()
        conn.close()
        
        # Calculate score adjustments
        score_adjustment = 0
        for event_type, count in recent_events:
            if event_type == 'NORMAL_OPERATION':
                score_adjustment += min(count * self.trust_factors['normal_operation'], 20)
            elif event_type == 'ANOMALY_DETECTED':
                score_adjustment += count * self.trust_factors['anomaly_detected']
            elif event_type == 'FAILED_ATTESTATION':
                score_adjustment += count * self.trust_factors['failed_attestation']
            elif event_type == 'SUCCESSFUL_ATTESTATION':
                score_adjustment += count * self.trust_factors['successful_attestation']
            elif event_type == 'POLICY_VIOLATION':
                score_adjustment += count * self.trust_factors['policy_violation']
            elif event_type == 'HONEYPOT_INTERACTION':
                score_adjustment += count * self.trust_factors['honeypot_interaction']
        
        # Apply time-based degradation (small penalty for inactivity)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT last_seen FROM devices WHERE device_id = ?
        """, (device_id,))
        
        last_seen = cursor.fetchone()[0]
        conn.close()
        
        if last_seen:
            last_seen_time = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            hours_inactive = (datetime.now() - last_seen_time.replace(tzinfo=None)).total_seconds() / 3600
            
            if hours_inactive > 24:  # Penalize devices inactive for more than 24 hours
                score_adjustment -= min(int(hours_inactive / 24) * 2, 10)
        
        # Calculate new score (bounded between 0 and 100)
        new_score = max(0, min(100, current_score + score_adjustment))
        return new_score
    
    def quarantine_device(self, device_id):
        """Quarantine a device with low trust score"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE devices 
        SET quarantined = TRUE, status = 'quarantined'
        WHERE device_id = ?
        """, (device_id,))
        
        conn.commit()
        conn.close()
        
        log_event(self.db_path, device_id, 'DEVICE_QUARANTINED', 
                 f"Device quarantined due to low trust score", 'CRITICAL')
        
        print(f"Device {device_id} has been quarantined due to low trust score")
        
        # Trigger SDN controller to redirect traffic to honeypot
        self.redirect_to_honeypot(device_id)
    
    def redirect_to_honeypot(self, device_id):
        """Request SDN controller to redirect device traffic to honeypot"""
        try:
            # Get device MAC address
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT mac_address FROM devices WHERE device_id = ?", (device_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                mac_address = result[0]
                print(f"Redirecting device {device_id} ({mac_address}) to honeypot")
                
                # Here we would send command to SDN controller
                # For now, just log the action
                log_event(self.db_path, device_id, 'HONEYPOT_REDIRECT', 
                         f"Traffic redirected to honeypot at {HONEYPOT_IP}")
                
        except Exception as e:
            print(f"Error redirecting device to honeypot: {e}")
    
    def attestation_challenge(self, device_id):
        """Send attestation challenge to device"""
        # Generate random challenge
        import secrets
        challenge = secrets.token_hex(32)
        
        # Store challenge temporarily (in production, use Redis or memory cache)
        log_event(self.db_path, device_id, 'ATTESTATION_CHALLENGE', 
                 f"Challenge sent: {challenge[:16]}...", 'INFO')
        
        # Here you would send the challenge to the device via network
        # and wait for signed response
        print(f"Attestation challenge sent to {device_id}")
        
        # Simulate attestation result (in real implementation, verify signature)
        import random
        if random.random() > 0.1:  # 90% success rate for simulation
            self.record_attestation_success(device_id)
        else:
            self.record_attestation_failure(device_id)
    
    def record_attestation_success(self, device_id):
        """Record successful attestation"""
        log_event(self.db_path, device_id, 'SUCCESSFUL_ATTESTATION', 
                 'Device attestation successful')
        
        # Update trust score immediately
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT trust_score FROM devices WHERE device_id = ?", (device_id,))
        current_score = cursor.fetchone()[0]
        conn.close()
        
        new_score = min(100, current_score + self.trust_factors['successful_attestation'])
        update_trust_score(self.db_path, device_id, new_score)
    
    def record_attestation_failure(self, device_id):
        """Record failed attestation"""
        log_event(self.db_path, device_id, 'FAILED_ATTESTATION', 
                 'Device attestation failed', 'WARNING')
        
        # Update trust score immediately
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT trust_score FROM devices WHERE device_id = ?", (device_id,))
        current_score = cursor.fetchone()[0]
        conn.close()
        
        new_score = max(0, current_score + self.trust_factors['failed_attestation'])
        update_trust_score(self.db_path, device_id, new_score)

# Example usage
if __name__ == "__main__":
    trust_manager = TrustManager(DATABASE_PATH)
    
    print("Starting Trust Management System...")
    trust_manager.start_trust_evaluation()
    
    try:
        # Keep the service running
        while True:
            time.sleep(60)
            print(f"Trust evaluation running... {datetime.now()}")
    except KeyboardInterrupt:
        print("\\nShutting down Trust Management System...")
        trust_manager.stop_trust_evaluation()
'''

with open(f"{project_name}/src/trust_management/trust_manager.py", "w") as f:
    f.write(trust_manager_code)
    
print("Created trust manager: src/trust_management/trust_manager.py")