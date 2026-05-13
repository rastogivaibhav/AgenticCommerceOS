import requests
import os

def test_spree_connection():
    url = "http://localhost:3000/api/v3/store/products"
    print("--- ACOS Spree Live Connectivity Test ---")
    print(f"[*] Attempting to fetch products from Spree API V3...")
    
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        products = data.get("data", [])
        
        print(f"[+] SUCCESS: Connected to Spree API.")
        print(f"[+] Found {len(products)} products in the catalog.")
        
        for p in products:
            attr = p.get("attributes", {})
            print(f"  - {attr.get('name')} (Price: {attr.get('price')} {attr.get('currency')})")
            
    except Exception as e:
        print(f"[!] FAILED: Could not connect to Spree.")
        print(f"    Error: {e}")

if __name__ == "__main__":
    test_spree_connection()
