import httpx
import json
import uuid
import time

BASE_URL = "http://localhost:9004"
API_KEY = "dev-key-insecure" # Open by default in demo mode

def send_message(text, channel, channel_user_id, customer_id=None, session_id=None):
    payload = {
        "text": text,
        "channel": channel,
        "channel_user_id": channel_user_id,
        "tenant_id": "default"
    }
    if customer_id:
        payload["customer_id"] = customer_id
    if session_id:
        payload["conversation_session_id"] = session_id
        
    print(f"\n>>> Sending message via {channel.upper()}: '{text}'")
    response = httpx.post(f"{BASE_URL}/api/northstar/messages", json=payload, headers={"X-API-Key": API_KEY})
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    return response.json()

def main():
    print("=== ACOS Omnichannel Cross-Channel Simulation ===")
    
    # 1. Start on WhatsApp
    wa_user_id = "+447700900001"
    wa_result = send_message(
        "I'm looking for a winter wedding outfit under £200, Reading pickup.", 
        "whatsapp", 
        wa_user_id,
        customer_id="cust_8822"
    )
    
    if not wa_result: return
    
    session_id = wa_result["message_envelope"]["conversation_session_id"]
    journey_id = wa_result["message_envelope"]["journey_id"]
    print(f"--- WhatsApp Turn Completed ---")
    print(f"Session ID: {session_id}")
    print(f"Journey ID: {journey_id}")
    print(f"Response: {wa_result['response_text']}")
    
    # Wait a bit to simulate human thinking
    time.sleep(1)
    
    # 2. Pick up on Web
    # We simulate the web app knowing the session (e.g. via login or cookie)
    web_user_id = "web_user_8822"
    web_result = send_message(
        "Do you have any loyalty rewards I can use for this?", 
        "web", 
        web_user_id,
        customer_id="cust_8822",
        session_id=session_id # This is how we link the channels
    )
    
    if not web_result: return
    
    new_session_id = web_result["message_envelope"]["conversation_session_id"]
    new_journey_id = web_result["message_envelope"]["journey_id"]
    
    print(f"\n--- Web Turn Completed ---")
    print(f"Session ID: {new_session_id} (Matches: {new_session_id == session_id})")
    print(f"Journey ID: {new_journey_id} (Matches: {new_journey_id == journey_id})")
    print(f"Response: {web_result['response_text']}")
    
    # 3. Verify Memory Consistency
    # We check if both messages are in the session history
    history_response = httpx.get(f"{BASE_URL}/api/northstar/studio-proof", headers={"X-API-Key": API_KEY})
    if history_response.status_code == 200:
        proof = history_response.json()
        print(f"\n=== Memory Consistency Verification ===")
        print(f"Total Sessions in System: {len(proof['sessions'])}")
        
        # Find our session
        our_session = next((s for s in proof['sessions'] if s['id'] == session_id), None)
        if our_session:
            print(f"Session found in durable store: YES")
            print(f"Channel Identities: {json.dumps(our_session['channel_identities'])}")
            if "whatsapp" in our_session['channel_identities'] and "web" in our_session['channel_identities']:
                print("Cross-channel identity link: YES (WhatsApp & Web both present)")
        
        # Verify Journey
        our_journey = next((j for j in proof['journeys'] if j['id'] == journey_id), None)
        if our_journey:
            print(f"Journey persistence: YES")
            print(f"Journey Status: {our_journey['status']}")
        else:
            print(f"Original Journey {journey_id} not found in proof!")
            print(f"Available journeys: {[j['id'] for j in proof['journeys']]}")

if __name__ == "__main__":
    main()
