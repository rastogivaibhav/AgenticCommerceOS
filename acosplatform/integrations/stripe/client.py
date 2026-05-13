import requests
import os
from typing import Any, Dict, List

class StripeClient:
    """ACOS Bridge for Stripe API (REST)."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("STRIPE_SECRET_KEY", "")
        self.base_url = "https://api.stripe.com/v1"
        self.auth = (self.api_key, "")

    def get_payment_intent(self, pi_id: str) -> Dict[str, Any]:
        """Fetch a payment intent to verify its status."""
        try:
            resp = requests.get(f"{self.base_url}/payment_intents/{pi_id}", auth=self.auth, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Stripe get_payment_intent Error: {e}")
            return {"error": str(e)}

    def create_refund(self, charge_id: str, amount: int = None) -> Dict[str, Any]:
        """Create a refund for a specific charge."""
        data = {"charge": charge_id}
        if amount:
            data["amount"] = amount
            
        try:
            resp = requests.post(f"{self.base_url}/refunds", data=data, auth=self.auth, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Stripe Refund Error: {e}")
            return {"error": str(e)}

    def list_customers(self, email: str = None) -> List[Dict[str, Any]]:
        """List customers, optionally filtered by email."""
        params = {"limit": 3}
        if email:
            params["email"] = email
            
        try:
            resp = requests.get(f"{self.base_url}/customers", params=params, auth=self.auth, timeout=5)
            resp.raise_for_status()
            return resp.json().get("data", [])
        except Exception:
            return []

# Tool Dispatcher for ACOS
def execute_stripe_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    client = StripeClient()
    if tool_name == "payments.get_intent":
        return client.get_payment_intent(arguments.get("payment_intent_id"))
    if tool_name == "payments.refund":
        return client.create_refund(arguments.get("charge_id"), arguments.get("amount"))
    if tool_name == "payments.find_customer":
        return client.list_customers(arguments.get("email"))
    return {"error": f"Tool {tool_name} not implemented for Stripe"}
