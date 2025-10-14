## Docker Guide: Adaptive Zero Trust IoT Framework

This guide shows how to run the framework (Flask onboarding API + Trust Manager + Ryu controller) and Mininet using Docker.

### Prerequisites
- Docker Engine 20.10+
- Docker Compose v2 (docker compose command)
- Linux host (recommended). If on Windows/macOS, ensure Docker supports host networking requirements.

### Repository Layout (relevant to Docker)
- `Dockerfile` – container for the framework and Ryu controller
- `docker-entrypoint.sh` – initializes DB and starts services in the container
- `docker-compose.framework.yml` – compose services for framework (and optional Mininet)
- `mininet-run.sh` – helper to run Mininet container interactively against a specific controller IP

Volumes are mounted for persistence:
- `iot project/adaptive_zero_trust_iot_framework/data` → database
- `iot project/adaptive_zero_trust_iot_framework/logs` → framework logs
- `iot project/adaptive_zero_trust_iot_framework/honeypot_logs` → honeypot logs
- `iot project/adaptive_zero_trust_iot_framework/certificates` → CA/device certs

### Build the Framework Image
From the repository root:

```bash
docker build -t iot-framework:latest .
```

This installs Python deps (Flask, cryptography, docker SDK, scapy, Ryu) and copies the framework into `/app/framework` inside the image.

### Run the Framework with Compose (recommended)
```bash
docker compose -f docker-compose.framework.yml up -d
```

What it does:
- Starts the `framework` container
  - Initializes the SQLite database
  - Launches Ryu controller on TCP 6653
  - Runs the framework `main.py` (Flask API on port 5000)
- Mounts host directories for data/logs/certs/honeypot logs
- Mounts `/var/run/docker.sock` so the framework can manage honeypot containers

Exposed ports on the host:
- 5000/tcp → Flask onboarding API (`/health`, `/status`, `/onboard`)
- 6653/tcp → Ryu OpenFlow controller

Verify services:
```bash
curl http://localhost:5000/health
curl http://localhost:5000/status
```

Show container logs:
```bash
docker compose -f docker-compose.framework.yml logs -f framework
```

Stop and remove:
```bash
docker compose -f docker-compose.framework.yml down
```

### Mininet Options

Option A: Run Mininet alongside the framework on the same host via Compose (host networking)
```bash
docker compose -f docker-compose.framework.yml up -d
# The compose file includes a `mininet` service that connects to controller 127.0.0.1:6653
docker compose -f docker-compose.framework.yml logs -f mininet
```

Option B: Run Mininet interactively pointing at any controller IP
```bash
chmod +x ./mininet-run.sh
./mininet-run.sh <CONTROLLER_IP> 6653
# Example (same host): ./mininet-run.sh 127.0.0.1 6653
# Example (remote controller): ./mininet-run.sh 192.168.137.104 6653
```

The helper launches the `opennetworking/mininet:stable` image with `--network host` and runs:
```bash
mn --topo single,3 --mac --controller=remote,ip=$CTRL_IP,port=$CTRL_PORT --switch ovsk,protocols=OpenFlow13
```

### Honeypots
The framework uses the Docker SDK to deploy Cowrie and Dionaea containers. Because `/var/run/docker.sock` is mounted into the framework container, the framework can start/stop honeypot containers on the host. Logs are written to `honeypot_logs/` (bind-mounted).

If you prefer to manage honeypots separately with Compose, you can add services (e.g., `cowrie`, `dionaea`) to `docker-compose.framework.yml` similarly to the existing examples in the project.

### Common Commands
- List containers:
```bash
docker ps
```
- Tail framework logs:
```bash
docker compose -f docker-compose.framework.yml logs -f framework
```
- View API health/status:
```bash
curl http://localhost:5000/health
curl http://localhost:5000/status
```

### Troubleshooting
- Flask 5000 not reachable:
  - Ensure the container is running: `docker ps`
  - Check logs: `docker compose -f docker-compose.framework.yml logs -f framework`
  - Confirm port mapping (5000:5000) not in use by another process

- Mininet cannot connect to controller:
  - Ensure controller port 6653 is listening in the framework logs
  - If controller is on another host, use `mininet-run.sh <controller_ip> 6653`
  - Firewalls must allow inbound TCP 6653

- Honeypot errors about Docker client:
  - Confirm `/var/run/docker.sock` is mounted into the framework container
  - Ensure Docker is running on the host

### Notes
- The framework container runs as a single process supervisor via `docker-entrypoint.sh` starting both Ryu and the framework app.
- Data/logs/certs directories are persisted on the host; you can back them up or inspect directly.

