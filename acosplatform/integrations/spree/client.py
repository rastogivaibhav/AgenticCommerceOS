import requests
import os
from typing import Any, Dict, List

class SpreeClient:
    """ACOS Bridge for Spree Commerce (API V3)."""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.environ.get("SPREE_BASE_URL", "http://localhost:3000")
        self.api_url = f"{self.base_url}/api/v3/store"
        self.headers = {
            "Content-Type": "application/json",
            "X-Spree-Order-Token": os.environ.get("SPREE_ORDER_TOKEN", "")
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def catalog_search(self, query: str = None, category: str = None) -> List[Dict[str, Any]]:
        """Search products in Spree Storefront."""
        params = {}
        if query:
            params["filter[name_cont]"] = query
        if category:
            params["filter[taxons_name_eq]"] = category
            
        try:
            resp = requests.get(f"{self.api_url}/products", params=params, headers=self.headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            # Transform Spree JSON:API format to ACOS simple format
            products = []
            for item in data.get("data", []):
                attr = item.get("attributes", {})
                products.append({
                    "id": item.get("id"),
                    "name": attr.get("name"),
                    "price": float(attr.get("price")),
                    "currency": attr.get("currency"),
                    "description": attr.get("description"),
                    "slug": attr.get("slug")
                })
            return products
        except Exception as e:
            print(f"Spree Search Error: {e}")
            return []

    def check_stock(self, product_id: str) -> Dict[str, Any]:
        """Check stock for a specific Spree product."""
        try:
            resp = requests.get(f"{self.api_url}/products/{product_id}", headers=self.headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            attr = data.get("data", {}).get("attributes", {})
            # Spree often uses 'in_stock' boolean or stock count
            return {
                "product_id": product_id,
                "in_stock": attr.get("in_stock", True),
                "purchasable": attr.get("purchasable", True),
                "status": "available" if attr.get("in_stock") else "out_of_stock"
            }
        except Exception:
            return {"product_id": product_id, "status": "unknown"}

    def get_order(self, order_number: str) -> Dict[str, Any]:
        """Retrieve order details from Spree."""
        try:
            # Note: Requires user token or order token
            resp = requests.get(f"{self.api_url}/orders/{order_number}", headers=self.headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            attr = data.get("data", {}).get("attributes", {})
            return {
                "order_id": order_number,
                "status": attr.get("state"),
                "total": attr.get("total"),
                "payment_state": attr.get("payment_state"),
                "shipment_state": attr.get("shipment_state")
            }
        except Exception:
            return {"error": "Order not found in Spree"}

# Tool Dispatcher for ACOS
def execute_spree_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    client = SpreeClient()
    if tool_name == "catalog.search":
        return client.catalog_search(arguments.get("query"), arguments.get("category"))
    if tool_name == "inventory.check_stock":
        return client.check_stock(arguments.get("product_id"))
    if tool_name == "orders.get_order":
        return client.get_order(arguments.get("order_id"))
    return {"error": f"Tool {tool_name} not implemented for Spree"}
