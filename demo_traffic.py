import requests
import time
import random

url = 'http://127.0.0.1:9080/v1/journey'
headers = {'X-API-Key': 'dev-key-insecure', 'Content-Type': 'application/json'}

journeys = [
    {'type': 'discovery', 'message': 'looking for a high end gaming laptop', 'tenant_id': 'default', 'customer_id': 'gamer99'},
    {'type': 'purchase', 'message': 'add the rtx 4090 to my cart', 'tenant_id': 'default', 'customer_id': 'gamer99'},
    {'type': 'checkout', 'message': 'checkout and pay', 'tenant_id': 'default', 'customer_id': 'gamer99'},
    {'type': 'service', 'message': 'my laptop screen is flickering, how do I return it?', 'tenant_id': 'brandX', 'customer_id': 'angry_user1'},
    {'type': 'engagement', 'message': 'the customer service was amazing', 'tenant_id': 'default', 'customer_id': 'happy_camper'},
    {'type': 'discovery', 'message': 'cheap wireless earbuds under $50', 'tenant_id': 'default', 'customer_id': 'bargain_hunter'},
    {'type': 'discovery', 'message': 'recommend me a mechanical keyboard', 'tenant_id': 'default', 'customer_id': 'typist22'},
    {'type': 'post_purchase', 'message': 'where is my order?', 'tenant_id': 'brandX', 'customer_id': 'typist22', 'order_id': 'ORD-123'}
]

print('Sending simulated shopper traffic to 127.0.0.1:9080...')
for j in journeys:
    try:
        r = requests.post(url, headers=headers, json=j)
        print(f"Sent {j['type']}: {r.status_code}")
        time.sleep(0.5)
    except Exception as e:
        print(f"Failed: {e}")
        
print('Traffic generation complete! Ops Dashboard should now have data.')
