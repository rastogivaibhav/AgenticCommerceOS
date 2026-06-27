import os
import requests

def list_nvidia_models():
    api_key = "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"
    url = "https://integrate.api.nvidia.com/v1/models"
    
    print("--- ACOS NVIDIA NIM Model Discovery ---")
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        models = data.get("data", [])
        
        print(f"[+] Found {len(models)} models available for your key.")
        for m in models[:10]:
            print(f"  - {m.get('id')}")
            
    except Exception as e:
        print(f"[!] FAILED: {e}")

if __name__ == "__main__":
    list_nvidia_models()
