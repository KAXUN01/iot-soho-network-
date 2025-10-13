# Create honeypot management module
honeypot_manager_code = '''"""
Honeypot Management System
Manages Docker-based honeypots for analyzing compromised IoT devices
"""
import docker
import json
import sqlite3
import threading
import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import log_event
from config.config import *

class HoneypotManager:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            print("Docker client initialized successfully")
        except Exception as e:
            print(f"Error initializing Docker client: {e}")
            self.docker_client = None
        
        self.active_honeypots = {}
        self.log_monitor_thread = None
        self.monitoring = False
    
    def deploy_cowrie_honeypot(self, container_name="iot-cowrie-honeypot"):
        """Deploy Cowrie SSH/Telnet honeypot"""
        if not self.docker_client:
            print("Docker client not available")
            return False
        
        try:
            # Check if container already exists
            try:
                existing = self.docker_client.containers.get(container_name)
                if existing.status == 'running':
                    print(f"Cowrie honeypot already running: {container_name}")
                    return True
                else:
                    existing.remove()
            except docker.errors.NotFound:
                pass
            
            # Deploy Cowrie honeypot container
            container = self.docker_client.containers.run(
                image="cowrie/cowrie:latest",
                name=container_name,
                ports={
                    '2222/tcp': ('0.0.0.0', 2222),  # SSH
                    '2223/tcp': ('0.0.0.0', 2223),  # Telnet
                },
                volumes={
                    f"{os.getcwd()}/honeypot_logs": {
                        'bind': '/cowrie/var/log/cowrie', 
                        'mode': 'rw'
                    }
                },
                environment={
                    'COWRIE_HOSTNAME': 'iot-device',
                    'COWRIE_LOG_LEVEL': 'INFO'
                },
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.active_honeypots[container_name] = {
                'container': container,
                'type': 'cowrie',
                'ip': HONEYPOT_IP,
                'ports': [2222, 2223],
                'started_at': datetime.now()
            }
            
            print(f"Cowrie honeypot deployed: {container_name}")
            print(f"SSH access: {HONEYPOT_IP}:2222")
            print(f"Telnet access: {HONEYPOT_IP}:2223")
            
            return True
            
        except Exception as e:
            print(f"Error deploying Cowrie honeypot: {e}")
            return False
    
    def deploy_dionaea_honeypot(self, container_name="iot-dionaea-honeypot"):
        """Deploy Dionaea multi-protocol honeypot"""
        if not self.docker_client:
            print("Docker client not available")
            return False
        
        try:
            # Check if container already exists
            try:
                existing = self.docker_client.containers.get(container_name)
                if existing.status == 'running':
                    print(f"Dionaea honeypot already running: {container_name}")
                    return True
                else:
                    existing.remove()
            except docker.errors.NotFound:
                pass
            
            # Deploy Dionaea honeypot container
            container = self.docker_client.containers.run(
                image="dinotools/dionaea:latest",
                name=container_name,
                ports={
                    '21/tcp': ('0.0.0.0', 21),    # FTP
                    '80/tcp': ('0.0.0.0', 8080),  # HTTP
                    '443/tcp': ('0.0.0.0', 8443), # HTTPS
                    '135/tcp': ('0.0.0.0', 135),  # RPC
                    '445/tcp': ('0.0.0.0', 445),  # SMB
                },
                volumes={
                    f"{os.getcwd()}/honeypot_logs": {
                        'bind': '/opt/dionaea/var/log', 
                        'mode': 'rw'
                    }
                },
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.active_honeypots[container_name] = {
                'container': container,
                'type': 'dionaea',
                'ip': HONEYPOT_IP,
                'ports': [21, 80, 443, 135, 445],
                'started_at': datetime.now()
            }
            
            print(f"Dionaea honeypot deployed: {container_name}")
            return True
            
        except Exception as e:
            print(f"Error deploying Dionaea honeypot: {e}")
            return False
    
    def start_log_monitoring(self):
        """Start monitoring honeypot logs for analysis"""
        if not self.monitoring:
            self.monitoring = True
            self.log_monitor_thread = threading.Thread(target=self._monitor_logs)
            self.log_monitor_thread.daemon = True
            self.log_monitor_thread.start()
            print("Honeypot log monitoring started")
    
    def stop_log_monitoring(self):
        """Stop log monitoring"""
        self.monitoring = False
        if self.log_monitor_thread:
            self.log_monitor_thread.join()
        print("Honeypot log monitoring stopped")
    
    def _monitor_logs(self):
        """Monitor honeypot logs for attack analysis"""
        log_dir = f"{os.getcwd()}/honeypot_logs"
        os.makedirs(log_dir, exist_ok=True)
        
        while self.monitoring:
            try:
                # Monitor Cowrie logs
                self._process_cowrie_logs(log_dir)
                
                # Monitor Dionaea logs  
                self._process_dionaea_logs(log_dir)
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error monitoring logs: {e}")
                time.sleep(60)
    
    def _process_cowrie_logs(self, log_dir):
        """Process Cowrie SSH/Telnet honeypot logs"""
        cowrie_log = os.path.join(log_dir, "cowrie.json")
        if not os.path.exists(cowrie_log):
            return
        
        try:
            # Read new log entries (simplified - in production, track file position)
            with open(cowrie_log, 'r') as f:
                lines = f.readlines()
                
            # Process recent entries
            for line in lines[-10:]:  # Process last 10 entries
                try:
                    log_entry = json.loads(line)
                    self._analyze_cowrie_event(log_entry)
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error processing Cowrie logs: {e}")
    
    def _analyze_cowrie_event(self, log_entry):
        """Analyze individual Cowrie log event"""
        event_type = log_entry.get('eventid', '')
        src_ip = log_entry.get('src_ip', '')
        
        if event_type == 'cowrie.login.success':
            username = log_entry.get('username', '')
            password = log_entry.get('password', '')
            
            print(f"Honeypot login: {src_ip} -> {username}:{password}")
            
            # Log to database
            self._log_honeypot_interaction(src_ip, 'SSH_LOGIN', 
                                         f"Login attempt: {username}:{password}")
        
        elif event_type == 'cowrie.command.input':
            command = log_entry.get('input', '')
            
            print(f"Honeypot command: {src_ip} -> {command}")
            
            self._log_honeypot_interaction(src_ip, 'COMMAND_EXECUTION', 
                                         f"Command: {command}")
        
        elif event_type == 'cowrie.session.file_download':
            url = log_entry.get('url', '')
            
            print(f"Honeypot download: {src_ip} -> {url}")
            
            self._log_honeypot_interaction(src_ip, 'FILE_DOWNLOAD', 
                                         f"Downloaded: {url}")
    
    def _process_dionaea_logs(self, log_dir):
        """Process Dionaea honeypot logs"""
        # Simplified log processing - Dionaea logs are more complex
        dionaea_log = os.path.join(log_dir, "dionaea.log")
        if not os.path.exists(dionaea_log):
            return
        
        # Process Dionaea logs (implementation depends on log format)
        # This is a placeholder for actual log processing
        pass
    
    def _log_honeypot_interaction(self, src_ip, interaction_type, description):
        """Log honeypot interaction to database"""
        try:
            # Find device by IP (simplified - in production, use proper IP tracking)
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # For now, log as general honeypot interaction
            log_event(DATABASE_PATH, f"IP:{src_ip}", 'HONEYPOT_INTERACTION', 
                     f"{interaction_type}: {description}", 'HIGH')
            
            conn.close()
            
        except Exception as e:
            print(f"Error logging honeypot interaction: {e}")
    
    def get_honeypot_status(self):
        """Get status of all honeypots"""
        status = {}
        
        for name, info in self.active_honeypots.items():
            container = info['container']
            try:
                container.reload()
                status[name] = {
                    'status': container.status,
                    'type': info['type'],
                    'ip': info['ip'],
                    'ports': info['ports'],
                    'started_at': info['started_at'].isoformat(),
                    'uptime': str(datetime.now() - info['started_at'])
                }
            except Exception as e:
                status[name] = {'status': 'error', 'error': str(e)}
        
        return status
    
    def stop_honeypot(self, container_name):
        """Stop a specific honeypot"""
        if container_name in self.active_honeypots:
            try:
                container = self.active_honeypots[container_name]['container']
                container.stop()
                container.remove()
                del self.active_honeypots[container_name]
                print(f"Honeypot stopped: {container_name}")
                return True
            except Exception as e:
                print(f"Error stopping honeypot: {e}")
                return False
        return False
    
    def stop_all_honeypots(self):
        """Stop all running honeypots"""
        for container_name in list(self.active_honeypots.keys()):
            self.stop_honeypot(container_name)

# Example usage
if __name__ == "__main__":
    honeypot_manager = HoneypotManager()
    
    print("Deploying honeypots...")
    honeypot_manager.deploy_cowrie_honeypot()
    honeypot_manager.deploy_dionaea_honeypot()
    
    print("Starting log monitoring...")
    honeypot_manager.start_log_monitoring()
    
    try:
        # Keep running
        while True:
            time.sleep(60)
            status = honeypot_manager.get_honeypot_status()
            print(f"Honeypot status: {len(status)} active")
    except KeyboardInterrupt:
        print("\\nShutting down honeypots...")
        honeypot_manager.stop_log_monitoring()
        honeypot_manager.stop_all_honeypots()
'''

with open(f"{project_name}/src/honeypot/honeypot_manager.py", "w") as f:
    f.write(honeypot_manager_code)
    
print("Created honeypot manager: src/honeypot/honeypot_manager.py")