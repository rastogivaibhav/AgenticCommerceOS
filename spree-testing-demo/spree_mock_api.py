from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI(title="Spree Commerce V3 Mock API")

# Mock Data in Spree JSON:API Format
PRODUCTS = {
    "data": [
        {
            "id": "1",
            "type": "product",
            "attributes": {
                "name": "Spree T-Shirt",
                "description": "Premium cotton t-shirt with Spree logo.",
                "price": "25.00",
                "currency": "USD",
                "slug": "spree-t-shirt",
                "in_stock": True,
                "purchasable": True
            }
        },
        {
            "id": "2",
            "type": "product",
            "attributes": {
                "name": "ACOS Hoodie",
                "description": "Agentic Commerce OS limited edition hoodie.",
                "price": "55.00",
                "currency": "USD",
                "slug": "acos-hoodie",
                "in_stock": True,
                "purchasable": True
            }
        }
    ]
}

@app.get("/api/v3/store/products")
def get_products(request: Request):
    # Support basic filtering
    query = request.query_params.get("filter[name_cont]", "").lower()
    if query:
        filtered = [p for p in PRODUCTS["data"] if query in p["attributes"]["name"].lower()]
        return {"data": filtered}
    return PRODUCTS

@app.get("/api/v3/store/products/{slug}")
def get_product(slug: str):
    product = next((p for p in PRODUCTS["data"] if p["attributes"]["slug"] == slug), None)
    if not product:
        return JSONResponse(status_code=404, content={"error": "Product not found"})
    return {"data": product}

@app.get("/api/v3/store/orders/{number}")
def get_order(number: str):
    return {
        "data": {
            "id": number,
            "type": "order",
            "attributes": {
                "number": number,
                "state": "complete",
                "payment_state": "paid",
                "shipment_state": "shipped",
                "total": "80.00",
                "currency": "USD"
            }
        }
    }

@app.get("/")
def read_root():
    return {
        "name": "Spree Commerce Mock API",
        "version": "V3 (Simulator)",
        "status": "online",
        "endpoints": ["/api/v3/store/products", "/api/v3/store/orders/{id}"]
    }

@app.get("/admin")
def read_admin():
    return {
        "message": "Spree Admin Panel (Mock)",
        "users": [{"id": 1, "email": "admin@spree.com", "api_key": "spree_api_key_mock_123"}],
        "note": "Use this API Key in your ACOS configuration."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
