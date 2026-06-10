import os

# Set environment variables BEFORE importing apps
os.environ["OPS_JWT_SECRET"] = "dev-secret-key-not-secure"
os.environ["ALLOW_INSECURE_DEV_AUTH"] = "1"
os.environ["SHOPPER_API_KEYS"] = "dev-key-insecure"
os.environ["ACOS_PLATFORM_MODE"] = "demo"

import uvicorn
from fastapi.testclient import TestClient
from apps.shopper_api.main import app as shopper_app
from apps.ops_api.main import app as ops_app

def generate_traffic():
    print("Injecting traffic into in-memory store...")
    client = TestClient(shopper_app)
    journeys = [
        {'type': 'discovery', 'message': 'looking for a high end gaming laptop', 'tenant_id': 'default', 'customer_id': 'gamer99'},
        {'type': 'purchase', 'message': 'add the rtx 4090 to my cart', 'tenant_id': 'default', 'customer_id': 'gamer99'},
        {'type': 'checkout', 'message': 'checkout and pay', 'tenant_id': 'default', 'customer_id': 'gamer99'},
        {'type': 'service', 'message': 'how do I return it?', 'tenant_id': 'brandX', 'customer_id': 'angry_user1'},
        {'type': 'engagement', 'message': 'service was amazing', 'tenant_id': 'default', 'customer_id': 'happy'},
        {'type': 'discovery', 'message': 'cheap earbuds under $50', 'tenant_id': 'default', 'customer_id': 'bargain'},
        {'type': 'discovery', 'message': 'recommend a mechanical keyboard', 'tenant_id': 'default', 'customer_id': 'typist22'},
        {'type': 'post_purchase', 'message': 'where is my order?', 'tenant_id': 'brandX', 'customer_id': 'typist22', 'order_id': 'ORD-123'}
    ]
    for j in journeys:
        r = client.post("/v1/journey", json=j, headers={"X-API-Key": "dev-key-insecure"})
        print(f"Sent {j['type']}: HTTP {r.status_code}")
    print("Traffic generation complete.")

if __name__ == "__main__":
    generate_traffic()
    
    print("Starting Ops API on port 9004 with populated in-memory data...")
    uvicorn.run(ops_app, host="0.0.0.0", port=9004, log_level="warning")
