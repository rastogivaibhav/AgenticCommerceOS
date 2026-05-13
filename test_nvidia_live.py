import requests
import json
import time

SHOPPER_API = "http://localhost:9005/v1/journey"
API_KEY = "dev-key-insecure"

def test_live():
    print("--- Sending message to trigger LLM via NVIDIA NIM ---")
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
    print("Response JSON:")
    print(json.dumps(data, indent=2))
    
    print("\n--- Summary ---")
    print(f"Recommendation Text: {data.get('recommendation', {}).get('recommendation_text', 'N/A')}")
    print(f"Source: {data.get('recommendation', {}).get('source', 'N/A')}")
    if data.get('recommendation', {}).get('source') == 'nvidia_nim':
        print("\nSUCCESS: NVIDIA NIM LLM API is integrated and working!")
    else:
        print("\nFAILED: Source is not nvidia_nim")

if __name__ == "__main__":
    test_live()
