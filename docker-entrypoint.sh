#!/bin/sh
set -e

echo "[entrypoint] Initializing Adaptive Zero Trust IoT Framework"

cd /app/framework

# Initialize database
python - <<'PY'
from src.database.db_manager import create_database
from config.config import DATABASE_PATH
print(f"[entrypoint] Creating database at {DATABASE_PATH}")
create_database(DATABASE_PATH)
print("[entrypoint] Database ready")
PY

# Start Ryu controller in background
echo "[entrypoint] Starting Ryu controller on 0.0.0.0:6653"
PYTHONPATH="/app/framework" ryu-manager --ofp-tcp-listen-port 6653 src/sdn_controller/iot_controller.py &
RYU_PID=$!

# Start the framework (Flask onboarding + trust manager + honeypot manager)
echo "[entrypoint] Starting framework main.py"
python main.py &
FW_PID=$!

trap 'echo "[entrypoint] Stopping..."; kill $RYU_PID $FW_PID 2>/dev/null || true; exit 0' TERM INT

wait $FW_PID

