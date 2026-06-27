import os
import sys

# ACOS-Spree Setup Script
# Use this to configure ACOS to talk to your local Spree instance

SPREE_CONFIG = {
    "SPREE_BASE_URL": "http://localhost:3000",
    "SPREE_API_KEY": "your_spree_api_key_here",
    "SPREE_ORDER_TOKEN": "optional_order_token",
    "STRIPE_SECRET_KEY": os.environ.get("STRIPE_SECRET_KEY", "MISSING"),
    "STRIPE_PUBLISHABLE_KEY": os.environ.get("STRIPE_PUBLISHABLE_KEY", "MISSING"),
    "ACOS_RETAIL_PROVIDER": "spree"
}

def setup_spree_env():
    print("--- Configuring ACOS for Spree Commerce ---")
    for k, v in SPREE_CONFIG.items():
        print(f"  [SET] {k}={v}")
        os.environ[k] = v
    
    # Update the ACOS .env file if it exists
    env_path = ".env.spree"
    with open(env_path, "w") as f:
        for k, v in SPREE_CONFIG.items():
            f.write(f"{k}={v}\n")
    print(f"\n[+] Created {env_path} for persistence.")
    print("\nNext Steps:")
    print("1. Update the .env.spree with your real Spree API Key.")
    print("2. Run 'python run_demo_suite.py' (Make sure SPREE_BASE_URL is reachable).")
    print("3. ACOS Agents will now use Spree V3 API for catalog and orders.")

if __name__ == "__main__":
    setup_spree_env()
