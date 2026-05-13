import subprocess
import time
import os
import sys
import socket

# Configuration
ENV_VARS = {
    "APP_VERSION": "1.0.0",
    "OPS_ENVIRONMENT": "dev",
    "OPS_JWT_SECRET": "acos_master_secret_2026_pilot",
    "ALLOW_INSECURE_DEV_AUTH": "1",
    "ALLOWED_ORIGINS": "http://localhost:8000,http://localhost:5173,http://localhost:3000",
}

SERVICES = [
    {
        "name": "Ops API (Control Plane)",
        "command": [sys.executable, "-m", "uvicorn", "apps.ops_api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        "port": 8000
    },
    {
        "name": "Shopper API (Messaging)",
        "command": [sys.executable, "-m", "uvicorn", "apps.shopper_api.main:app", "--host", "0.0.0.0", "--port", "9005"],
        "port": 9005
    },
    {
        "name": "Retail Mock API (ERP/OMS)",
        "command": [sys.executable, "-m", "uvicorn", "apps.retail_mock_api.main:app", "--host", "0.0.0.0", "--port", "9006"],
        "port": 9006
    }
]

def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_suite():
    print("--- ACOS High-Fidelity Demo Suite Initializing ---")
    
    # Merge env vars
    os_env = os.environ.copy()
    
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        k, v = line.split("=", 1)
                        os_env[k.strip()] = v.strip()
                    except ValueError:
                        pass

    os_env.update(ENV_VARS)
    
    processes = []
    
    for service in SERVICES:
        if is_port_open(service['port']):
            print(f"[!] Port {service['port']} is already in use. Skipping {service['name']}.")
            continue
            
        print(f"[*] Starting {service['name']} on port {service['port']}...")
        log_file = open(f"{service['name'].replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').lower()}.log", "w")
        proc = subprocess.Popen(
            service['command'],
            env=os_env,
            stdout=log_file,
            stderr=log_file
        )
        processes.append((service, proc))
    
    print("\n[*] Waiting for services to stabilize (Health Checks)...")
    max_retries = 10
    while max_retries > 0:
        all_ready = True
        for service in SERVICES:
            if not is_port_open(service['port']):
                all_ready = False
                break
        
        if all_ready:
            break
        
        time.sleep(2)
        max_retries -= 1
        print(f"  . Still waiting ({max_retries} attempts left)...")

    if max_retries == 0:
        print("\n[!] WARNING: Some services failed to start in time.")
    else:
        print("\n[+] SUCCESS: All High-Fidelity components are LIVE!")

    print("\n--- DEMO ENTRY POINTS ---")
    print("1. John Lewis Web Experience:  http://localhost:8000/customer-chat")
    print("2. ACOS Ops Control Plane:     http://localhost:8000/ui")
    print("3. Retail ERP Documentation:   http://localhost:9006/docs")
    print("4. A2A Orchestration Traces:   http://localhost:8000/ui/a2a-trace")
    print("\nKeep this terminal open to maintain the services. Press Ctrl+C to terminate the suite.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down ACOS Demo Suite...")
        for service, proc in processes:
            print(f"  - Stopping {service['name']}...")
            proc.terminate()
        print("[+] Done.")

if __name__ == "__main__":
    run_suite()
