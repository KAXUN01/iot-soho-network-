# Create main orchestrator that ties everything together
main_orchestrator = '''"""
Main Orchestrator for Adaptive Zero Trust IoT Framework
Coordinates all system components and provides central management
"""
import time
import threading
import signal
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.onboarding.onboarding_service import app
from src.trust_management.trust_manager import TrustManager
from src.honeypot.honeypot_manager import HoneypotManager
from src.database.db_manager import create_database
from config.config import *

class IoTFrameworkOrchestrator:
    def __init__(self):
        print("Initializing Adaptive Zero Trust IoT Framework...")
        
        # Initialize database
        create_database(DATABASE_PATH)
        
        # Initialize components
        self.trust_manager = TrustManager(DATABASE_PATH)
        self.honeypot_manager = HoneypotManager()
        
        # Threading for services
        self.flask_thread = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def start_framework(self):
        """Start all framework components"""
        print("Starting IoT Framework components...")
        
        self.running = True
        
        # Start Flask onboarding service in separate thread
        self.flask_thread = threading.Thread(target=self._run_flask_service)
        self.flask_thread.daemon = True
        self.flask_thread.start()
        print("✓ Onboarding service started on port 5000")
        
        # Start trust management
        self.trust_manager.start_trust_evaluation()
        print("✓ Trust management service started")
        
        # Deploy and start honeypots
        self.honeypot_manager.deploy_cowrie_honeypot()
        self.honeypot_manager.deploy_dionaea_honeypot()
        self.honeypot_manager.start_log_monitoring()
        print("✓ Honeypot services started")
        
        print("\\n" + "="*50)
        print("🚀 IoT Framework is now running!")
        print("="*50)
        print(f"📡 Onboarding service: http://localhost:5000")
        print(f"🔑 Onboarding key: {ONBOARDING_KEY}")
        print(f"📊 Trust evaluation interval: {TRUST_EVALUATION_INTERVAL}s")
        print(f"🍯 Honeypot IP: {HONEYPOT_IP}")
        print(f"📁 Database: {DATABASE_PATH}")
        print("="*50)
        
        # Start monitoring and management loop
        self._management_loop()
    
    def _run_flask_service(self):
        """Run Flask onboarding service"""
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
    def _management_loop(self):
        """Main management and monitoring loop"""
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                
                # Print status every 10 iterations (10 minutes)
                if iteration % 10 == 0:
                    self._print_status()
                
                # Perform periodic maintenance
                if iteration % 60 == 0:  # Every hour
                    self._perform_maintenance()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in management loop: {e}")
                time.sleep(30)
    
    def _print_status(self):
        """Print system status summary"""
        try:
            import sqlite3
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get device statistics
            cursor.execute("SELECT COUNT(*) FROM devices")
            total_devices = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM devices WHERE quarantined = TRUE")
            quarantined_devices = cursor.fetchone()[0]
            
            cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE timestamp > datetime('now', '-1 hour')
            """)
            recent_events = cursor.fetchone()[0]
            
            conn.close()
            
            # Get honeypot status
            honeypot_status = self.honeypot_manager.get_honeypot_status()
            active_honeypots = len([h for h in honeypot_status.values() 
                                  if h.get('status') == 'running'])
            
            print(f"\\n📊 System Status ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"   Devices: {total_devices} total, {quarantined_devices} quarantined")
            print(f"   Events: {recent_events} in last hour")
            print(f"   Honeypots: {active_honeypots} active")
            
        except Exception as e:
            print(f"Error getting status: {e}")
    
    def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        print("🔧 Performing maintenance tasks...")
        
        # Clean up old events (keep last 30 days)
        try:
            import sqlite3
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
            DELETE FROM events 
            WHERE timestamp < datetime('now', '-30 days')
            """)
            
            deleted_events = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_events > 0:
                print(f"   Cleaned up {deleted_events} old events")
                
        except Exception as e:
            print(f"   Error during maintenance: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\\nReceived signal {signum}. Shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Gracefully shutdown all services"""
        print("Shutting down IoT Framework...")
        
        self.running = False
        
        # Stop trust management
        if self.trust_manager:
            self.trust_manager.stop_trust_evaluation()
            print("✓ Trust management stopped")
        
        # Stop honeypots
        if self.honeypot_manager:
            self.honeypot_manager.stop_log_monitoring()
            self.honeypot_manager.stop_all_honeypots()
            print("✓ Honeypots stopped")
        
        print("✓ IoT Framework shutdown complete")

def main():
    """Main entry point"""
    print("\\n" + "="*60)
    print("🛡️  ADAPTIVE ZERO TRUST IoT SECURITY FRAMEWORK")
    print("="*60)
    
    orchestrator = IoTFrameworkOrchestrator()
    
    try:
        orchestrator.start_framework()
    except KeyboardInterrupt:
        print("\\nShutdown requested by user")
        orchestrator.shutdown()
    except Exception as e:
        print(f"Fatal error: {e}")
        orchestrator.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

with open(f"{project_name}/main.py", "w") as f:
    f.write(main_orchestrator)
    
print("Created main orchestrator: main.py")