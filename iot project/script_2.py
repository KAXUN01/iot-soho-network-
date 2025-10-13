# Create database schema and initialization
database_schema = '''"""
Database schema and initialization for IoT Framework
"""
import sqlite3
import os
from datetime import datetime

def create_database(db_path):
    """Create and initialize the SQLite database with required tables"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Devices table - stores device information and certificates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        device_id TEXT PRIMARY KEY,
        mac_address TEXT UNIQUE NOT NULL,
        certificate_pem TEXT,
        trust_score INTEGER DEFAULT 50,
        status TEXT DEFAULT 'onboarding',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        learning_complete BOOLEAN DEFAULT FALSE,
        quarantined BOOLEAN DEFAULT FALSE
    )
    """)
    
    # Policy table - stores network access policies per device
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        policy_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
    )
    """)
    
    # Events table - logs all security events and activities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        event_type TEXT NOT NULL,
        description TEXT,
        severity TEXT DEFAULT 'INFO',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
    )
    """)
    
    # Traffic baseline table - stores learned behavior patterns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS traffic_baseline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        destination_ip TEXT,
        destination_port INTEGER,
        protocol TEXT,
        frequency INTEGER DEFAULT 1,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices(device_id)
    )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_device ON events(device_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_policies_device ON policies(device_id)")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

def add_device(db_path, device_id, mac_address, certificate_pem=None):
    """Add a new device to the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO devices (device_id, mac_address, certificate_pem)
        VALUES (?, ?, ?)
        """, (device_id, mac_address, certificate_pem))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_trust_score(db_path, device_id, new_score):
    """Update device trust score"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    UPDATE devices 
    SET trust_score = ?, last_seen = CURRENT_TIMESTAMP
    WHERE device_id = ?
    """, (new_score, device_id))
    
    conn.commit()
    conn.close()

def log_event(db_path, device_id, event_type, description, severity='INFO'):
    """Log a security event"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO events (device_id, event_type, description, severity)
    VALUES (?, ?, ?, ?)
    """, (device_id, event_type, description, severity))
    
    conn.commit()
    conn.close()

def get_device_by_mac(db_path, mac_address):
    """Retrieve device information by MAC address"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT * FROM devices WHERE mac_address = ?
    """, (mac_address,))
    
    result = cursor.fetchone()
    conn.close()
    return result

if __name__ == "__main__":
    # Test database creation
    create_database("../data/iot_framework.db")
'''

with open(f"{project_name}/src/database/db_manager.py", "w") as f:
    f.write(database_schema)
    
print("Created database manager: src/database/db_manager.py")