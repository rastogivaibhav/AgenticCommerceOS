import requests
import json
import time

SHOPPER_API = "http://localhost:9005/v1/journey"
OPS_API = "http://localhost:8000/api/northstar"
API_KEY = "dev-key-insecure"

def run_diagnostic():
    print("--- Phase 1: Sending Web Chat Message ---")
    payload = {
        "message": "I need a tuxedo for a winter wedding.",
        "customer_id": "cust_8822",
        "tenant_id": "default"
    }
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    
    resp = requests.post(SHOPPER_API, json=payload, headers=headers)
    if resp.status_code != 200:
        print(f"FAILED: Shopper API returned {resp.status_code}")
        print(resp.text)
        return
    
    data = resp.json()
    # The shopper API doesn't always return the session_id in the top-level result
    # We need to find it in the Northstar sessions list
    print("SUCCESS: Message sent to Shopper API")

    print("\n--- Phase 2: Finding Session ID ---")
    # We'll use the 'studio-proof' endpoint which contains the sessions list
    proof_resp = requests.get(f"{OPS_API}/studio-proof", headers=headers)
    if proof_resp.status_code != 200:
        print(f"FAILED: Ops API proof returned {proof_resp.status_code}")
        return
    
    sessions = proof_resp.json().get("sessions", [])
    session_id = None
    for s in sessions:
        if s.get("customer_id") == "cust_8822":
            session_id = s.get("id")
            break
    
    if not session_id:
        print("FAILED: Could not find session for cust_8822")
        return
    
    print(f"FOUND Session ID: {session_id}")

    print("\n--- Phase 3: Verifying Identity Linkage ---")
    linkage_url = f"{OPS_API}/sessions/{session_id}/identity-linkage"
    linkage_resp = requests.get(linkage_url, headers=headers)
    if linkage_resp.status_code != 200:
        print(f"FAILED: Linkage API returned {linkage_resp.status_code}")
        print(linkage_resp.text)
        return
    
    linkage_data = linkage_resp.json()
    print("SUCCESS: Linkage Data Retrieved")
    print(json.dumps(linkage_data, indent=2))
    
    if "web" in linkage_data.get("linked_identities", {}):
        print("\nPASSED: 'web' identity is correctly linked to the session.")
    else:
        print("\nFAILED: 'web' identity missing from linked identities.")

if __name__ == "__main__":
    run_diagnostic()
