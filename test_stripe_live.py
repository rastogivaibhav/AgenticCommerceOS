import os
import requests

def test_stripe_connection():
    key = os.environ.get("STRIPE_SECRET_KEY", "MISSING_KEY")
    print("--- ACOS Stripe Live Connectivity Test ---")
    print(f"[*] Attempting to fetch customers from Stripe Sandbox...")
    
    try:
        resp = requests.get(
            "https://api.stripe.com/v1/customers",
            auth=(key, ""),
            params={"limit": 5},
            timeout=10
        )
        resp.raise_for_status()
        customers = resp.json().get("data", [])
        
        print(f"[+] SUCCESS: Connected to Stripe Sandbox.")
        print(f"[+] Found {len(customers)} customers in your sandbox.")
        
        for c in customers:
            print(f"  - Customer: {c.get('email') or 'No Email'} (ID: {c.get('id')})")
            
    except Exception as e:
        print(f"[!] FAILED: Could not connect to Stripe.")
        print(f"    Error: {e}")

if __name__ == "__main__":
    test_stripe_connection()
