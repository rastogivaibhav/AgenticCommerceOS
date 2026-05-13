import subprocess
import os

PORTS = [8000, 9005, 9006]

def kill_ports():
    print("--- ACOS Process Cleanup ---")
    for port in PORTS:
        try:
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in output.splitlines():
                if "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    print(f"[*] Killing process {pid} listening on port {port}...")
                    os.system(f"taskkill /F /PID {pid}")
        except subprocess.CalledProcessError:
            print(f"[ ] Port {port} is already free.")
    print("--- Cleanup Complete ---")

if __name__ == "__main__":
    kill_ports()
