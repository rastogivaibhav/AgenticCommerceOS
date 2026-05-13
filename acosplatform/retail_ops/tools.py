import requests
import os
import json
from typing import Any, Dict, List

RETAIL_API_BASE = "http://localhost:9006"

def catalog_search(query: str = None, category: str = None) -> List[Dict[str, Any]]:
    """Search the real John Lewis catalog via API."""
    params = {"category": category} if category else {}
    try:
        resp = requests.get(f"{RETAIL_API_BASE}/catalog/products", params=params, timeout=2.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Catalog API error: {e}")
        return []

def inventory_check_stock(product_id: str) -> Dict[str, Any]:
    """Check live stock levels in the ERP."""
    try:
        resp = requests.get(f"{RETAIL_API_BASE}/inventory/stock/{product_id}", timeout=2.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {"product_id": product_id, "stock": 0, "status": "unknown"}

def loyalty_get_balance(customer_id: str) -> Dict[str, Any]:
    """Retrieve live loyalty balance from the rewards system."""
    try:
        resp = requests.get(f"{RETAIL_API_BASE}/loyalty/balance/{customer_id}", timeout=2.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {"customer_id": customer_id, "points": 0, "tier": "Standard"}

def orders_create(customer_id: str, items: List[Dict[str, Any]], total: float) -> Dict[str, Any]:
    """Place a real order in the management system."""
    payload = {"customer_id": customer_id, "items": items, "total": total}
    try:
        resp = requests.post(f"{RETAIL_API_BASE}/orders/create", json=payload, timeout=2.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {"status": "failed", "reason": "ERP_CONNECTION_ERROR"}

# Dispatcher for the ACOS Agent Runtime
def execute_retail_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    if tool_name == "catalog.search":
        return catalog_search(arguments.get("query"), arguments.get("category"))
    if tool_name == "inventory.check_stock":
        return inventory_check_stock(arguments.get("product_id"))
    if tool_name == "loyalty.get_balance":
        return loyalty_get_balance(arguments.get("customer_id"))
    if tool_name == "orders.create":
        return orders_create(arguments.get("customer_id"), arguments.get("items"), arguments.get("total"))
    return {"error": f"Tool {tool_name} not implemented in retail_ops_tools"}
