from fastapi import FastAPI, HTTPException, Body
from typing import List, Dict, Any
import uuid

app = FastAPI(title="John Lewis ERP Mock API")

# High-Fidelity Mock Data: Nursery Category
PRODUCTS = [
    {
        "id": "prod_nursery_001",
        "name": "Anyday Elementary Cot Bed",
        "description": "FSC-certified pine cot bed, perfect for small nurseries.",
        "price": 150.00,
        "category": "Nursery Furniture",
        "tags": ["eco-friendly", "small-space", "best-seller"],
        "stock": 45
    },
    {
        "id": "prod_nursery_002",
        "name": "West Elm x PBT Mid-Century Crib",
        "description": "Stylish, sustainable acorn-finish crib.",
        "price": 699.00,
        "category": "Nursery Furniture",
        "tags": ["premium", "mid-century", "sustainable"],
        "stock": 12
    },
    {
        "id": "prod_nursery_003",
        "name": "SnuzPod 4 Bedside Crib",
        "description": "Breathable bedside crib for newborn safety.",
        "price": 199.00,
        "category": "Newborn Essentials",
        "tags": ["safety", "breathable", "portable"],
        "stock": 88
    }
]

LOYALTY_ACCOUNTS = {
    "cust_8822": {"points": 5200, "tier": "Gold", "balance_gbp": 52.00}
}

ORDERS = []

@app.get("/catalog/products")
def get_products(category: str = None):
    if category:
        return [p for p in PRODUCTS if p["category"].lower() == category.lower()]
    return PRODUCTS

@app.get("/inventory/stock/{product_id}")
def check_stock(product_id: str):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product_id": product_id, "stock": product["stock"], "status": "in_stock" if product["stock"] > 0 else "out_of_stock"}

@app.get("/loyalty/balance/{customer_id}")
def get_loyalty(customer_id: str):
    account = LOYALTY_ACCOUNTS.get(customer_id)
    if not account:
        return {"customer_id": customer_id, "points": 0, "tier": "Standard", "balance_gbp": 0.00}
    return account

@app.post("/orders/create")
def create_order(payload: Dict[str, Any] = Body(...)):
    order_id = f"JL-{uuid.uuid4().hex[:8].upper()}"
    order = {
        "order_id": order_id,
        "status": "confirmed",
        "items": payload.get("items", []),
        "total": payload.get("total", 0.0),
        "customer_id": payload.get("customer_id")
    }
    ORDERS.append(order)
    return order

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9006)
