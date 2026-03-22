# Shopping Chatbot Agent Design Specification

**Date:** March 22, 2026
**Version:** 1.0
**Status:** Design Approved
**Scope:** Customer-facing conversational shopping agent for grocery and retail products

---

## Executive Summary

This document defines the architecture, components, and integration strategy for a **shopping chatbot agent** - a new feature within ACOS that enables customers to shop conversationally via web and mobile interfaces. The agent is powered by Claude LLM, integrated with customer's MCP product servers, and leverages ACOS's existing authentication, database, and tool infrastructure.

**Key Characteristics:**
- LLM-powered conversational shopping experience
- Real-time product discovery via MCP servers
- Guest and registered customer support
- Cart management and order tracking
- Seamless integration into ACOS core
- Production-grade error handling

---

## 1. System Architecture

### 1.1 Layered Design

The shopping agent is built as a new feature **within ACOS**, reusing core infrastructure:

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND (Web + Mobile)                │
│   Chat Interface + Dashboard + Product Browsing   │
└────────────────────┬────────────────────────────────┘
                     │
         ╔═══════════════════════════════════════════════════════════╗
         ║                    ACOS CORE LAYER                         ║
         ║                  (FastAPI + PostgreSQL)                    ║
         ║                                                             ║
         ║  ┌─────────────────────────────────────────────────────┐  ║
         ║  │  Shopping Agent Feature (NEW)                       │  ║
         ║  │  - Chat WebSocket endpoint                          │  ║
         ║  │  - Agent Executor (Claude-based)                    │  ║
         ║  │  - Tool dispatcher for MCP calls                    │  ║
         ║  └─────────────────────────────────────────────────────┘  ║
         ║                           │                                ║
         ║  ┌────────────────────────┼──────────────────────────┐   ║
         ║  │  Tool Use Layer (existing/enhanced)              │   ║
         ║  │  - Tool registry                                 │   ║
         ║  │  - MCP connector manager                          │   ║
         ║  │  - Tool execution engine                          │   ║
         ║  └────────────────────────┼──────────────────────────┘   ║
         ║  ┌────────────────────────┼──────────────────────────┐   ║
         ║  │  Core Services (existing)                         │   ║
         ║  │  - Authentication/API Keys                        │   ║
         ║  │  - Rate limiting                                  │   ║
         ║  │  - Session management                             │   ║
         ║  │  - Workflow execution engine                      │   ║
         ║  │  - Analytics                                      │   ║
         ║  └────────────────────────┼──────────────────────────┘   ║
         ║  ┌────────────────────────┼──────────────────────────┐   ║
         ║  │  Data Layer (PostgreSQL + optional Redis)        │   ║
         ║  │  - Workflows table       - Sessions table          │   ║
         ║  │  - Experiments table     - Carts table (NEW)      │   ║
         ║  │  - Analytics table       - Orders table (NEW)     │   ║
         ║  │  - Users/API Keys        - Training data (NEW)    │   ║
         ║  └────────────────────────┼──────────────────────────┘   ║
         ║                           │                                ║
         ║  ┌────────────────────────┼──────────────────────────┐   ║
         ║  │  External Integrations (via Tool Layer)           │   ║
         ║  │  - Product MCP Server                             │   ║
         ║  │  - Order/Fulfillment systems                      │   ║
         ║  │  - Payment processors (future)                    │   ║
         ║  └────────────────────────────────────────────────────┘   ║
         ║                                                             ║
         ╚═══════════════════════════════════════════════════════════╝
```

### 1.2 Reused ACOS Components

- **FastAPI framework** - Existing backend serves shopping endpoints
- **PostgreSQL database** - New shopping tables coexist with workflow tables
- **Authentication** - Existing API key + new session-based auth for customers
- **Tool/MCP system** - Shopping tools use same Tool Use infrastructure
- **Rate limiting** - Existing 100 req/min limiter protects agent calls
- **Analytics** - Shopping metrics stored alongside workflow analytics

### 1.3 New Shopping-Specific Components

- **Chat WebSocket endpoint** - Real-time bidirectional messaging
- **Agent Executor** - Claude-based decision maker with tool planning
- **Shopping tools** - Product search, cart, order tracking
- **Session store** - Conversation history + cart state
- **Training data store** - Product knowledge enrichment

---

## 2. Core Components & Responsibilities

### 2.1 Shopping Chat Endpoint

**Endpoint:** `WebSocket /ws/shopping-chat/{session_id}`

**Responsibilities:**
- Accept customer messages (text-based conversations)
- Maintain session state across reconnections
- Manage conversation history for context
- Route messages to Agent Executor
- Stream responses back to client in real-time
- Handle session persistence (30-day expiry for guests, indefinite for registered users)

**Session Data Structure:**
```python
{
  "session_id": "uuid",
  "customer_id": "uuid or null (for guests)",
  "conversation_history": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "cart_items": [
    {"product_id": "x", "quantity": 2, "price": 399.99}
  ],
  "session_preferences": {
    "inferred_budget": 500,
    "product_categories": ["mattresses"],
    "firmness_preference": "firm"
  },
  "created_at": "2026-03-22T10:00:00Z",
  "last_activity": "2026-03-22T10:15:00Z"
}
```

### 2.2 Agent Executor

**Role:** Claude-based intelligent decision maker

**Responsibilities:**
- Parse customer intent from messages
- Plan which tools to invoke based on intent
- Execute tools in appropriate sequence
- Maintain conversation context
- Generate natural, helpful responses
- Handle edge cases and clarifications

**System Prompt Guidance:**
```
You are a friendly, knowledgeable shopping assistant for a grocery and retail
business. You help customers discover products, answer questions, and manage
their shopping carts.

Available capabilities:
- Search our product catalog by name, category, or preference
- Provide detailed product information, specifications, and reviews
- Help customers add items to their cart and manage quantities
- Track their orders and provide delivery updates
- Answer questions about shipping, returns, guarantees
- Make personalized product recommendations

Communication style:
- Friendly and conversational
- Product-focused: quickly identify what customer needs
- Proactive: suggest related products or helpful options
- Clear: explain product features in customer's language
- Honest: admit when you don't know and offer to help find answer

You have access to our product training data which includes detailed information
about all products, customer reviews, FAQs, and recommendations. Use this to
provide knowledgeable assistance.
```

### 2.3 Shopping-Specific Tools

Tools available to Agent Executor via MCP integration:

| Tool | Input | Output | Use Case |
|------|-------|--------|----------|
| `search_products` | query, category, price_max, filters | List of products with details | "Find mattresses under $500" |
| `get_product_details` | product_id | Full specs, images, reviews, guarantee | "Tell me more about product X" |
| `get_product_recommendations` | preferences (dict) | Personalized product list | "What do you recommend for me?" |
| `add_to_cart` | product_id, quantity | Confirmation, updated cart total | "Add 2 to my cart" |
| `view_cart` | (none) | Current items, subtotal, tax, delivery est. | "What's in my cart?" |
| `remove_from_cart` | product_id, quantity | Updated cart, new total | "Remove that from cart" |
| `update_cart_item` | product_id, new_quantity | Confirmation, new total | "Change quantity to 3" |
| `check_stock` | product_id | In stock status, delivery timeline | "Is this in stock?" |
| `get_order_history` | customer_id | List of past orders with status | "Show my orders" |
| `track_order` | order_id | Current status, estimated delivery | "Where's my order?" |

**All tools call MCP product server** - Agent doesn't query database directly; all product/order data flows through customer's MCP servers.

### 2.4 MCP Product Server Integration

**Expected MCP Server Capabilities:**

The customer provides MCP servers that expose:
- **Product Catalog** - Metadata: name, description, price, images, specs, category, SKU
- **Inventory** - Real-time stock levels, location, availability
- **Product Training Data** - Detailed product knowledge, FAQs, recommendations, reviews
- **Order/Fulfillment** - Order creation, status tracking, cancellation
- **Recommendations** - Recommendation engine based on customer preferences

**MCP Implementation:**
- Shopping agent calls Tool Use layer with tool requests
- Tool Use layer invokes MCP connectors (via existing MCP infrastructure)
- MCP servers handle actual product data access and manipulation
- Results returned to Agent Executor for response generation

### 2.5 Session & Cart Storage

**PostgreSQL Schema:**

```sql
-- Shopping sessions: manage conversation context
CREATE TABLE shopping_sessions (
  session_id UUID PRIMARY KEY,
  customer_id UUID REFERENCES users(id) NULL,  -- NULL for guests
  conversation_history JSONB NOT NULL,  -- Array of messages
  cart_items JSONB NOT NULL,  -- Array of {product_id, qty, price, name}
  session_preferences JSONB,  -- Inferred from conversation
  created_at TIMESTAMP DEFAULT NOW(),
  last_activity TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP,  -- 30 days for guests, null for registered
  CONSTRAINT valid_guest_expiry CHECK (
    customer_id IS NOT NULL OR expires_at IS NOT NULL
  )
);

-- Shopping carts: persistent cart state
CREATE TABLE shopping_carts (
  cart_id UUID PRIMARY KEY,
  session_id UUID REFERENCES shopping_sessions(session_id),
  customer_id UUID REFERENCES users(id),
  items JSONB NOT NULL,  -- [{product_id, qty, price, name, image_url}]
  subtotal DECIMAL(12,2),
  tax DECIMAL(12,2),
  total DECIMAL(12,2),
  status TEXT DEFAULT 'active',  -- active, abandoned, converted
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  converted_at TIMESTAMP NULL
);

-- Shopping orders: track customer purchases
CREATE TABLE shopping_orders (
  order_id UUID PRIMARY KEY,
  customer_id UUID REFERENCES users(id),
  session_id UUID REFERENCES shopping_sessions(session_id),
  items JSONB NOT NULL,  -- Snapshot of cart items
  subtotal DECIMAL(12,2),
  tax DECIMAL(12,2),
  total DECIMAL(12,2),
  status TEXT DEFAULT 'pending',  -- pending, confirmed, shipped, delivered
  delivery_address JSONB,  -- {street, city, zip, country}
  created_at TIMESTAMP DEFAULT NOW(),
  confirmed_at TIMESTAMP NULL,
  shipped_at TIMESTAMP NULL,
  delivered_at TIMESTAMP NULL
);

-- Training data: product knowledge for agent enrichment
CREATE TABLE shopping_training_data (
  id UUID PRIMARY KEY,
  product_id VARCHAR(255),
  category VARCHAR(100),
  content TEXT,  -- Product info, FAQs, recommendations
  embedding VECTOR(1536),  -- OpenAI embeddings for semantic search
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_product_id (product_id),
  INDEX idx_embedding ON embedding
);
```

---

## 3. Message Data Flow

**Example Scenario:** Customer says "I need a firm mattress under $500"

### Step-by-Step Flow

```
1. CUSTOMER MESSAGE
   ├─ User types in chat widget (web or mobile)
   └─> WebSocket sends: {
         "type": "message",
         "content": "I need a firm mattress under $500"
       }

2. SESSION LOOKUP & CONTEXT ASSEMBLY
   ├─ Endpoint receives WebSocket message
   ├─ Query shopping_sessions for session_id
   ├─ Retrieve: conversation_history, cart_items, session_preferences
   └─> Load ~10 most recent messages for context window

3. AGENT PREPARATION
   ├─ Build Claude API request with:
   │  ├─ System prompt (assistant role, tools, instructions)
   │  ├─ Training data context (product knowledge from VDB)
   │  ├─ Conversation history (for continuity)
   │  ├─ Current cart state (what customer added)
   │  ├─ Available tools list + schemas
   │  └─ Customer message: "I need a firm mattress under $500"
   └─> Send to Claude API

4. AGENT REASONING & TOOL PLANNING
   ├─ Claude analyzes customer intent
   ├─ Decides tools needed: search_products
   ├─ Plans parameters:
   │  ├─ query: "firm mattress"
   │  ├─ price_max: 500
   │  └─ category: "mattresses"
   └─> Returns: {
         "thinking": "Customer wants firm, budget <$500. Search products.",
         "tool_calls": [{
           "id": "call_1",
           "tool": "search_products",
           "params": {"query": "firm mattress", "price_max": 500}
         }],
         "response_partial": "Let me find firm mattresses under $500..."
       }

5. TOOL EXECUTION
   ├─ Shopping endpoint executes tool_calls
   ├─ Calls Tool Use layer -> MCP connector
   ├─ MCP server returns:
   │  ├─ Product A: {id, name, price: 399, firm: true, rating: 4.8}
   │  ├─ Product B: {id, name, price: 479, firm: true, rating: 4.6}
   │  └─ Product C: {id, name, price: 495, firm: true, rating: 4.7}
   └─> Store results in memory for next step

6. AGENT RESPONSE GENERATION
   ├─ Send tool results back to Claude
   ├─ Claude sees products, generates response:
   │  {
   │    "response": "Great! I found 3 firm mattresses under $500...
   │                 • Mattress A ($399) - Excellent support, highly rated
   │                 • Mattress B ($479) - Premium comfort
   │                 Would you like details on any of these?"
   │  }
   └─> No additional tool calls needed

7. RESPONSE TO CUSTOMER
   ├─ WebSocket sends to client: {
   │    "type": "response",
   │    "content": "Great! I found 3 firm mattresses...",
   │    "products": [
   │      {id, name, price, image, rating, action: "view-details"}
   │    ]
   │  }
   └─> Chat UI displays message + product cards

8. SESSION UPDATE
   ├─ Update shopping_sessions table:
   │  ├─ Append new user/assistant messages to conversation_history
   │  ├─ Update session_preferences: {inferred_budget: 500, firmness: "firm"}
   │  └─ Set last_activity = now()
   └─> Persist for future conversation continuity
```

---

## 4. Customer Journeys

### 4.1 Guest Customer Flow

```
Visit website/app
    ↓
Chat widget opens (anonymous session created)
    ↓
Browse/search products conversationally
    ↓
Add items to cart
    ↓
"Ready to checkout?" → Enter email + delivery address
    ↓
Proceed to payment (external processor)
    ↓
Order confirmation → Option: "Create account for faster checkout next time"
    ↓
Order tracking (guest can track with order_id + email)
```

**Data Retention:** Guest session + cart persisted for 30 days. Guest can access cart via email link.

### 4.2 Registered Customer Flow

```
Log in with email/password (or OAuth)
    ↓
Chat widget opens (session linked to user_id)
    ↓
Conversational shopping
    ↓
"Add to cart" → instant, no checkout needed yet
    ↓
"View my cart" → Shows all items across sessions
    ↓
"Checkout" → Pre-filled with address from account
    ↓
Order confirmation
    ↓
Order history available in account dashboard
    ↓
Customers can resume/re-order from previous conversations
```

**Data Retention:** Sessions and carts persist indefinitely. Customers can browse conversation history.

---

## 5. Error Handling & Edge Cases

| Scenario | Handling Strategy |
|----------|-------------------|
| **MCP Server Down** | Agent responds: "I'm having trouble accessing our catalog. Please try again in a moment." Fall back to pre-cached product list. Rate limit retries to 2x. |
| **Product No Longer Available** | Agent: "That product is no longer in stock, but we have similar options." Suggest alternatives from MCP. |
| **Out of Stock** | Show availability: "Back in stock on [date]." Offer to notify when available. |
| **Invalid Product ID** | Agent: "I couldn't find that product. Let me show you similar items." |
| **Customer Disconnects** | WebSocket closes, session saved. Customer can reconnect and resume conversation. |
| **Rate Limit Hit (100 req/min)** | Agent: "I'm getting lots of requests. Your message is queued." Queue and retry. |
| **Unclear Intent** | Agent asks clarifying question: "Are you looking for mattresses, pillows, or bed frames?" |
| **Guest Timeout (30 days)** | Session expires. New chat creates new session. Old cart abandoned. |
| **Cart Item Price Changed** | Agent updates total: "Note: Product X price changed to $X. Your cart total is now $Y." |
| **Payment Failure** | Agent: "There was an issue processing payment. Please try again or contact support." |
| **Support Escalation** | Agent: "I'm connecting you with our support team..." → Transitions to support queue. |

---

## 6. Integration with Existing ACOS Features

### 6.1 Feature Integration Matrix

| ACOS Feature | Shopping Agent Integration |
|---|---|
| **Authentication** | Reuse existing API key auth for internal APIs. Add session-based token auth for customer chat. |
| **Tool Use System** | Shopping agent's tool calls (search, add_to_cart, etc.) route through existing Tool Use layer and MCP connectors. |
| **Rate Limiting** | Same 100 req/min limiter protects agent endpoints. Shopping calls count toward rate limit. |
| **Analytics** | Shopping metrics (searches, conversions, avg order value) stored in existing analytics tables. Dashboards extended with shopping metrics. |
| **Database** | Shopping tables (sessions, carts, orders, training_data) coexist in same PostgreSQL instance as workflows, experiments. |
| **Workflows** | Future: Complex multi-step orders built as workflows (e.g., auto-reorder subscription, returns processing). |
| **Experiments** | Future: A/B test agent responses, recommendation algorithms, chat UI variations. |

### 6.2 No Breaking Changes

- Shopping agent is **additive only** - doesn't modify existing ACOS code
- Uses existing FastAPI router pattern
- Shares PostgreSQL but on separate tables with prefixes
- Reuses authentication middleware with new session token support
- Tool layer enhancement supports shopping tools without breaking workflow tools

---

## 7. Frontend Chat Interface

### 7.1 Web Component Requirements

**Location:** New React component in ACOS frontend (e.g., `src/components/ShoppingChat.jsx`)

**Features:**
- Chat input box (text-only for MVP)
- Message history (scrollable)
- Product cards displayed inline (image, name, price, rating, "Add to Cart")
- Cart sidebar showing current items + total
- Typing indicators ("Agent is typing...")
- Connection status indicator
- Error messages for network/system issues
- Responsive: works on desktop (1280px+)

**UI Framework:** Reuse existing Tailwind + shadcn/ui components

### 7.2 Mobile App Component Requirements

**Options:**
- A) React Native component (if you have native app)
- B) WebView wrapper around React web component
- C) Native iOS/Android implementation (future)

**For MVP:** Option B (WebView) - reuse web component logic

### 7.3 Authentication in Chat Widget

**Registered users:**
```javascript
// Chat widget receives user context
<ShoppingChat
  customerId={user.id}
  apiKey={user.apiKey}  // Existing ACOS key
/>
```

**Guest users:**
```javascript
// Chat widget creates anonymous session
<ShoppingChat
  sessionId={generateUUID()}  // New session
  isGuest={true}
/>
```

---

## 8. Security Considerations

### 8.1 Authentication & Authorization

- **Registered users:** Authenticate with existing ACOS API key
- **Guest users:** Session tokens (short-lived, scoped to shopping only)
- **MCP server calls:** Use server-side auth (API keys, OAuth) - never expose to client
- **Cart access:** Customers can only view/modify their own carts

### 8.2 Data Protection

- **PII:** Delivery address encrypted at rest in PostgreSQL
- **Payment:** Never handle credit cards - use external payment processor
- **Training data:** Product information sanitized before storing
- **Conversation history:** Customers can request deletion (GDPR compliance)

### 8.3 Rate Limiting & Abuse Prevention

- Existing 100 req/min limiter applies to shopping endpoints
- Additional per-session limits: max 50 messages/hour to prevent spam
- MCP server calls rate-limited per-tool
- Bot detection: Escalate suspicious patterns to support

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Coverage areas:**
- Agent intent classification (recognize different shopping requests)
- Tool execution (search, add to cart, view cart)
- Session persistence (save/load conversation)
- Message formatting (ensure responses render correctly)

**Test framework:** pytest + mock MCP server

### 9.2 Integration Tests

**Coverage areas:**
- End-to-end: Message → Tool execution → Response
- MCP server integration (mock and real)
- Cart operations (add, remove, update, checkout)
- Guest vs. registered flows
- Session expiry and cleanup

**Test framework:** pytest + Docker containerized test database

### 9.3 E2E Tests (Playwright)

**Scenarios:**
1. Guest customer: Browse → Search → Add to cart → Checkout
2. Registered customer: Resume previous conversation → Add items → Checkout
3. Error scenarios: MCP down, invalid product, network failure
4. Long conversations: Multi-turn shopping assistance
5. Mobile responsiveness: Chat on tablet and phone

**Test framework:** Playwright (existing test suite extended)

**Target coverage:** 80% of critical paths

---

## 10. Deployment & Operations

### 10.1 Database Migrations

**On deployment:**
1. Create new tables: shopping_sessions, shopping_carts, shopping_orders, shopping_training_data
2. Add indexes for performance
3. No changes to existing ACOS tables

### 10.2 Configuration

**Environment variables:**
```bash
# MCP Product Server
MCP_PRODUCT_SERVER_URL=<endpoint>
MCP_PRODUCT_SERVER_API_KEY=<key>

# Chat agent
SHOPPING_AGENT_MODEL=claude-opus-4-6
SHOPPING_AGENT_MAX_TOKENS=1024

# Session storage
SHOPPING_SESSION_EXPIRY_DAYS=30
SHOPPING_CART_RECOVERY_ENABLED=true

# Analytics
SHOPPING_ANALYTICS_ENABLED=true
```

### 10.3 Monitoring & Alerting

**Metrics to track:**
- Chat session count (concurrent + daily)
- Message latency (p50, p95, p99)
- Tool execution success rate
- MCP server availability
- Cart conversion rate (carts → orders)
- Error rates by type

**Alerts:**
- MCP server down (immediate)
- Agent latency > 5s (threshold)
- Conversion rate drop > 10% (daily check)

---

## 11. Success Criteria

**Launch readiness checklist:**

- [ ] All 4 component sections functional: Chat endpoint, Agent executor, Tools, Session store
- [ ] MCP product server integration tested with real data
- [ ] E2E tests pass (80%+ critical paths)
- [ ] Chat works on web (desktop + responsive)
- [ ] Chat works on mobile (app or WebView)
- [ ] Guest + registered customer flows working
- [ ] Error handling for all 12+ edge cases
- [ ] Rate limiting prevents abuse
- [ ] Analytics dashboard showing shopping metrics
- [ ] Documentation: API docs, user guide, troubleshooting

---

## 12. Timeline & Phases

**Phase 1 (Weeks 1-2): Foundation**
- Set up database schema
- Implement chat WebSocket endpoint
- Basic session management
- Mock MCP server for testing

**Phase 2 (Weeks 3-4): Agent & Tools**
- Claude agent executor with system prompt
- Shopping tools (search, cart, order tracking)
- Real MCP server integration
- Training data store setup

**Phase 3 (Weeks 5-6): Frontend & Testing**
- Chat widget component (web)
- Mobile integration (WebView)
- E2E test suite
- Error handling hardening

**Phase 4 (Weeks 7-8): Polish & Launch**
- Analytics dashboard
- Monitoring & alerting setup
- Documentation
- Beta testing with real data
- Launch to production

---

## Appendix: Example API Contracts

### WebSocket Message Format

**Client → Server:**
```json
{
  "type": "message",
  "content": "I need a firm mattress under $500",
  "timestamp": "2026-03-22T10:00:00Z"
}
```

**Server → Client (streaming):**
```json
{
  "type": "response",
  "content": "Let me find firm mattresses under $500 for you...",
  "status": "thinking"
}
```

Then:
```json
{
  "type": "response",
  "content": "Great! I found 3 options:\n• Mattress A: $399\n• Mattress B: $479",
  "products": [
    {
      "id": "prod_123",
      "name": "Mattress A",
      "price": 399,
      "image": "https://...",
      "rating": 4.8,
      "action": "add-to-cart"
    }
  ],
  "status": "complete"
}
```

### Tool Call Format (Internal)

```json
{
  "tool": "search_products",
  "params": {
    "query": "firm mattress",
    "price_max": 500,
    "limit": 5
  }
}
```

---

## Document History

| Version | Date | Author | Status |
|---------|------|--------|--------|
| 1.0 | 2026-03-22 | Design Team | Approved |

