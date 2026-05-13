TOOLS = [
    {"name": "catalog.search", "description": "Search retail catalog.", "protocol": "native"},
    {"name": "catalog.get_product", "description": "Get product detail.", "protocol": "native"},
    {"name": "inventory.check_stock", "description": "Check stock for product/location.", "protocol": "native"},
    {"name": "pricing.calculate", "description": "Calculate basket price and budget fit.", "protocol": "native"},
    {"name": "promotions.find_offers", "description": "Find eligible retail offers.", "protocol": "native"},
    {"name": "orders.get_order", "description": "Lookup order state.", "protocol": "native"},
    {"name": "orders.track_order", "description": "Track order state.", "protocol": "native"},
    {"name": "returns.check_eligibility", "description": "Check return eligibility.", "protocol": "native"},
    {"name": "returns.create_return", "description": "Create a governed return request.", "protocol": "native"},
    {"name": "loyalty.get_balance", "description": "Lookup loyalty balance.", "protocol": "native"},
    {"name": "case.create", "description": "Create service case/handoff.", "protocol": "native"},
]
def list_tools() -> list[dict]:
    return TOOLS.copy()
