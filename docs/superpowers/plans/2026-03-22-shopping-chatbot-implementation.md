# Shopping Chatbot Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-ready shopping chatbot agent enabling customers to discover products, manage carts, and complete purchases through conversational AI.

**Architecture:** LLM-powered agent integrated into ACOS backend (FastAPI + PostgreSQL), chat via WebSocket, payments via Stripe, product data via MCP servers.

**Tech Stack:** FastAPI, PostgreSQL (pgvector), Claude API, Stripe, React, Playwright, pytest

**Timeline:** 8 weeks solo development across 19 focused tasks

---

## Phase 1: Database Setup (Week 1)

### Task 1: Create Shopping Database Schema

**Files:** `ops_api/migrations/001_create_shopping_tables.sql`

Creates 4 tables:
- shopping_sessions (conversation_history JSONB, cart_items JSONB, expires_at for guests)
- shopping_carts (items JSONB, subtotal, tax, total DECIMAL(19,4), status)
- shopping_orders (items snapshot, payment_intent_id unique, payment_status, order status)
- shopping_training_data (product_id, content TEXT, embedding VECTOR(1536))

All with proper constraints, indexes, UUID PKs.

**Run:** `psql $DATABASE_URL < ops_api/migrations/001_create_shopping_tables.sql`

### Task 2: Create SQLAlchemy Models & Schemas

**Files:**
- `ops_api/models/shopping.py` - ShoppingSession, ShoppingCart, ShoppingOrder, ShoppingTrainingData models
- `ops_api/models/schemas.py` - Pydantic SessionCreateRequest, ChatMessageRequest, CartItemRequest, OrderResponse, ErrorResponse

---

## Phase 2: Backend Foundation (Week 2)

### Task 3: Session Management Service

**File:** `ops_api/services/shopping_sessions.py`

SessionManager class:
- create_session(customer_id: UUID) → ShoppingSession (guest=30d expiry, registered=no expiry)
- get_session(session_id: UUID) → with expiry validation
- add_message(session_id, role, content) → appends to conversation_history
- update_cart(session_id, cart_items) → syncs cart, updates last_activity
- update_preferences(session_id, prefs) → stores inferred preferences

Test: `tests/unit/test_shopping_sessions.py`

### Task 4: Shopping Chat WebSocket Endpoint

**File:** `ops_api/routers/shopping_chat.py`

Endpoint: `WebSocket /ws/shopping-chat/{session_id}`

ConnectionManager class handles active connections.

Flow:
1. WebSocket accept
2. Receive JSON: {type: "message", content: "..."}
3. Get/create session
4. Add user message to history
5. Send "thinking" status
6. Call shopping agent
7. Add assistant response to history
8. Send final response + products

Test: `tests/integration/test_shopping_websocket.py`

---

## Phase 3: Agent & Tools (Weeks 3-4)

### Task 5: Claude Agent Executor

**File:** `ops_api/services/shopping_agent.py`

ShoppingAgent class:
- __init__() → Initialize Anthropic client with SHOPPING_AGENT_MODEL=claude-opus-4-6
- process_message(customer_msg, history, preferences) → Claude API call with tool_use
- System prompt: "You are a friendly shopping assistant. You have access to product tools..."

Returns: {response: str, tool_calls: List, products: List}

Test: `tests/unit/test_shopping_agent.py`

### Task 6: Shopping Tools Layer

**File:** `ops_api/services/shopping_tools.py`

7 tools that call MCP servers:
1. search_products(query, category, price_max, limit=5) → products
2. get_product_details(product_id) → full specs
3. get_recommendations(budget, categories, preferences) → ranked products
4. add_to_cart(product_id, qty) → cart confirmation
5. view_cart() → current items + total
6. remove_from_cart(product_id) → updated cart
7. check_stock(product_id) → in_stock bool, delivery_est

Test: `tests/unit/test_shopping_tools.py`

### Task 7: Tool Executor with Retry Logic

**File:** `ops_api/services/tool_executor.py`

ToolExecutor class:
- execute_tool(tool_name, params, timeout_sec=10) with retry
- Exponential backoff: 1s, 2s, 4s
- Timeout enforcement (tool-specific: 5-10s)
- Malformed response detection
- Partial failure handling

```python
def execute_with_retry(tool, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            return mcp_server.call(tool, params, timeout=...)
        except ToolTimeout:
            if attempt < max_retries - 1:
                sleep(2 ** attempt)
            else:
                raise
```

Test: `tests/unit/test_tool_executor.py`

### Task 8: MCP Product Server Connector

**File:** `ops_api/services/mcp_client.py`

MCPClient class:
- __init__(mcp_server_url, api_key) → Initialize connection
- call_tool(tool_name, params) → JSON-RPC to MCP server
- Redis cache (15-min TTL) for search results
- Fallback to cached products if MCP down
- Alert if > 5 min down

```python
class MCPClient:
    def call_tool(self, tool, params):
        cache_key = f"mcp:{tool}:{hash(params)}"
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached)

        result = self._invoke_mcp(tool, params)
        redis.setex(cache_key, 900, json.dumps(result))  # 15 min
        return result
```

Test: `tests/integration/test_mcp_integration.py`

### Task 9: Cart Management REST Endpoints

**File:** `ops_api/routers/shopping_carts.py`

Endpoints:
- POST /api/shopping/sessions → Create session, return token
- POST /api/shopping/sessions/{id}/cart/items → Add item, return updated cart
- DELETE /api/shopping/sessions/{id}/cart/items/{product_id} → Remove
- GET /api/shopping/sessions/{id}/cart → View current cart

Test: `tests/integration/test_shopping_carts.py`

### Task 10: Order Management Endpoints

**File:** `ops_api/routers/shopping_orders.py`

Endpoints:
- POST /api/shopping/orders → Create from cart (snapshot items)
- GET /api/shopping/orders/{order_id} → Track (with email auth for guests)
- GET /api/shopping/orders → List by customer_id
- POST /api/shopping/orders/{id}/cancel → Cancel order

Test: `tests/integration/test_shopping_orders.py`

---

## Phase 4: Payment Integration (Week 5)

### Task 11: Stripe Payment Service

**File:** `ops_api/services/payment_service.py`

PaymentService class:
- create_payment_intent(order_id, amount, currency) → {client_secret, status}
- confirm_payment(payment_intent_id, token) → {status, order_id}
- handle_webhook_event(event) → Update order status

Error handling:
- CardError → "Card declined"
- RateLimitError → Retry with exponential backoff
- APIConnectionError → Queue for retry

```python
def confirm_payment(payment_id, token):
    try:
        pi = stripe.PaymentIntent.confirm(payment_id, payment_method=token)
        if pi.status == "succeeded":
            order.status = "confirmed"
            send_email(customer, "Order confirmed")
        return pi.status
    except stripe.error.CardError as e:
        return "declined", e.user_message
```

Test: `tests/unit/test_payment_service.py`

### Task 12: Payment Endpoints

**File:** `ops_api/routers/shopping_payments.py`

Endpoints:
- POST /api/shopping/checkout → Create PaymentIntent, return client_secret
- POST /api/shopping/orders/{id}/confirm-payment → Confirm payment

**File:** `ops_api/routers/shopping_webhooks.py`

Endpoint:
- POST /api/shopping/webhooks/payment → Stripe webhook with signature verification

```python
@router.post("/webhooks/payment")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})

    if event["type"] == "payment_intent.succeeded":
        order_id = event["data"]["object"]["metadata"]["order_id"]
        update_order_status(order_id, "confirmed")
```

Test: `tests/integration/test_stripe_webhooks.py`

### Task 13: Payment Webhook Integration

Configure Stripe:
- Webhook URL: https://yourdomain.com/api/shopping/webhooks/payment
- Events: payment_intent.succeeded, payment_intent.payment_failed, charge.refunded
- Sign with webhook secret from Stripe dashboard

---

## Phase 5: Frontend (Week 6)

### Task 14: Shopping Chat Widget

**Files:**
- `src/components/ShoppingChat/ShoppingChat.jsx` - Main component
- `src/components/ShoppingChat/ChatMessage.jsx` - Message display
- `src/components/ShoppingChat/ProductCard.jsx` - Product inline display
- `src/components/ShoppingChat/CartSidebar.jsx` - Cart + checkout
- `src/hooks/useShoppingChat.js` - WebSocket + state management

Features:
- WebSocket connect on mount
- Message input + send
- Display user/assistant messages
- Product cards with "Add to Cart"
- Cart summary with total
- Mobile responsive (Tailwind)
- Error state with retry button

### Task 15: Cart & Checkout Flow

Integrate Stripe.js Elements:
- Delivery address form (street, city, postcode)
- Stripe card element
- Payment button
- Loading state during processing
- Success screen with order confirmation

### Task 16: Order Tracking Page

Display:
- Order list (registered) or current order (guest)
- Status timeline (pending → confirmed → shipped → delivered)
- Tracking URL from MCP
- Estimated delivery date
- Contact support link

---

## Phase 6: Testing & Launch (Week 7-8)

### Task 17: Unit Tests (80%+ coverage)

**Files:** `tests/unit/test_shopping_*.py`

Cover:
- Session creation + expiry
- Tool execution + retries
- Cart calculations (subtotal, tax, total)
- Payment intent creation
- Agent tool calling and response parsing

```bash
pytest tests/unit/ -v --cov=ops_api --cov-report=term-missing
```

Target: >= 80% coverage

### Task 18: Integration Tests

**Files:** `tests/integration/test_shopping_*.py`

Cover:
- Full WebSocket message flow (send → receive)
- MCP tool invocation with real/mock server
- Stripe webhook handling (signature verify, event process)
- Guest session creation → cart → checkout → order
- Registered customer flow (login → browse → checkout)

### Task 19: E2E Tests (Playwright)

**File:** `tests/e2e/test_shopping_flow.spec.js`

Scenarios (80%+ critical paths):
1. Guest flow: Landing → Search "mattress" → Click product → Add to cart → Checkout
2. Registered flow: Login → Browse → Add items → View cart → Checkout
3. Order tracking: View past orders → Click order → See status + tracking
4. Error recovery: Search while MCP down → See fallback products → Add works
5. Mobile: All above on tablet/phone viewport

```bash
npx playwright test tests/e2e/
```

### Task 20: Monitoring & Analytics

Add to dashboard:
- Sessions created (hourly)
- Products searched (top 10)
- Cart additions per session
- Checkout initiations
- Order confirmations
- Conversion rate (carts → orders)

Monitoring:
- API latency (p95 < 3s)
- Error rate (< 5%)
- MCP uptime (alert if > 5 min down)
- WebSocket connections (active count)

### Task 21: Documentation & Launch

Files:
- API docs (Swagger at /docs)
- Deployment guide (Docker, systemd, environment vars)
- Runbook (troubleshooting: MCP down, payment failures, session timeouts)
- User guide (how to chat, checkout, track orders)

Checklist before launch:
- [ ] All 19 tasks completed and committed
- [ ] 80%+ unit test coverage
- [ ] E2E tests passing (all 5 scenarios)
- [ ] p95 latency < 3 seconds (load tested)
- [ ] Security audit passed (no PII logged, HTTPS enforced)
- [ ] Documentation complete
- [ ] Monitoring dashboards live
- [ ] Runbook reviewed by ops team

---

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run dev server
python -m uvicorn ops_api.main:app --reload

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ops_api --cov-report=html

# Format code
black ops_api/ src/
isort ops_api/

# Check types (optional)
mypy ops_api/

# Run E2E tests
npx playwright test tests/e2e/

# Database migrations
psql $DATABASE_URL < ops_api/migrations/001_create_shopping_tables.sql
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `ops_api/migrations/001_create_shopping_tables.sql` | Database schema |
| `ops_api/models/shopping.py` | SQLAlchemy models |
| `ops_api/services/shopping_agent.py` | Claude agent executor |
| `ops_api/services/shopping_tools.py` | Tool definitions |
| `ops_api/services/tool_executor.py` | Retry + timeout logic |
| `ops_api/services/mcp_client.py` | MCP server connector |
| `ops_api/services/payment_service.py` | Stripe integration |
| `ops_api/routers/shopping_chat.py` | WebSocket endpoint |
| `ops_api/routers/shopping_carts.py` | Cart REST endpoints |
| `ops_api/routers/shopping_orders.py` | Order REST endpoints |
| `ops_api/routers/shopping_webhooks.py` | Stripe webhook handler |
| `src/components/ShoppingChat/` | React chat widget |
| `tests/unit/` | Unit test suite |
| `tests/integration/` | Integration tests |
| `tests/e2e/` | Playwright E2E tests |

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.0 | 2026-03-22 | Ready for Implementation |
