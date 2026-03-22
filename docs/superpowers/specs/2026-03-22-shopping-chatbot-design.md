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
-- Shopping sessions: manage conversation context and session state
CREATE TABLE shopping_sessions (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- NULL for guests
  conversation_history JSONB NOT NULL DEFAULT '[]',  -- Array of {role, content, timestamp}
  cart_items JSONB NOT NULL DEFAULT '[]',  -- Array of {product_id, qty, price_at_time, name}
  session_preferences JSONB,  -- {inferred_budget, categories, firmness_preference}
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  last_activity TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP,  -- 30 days for guests, NULL for registered users

  CONSTRAINT valid_guest_expiry CHECK (
    customer_id IS NOT NULL OR expires_at IS NOT NULL
  ),
  CONSTRAINT valid_conversation_history CHECK (
    jsonb_typeof(conversation_history) = 'array'
  ),
  CONSTRAINT valid_cart_items CHECK (
    jsonb_typeof(cart_items) = 'array'
  )
);

CREATE INDEX idx_sessions_customer ON shopping_sessions(customer_id);
CREATE INDEX idx_sessions_expires_at ON shopping_sessions(expires_at)
  WHERE expires_at IS NOT NULL;

-- Shopping carts: persistent cart state (optional—can use session.cart_items instead)
CREATE TABLE shopping_carts (
  cart_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES shopping_sessions(session_id) ON DELETE CASCADE,
  customer_id UUID REFERENCES users(id) ON DELETE CASCADE,

  items JSONB NOT NULL DEFAULT '[]',  -- [{product_id, qty, price_at_time, name, image_url}]
  subtotal DECIMAL(19,4) NOT NULL DEFAULT 0.0000,  -- GBP with 4 decimal places
  tax DECIMAL(19,4) NOT NULL DEFAULT 0.0000,
  total DECIMAL(19,4) NOT NULL DEFAULT 0.0000,

  status TEXT NOT NULL DEFAULT 'active',  -- active, abandoned, converted
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  converted_at TIMESTAMP,

  CONSTRAINT valid_items CHECK (jsonb_typeof(items) = 'array'),
  CONSTRAINT valid_amounts CHECK (subtotal >= 0 AND tax >= 0 AND total = subtotal + tax),
  CONSTRAINT valid_status CHECK (status IN ('active', 'abandoned', 'converted')),
  CONSTRAINT valid_conversion_date CHECK (
    (status = 'converted' AND converted_at IS NOT NULL) OR
    (status IN ('active', 'abandoned') AND converted_at IS NULL)
  )
);

CREATE INDEX idx_carts_session ON shopping_carts(session_id);
CREATE INDEX idx_carts_customer ON shopping_carts(customer_id);
CREATE INDEX idx_carts_status ON shopping_carts(status);
CREATE INDEX idx_carts_updated_at ON shopping_carts(updated_at);

-- Shopping orders: immutable snapshot of purchases
CREATE TABLE shopping_orders (
  order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES shopping_sessions(session_id) ON DELETE SET NULL,

  -- Items: snapshot at purchase time (prevents price disputes)
  items JSONB NOT NULL,  -- [{product_id, qty, price_at_purchase, name, image_url}]

  -- Financial snapshot
  subtotal DECIMAL(19,4) NOT NULL,  -- GBP
  tax DECIMAL(19,4) NOT NULL DEFAULT 0.0000,
  total DECIMAL(19,4) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'GBP',

  -- Delivery
  delivery_address JSONB NOT NULL,  -- {street, city, postcode, country}

  -- Payment
  payment_method TEXT NOT NULL,  -- stripe, paypal, etc.
  payment_intent_id VARCHAR(255),  -- Stripe PaymentIntent ID for reconciliation
  payment_status TEXT NOT NULL DEFAULT 'pending',  -- pending, succeeded, failed

  -- Status tracking
  status TEXT NOT NULL DEFAULT 'pending',  -- pending, confirmed, shipped, delivered, cancelled

  -- Timestamps
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  confirmed_at TIMESTAMP,
  shipped_at TIMESTAMP,
  delivered_at TIMESTAMP,
  cancelled_at TIMESTAMP,

  CONSTRAINT valid_items CHECK (jsonb_typeof(items) = 'array' AND jsonb_array_length(items) > 0),
  CONSTRAINT valid_address CHECK (jsonb_typeof(delivery_address) = 'object'),
  CONSTRAINT valid_amounts CHECK (subtotal > 0 AND tax >= 0 AND total = subtotal + tax),
  CONSTRAINT valid_status CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
  CONSTRAINT valid_payment_status CHECK (payment_status IN ('pending', 'succeeded', 'failed')),
  CONSTRAINT valid_status_timestamps CHECK (
    (status = 'confirmed' AND confirmed_at IS NOT NULL) OR
    (status IN ('pending') AND confirmed_at IS NULL)
  )
);

CREATE INDEX idx_orders_customer ON shopping_orders(customer_id);
CREATE INDEX idx_orders_session ON shopping_orders(session_id);
CREATE INDEX idx_orders_status ON shopping_orders(status);
CREATE INDEX idx_orders_created_at ON shopping_orders(created_at);
CREATE INDEX idx_orders_payment_intent ON shopping_orders(payment_intent_id);

-- Training data: product knowledge for LLM context enrichment
CREATE TABLE shopping_training_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id VARCHAR(255) NOT NULL,
  category VARCHAR(100),

  content TEXT NOT NULL,  -- Product info, FAQs, buying guides, recommendations
  embedding VECTOR(1536),  -- OpenAI embeddings (optional—if using semantic search)

  source TEXT,  -- "product_description", "faq", "review", "guide"
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

  CONSTRAINT valid_content CHECK (length(content) > 0)
);

CREATE INDEX idx_training_data_product ON shopping_training_data(product_id);
CREATE INDEX idx_training_data_category ON shopping_training_data(category);
CREATE INDEX idx_training_data_source ON shopping_training_data(source);
-- Vector index for semantic search (pgvector extension)
CREATE INDEX idx_training_data_embedding ON shopping_training_data
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Helper function: calculate cart total
CREATE OR REPLACE FUNCTION calculate_cart_total(
  p_subtotal DECIMAL,
  p_tax_rate DECIMAL DEFAULT 0.20  -- 20% VAT (UK)
) RETURNS DECIMAL AS $$
  SELECT p_subtotal * (1 + p_tax_rate);
$$ LANGUAGE SQL IMMUTABLE;
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

### 5.1 Tool Execution & Retry Strategy

**Tool Timeout Specification:**
```
Tool Type          Timeout   Retries   Backoff Strategy
─────────────────────────────────────────────────────────
search_products    10s       3         exponential: 1s, 2s, 4s
get_product_details 5s       2         exponential: 1s, 2s
add_to_cart        8s        2         exponential: 1s, 2s
check_stock        5s        2         exponential: 1s, 2s
track_order        10s       2         exponential: 1s, 2s
```

**End-to-End Message Timeout:**
- Agent receives message → deadline = now() + 30 seconds
- All tool calls must complete within deadline
- If deadline approaches, agent truncates response and sends partial result

**Retry Logic (Exponential Backoff):**
```python
def call_tool_with_retry(tool_name, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = mcp_server.call_tool(tool_name, params)
            return result
        except ToolTimeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                time.sleep(wait_time)
            else:
                raise ToolFailureError(f"{tool_name} failed after {max_retries} retries")
        except MalformedResponse as e:
            # Don't retry for malformed data—log and fail immediately
            log_error(f"MCP server returned invalid data: {e}")
            raise
```

### 5.2 Scenario Handling

| Scenario | Handling Strategy |
|----------|-------------------|
| **MCP Server Down** | Agent responds: "I'm having trouble accessing our catalog. Please try again in a moment." Fall back to pre-cached product list (max 15 min old). If > 5 min down, send customer SMS/email with link to re-access. |
| **Product No Longer Available** | Agent: "That product is no longer in stock, but we have similar options." Use recommendations engine. |
| **Out of Stock** | Agent: "Back in stock on [date]." Offer to notify customer (store in notification queue). |
| **Invalid Product ID** | Agent: "I couldn't find that product. Let me show you similar items based on your preferences." |
| **Tool Timeout After 3 Retries** | Agent: "I had trouble with that request. Let me try something else." Simplify request or suggest alternative. |
| **Malformed MCP Response** | Log error (alert ops), Agent: "I encountered an unexpected error. Please try again." Don't retry. |
| **Customer Disconnects** | WebSocket closes gracefully. Session persisted. Customer reconnects within 24 hours → resume conversation. |
| **Session Expires (30 days guest)** | Cannot reopen. Direct to new session creation. Offer: "Your old cart is no longer available, but we saved your preferences." |
| **Rate Limit Hit (100 req/min)** | Agent: "I'm getting lots of requests. Your message is queued." Queue and retry with backoff. |
| **Unclear Intent** | Agent asks clarifying question: "Are you looking for mattresses, pillows, or bed frames?" |
| **Cart Item Price Changed** | Agent: "Note: Product X price changed to $399 (was $499). Your cart total is now $Y." Allow re-confirmation. |
| **Payment Failure (Card Declined)** | Agent: "Your card was declined. Please try a different card or payment method." Preserve cart for retry (24 hrs). |
| **Payment Failure (3DS Auth)** | Customer completes authentication on Stripe form. Webhook updates order status. Agent: "Payment confirmed!" |
| **Support Escalation** | Agent: "I'm connecting you with our support team. Please hold..." → Transition chat to support queue (future integration). |

### 5.3 Conversation Context Management

**Context Window Strategy:**
```python
# When building Claude prompt
context_params = {
    "max_messages": 10,  # Last 10 messages
    "token_limit": 4000,  # Rough limit for context
    "max_conversation_age": 24_hours,  # Conversations older than 24h are archived
}

messages_to_include = session.conversation_history[
    -context_params["max_messages"]:
]

# If total tokens > 4000, truncate oldest messages
while estimate_tokens(messages_to_include) > context_params["token_limit"]:
    messages_to_include = messages_to_include[1:]  # Drop oldest

# Optionally summarize truncated messages
if len(session.conversation_history) > context_params["max_messages"]:
    summary = summarize_earlier_messages(
        session.conversation_history[:-context_params["max_messages"]]
    )
    system_prompt += f"\n\nEarlier conversation summary: {summary}"
```

**Behavior on Long Conversations:**
- Keep last 10 messages in full
- Summarize older messages (1-sentence per message)
- Example: "Customer previously asked about firm mattresses, budget ~$500. Showed 3 products. Customer interested in Product A."
- Storage: Store summaries in `session_preferences` for persistence

**Handoff When Conversation Gets Old (>24h):**
- Agent: "I see this conversation is over 24 hours old. Would you like me to remind you what we discussed?"
- Provide 1-line summary of last action (e.g., "You had Mattress A in your cart")

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

**Registered Users:**
- Authenticate with existing ACOS API key (Bearer token)
- Session linked to customer_id
- Can access cart, order history, preferences across sessions
- Can logout (expires session token)

**Guest Users:**
- Generate anonymous session_token (UUID, 128-bit entropy)
- Token valid for 24 hours or until checkout
- Cannot access order history (can only track current order via order_id + email)
- Cart preserved for 30 days (for abandoned cart recovery)

**Cart Access Control:**
```python
# Enforce in all cart-modifying endpoints
def require_cart_ownership(session_id, authenticated_user_id):
    session = db.get_session(session_id)

    # Registered user must own the session
    if authenticated_user_id:
        if session.customer_id != authenticated_user_id:
            raise AuthorizationError("Cannot access other user's cart")

    # Guest: check session token validity
    else:
        if session.expires_at < now():
            raise AuthorizationError("Session expired")
```

**MCP Server Calls:**
- Use server-side authentication (API keys, OAuth, mTLS)
- Never expose MCP credentials to frontend
- Store MCP secrets in environment variables or secrets manager
- Rotate credentials quarterly

### 8.2 Data Protection

**Personally Identifiable Information (PII):**
- **Delivery address:** Encrypted at rest using AES-256 (PostgreSQL pgcrypto or application-level)
- **Email:** Stored as plaintext (necessary for order tracking + compliance)
- **Conversation history:** Flagged for potential PII; sanitized before training data

**Payment:**
- **Never store:** Full card numbers, CVC, bank account details
- **Use Stripe tokenization:** Client-side only, server receives token_id
- **Log:** Only last 4 digits for customer reference
- **Enforce HTTPS:** All payment endpoints require TLS 1.2+

**Training Data:**
- Sanitize product descriptions before storing (remove internal notes, PII)
- Mark sources as public vs. internal
- Embeddings generated from public content only

**Conversation History:**
- Customers (registered only) can request full conversation deletion (GDPR right-to-be-forgotten)
- Implement: `DELETE FROM shopping_sessions WHERE customer_id = $1 AND created_at < $2`
- Guests: Auto-delete after 30 days via scheduled job

### 8.3 Authorization Matrix

| User Type | View Own Cart | View Own Orders | View Other Carts | Create Order | Track Order |
|-----------|---|---|---|---|---|
| **Registered** | ✅ | ✅ | ❌ | ✅ | ✅ (history) |
| **Guest** | ✅ (via token) | ❌ | ❌ | ✅ | ✅ (order_id + email) |
| **Admin** | ✅ | ✅ | ✅ (view only) | ✅ (on behalf) | ✅ |

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

## 9.4 Payment Integration Strategy

### Payment Flow

**Payment Processor:** Stripe (extensible to PayPal, others)

**Flow:**
```
1. Customer initiates checkout → POST /api/shopping/sessions/{id}/checkout
   └─> ACOS creates Stripe PaymentIntent, returns client_secret

2. Frontend collects card details via Stripe Elements
   └─> Never touches card data (PCI compliant)

3. Customer confirms payment → POST /api/shopping/orders/{id}/confirm-payment
   └─> Stripe processes charge, sends webhook to ACOS

4. ACOS receives webhook → POST /api/shopping/webhooks/payment
   └─> Validates signature, updates order status
   └─> Sends confirmation email to customer

5. Agent notifies customer: "Payment confirmed! Order #xyz dispatching..."
```

**Webhook Events:**
```
payment_intent.succeeded:
  - Update order status: "confirmed"
  - Send confirmation email
  - Trigger fulfillment workflow

payment_intent.payment_failed:
  - Update order status: "payment_failed"
  - Notify customer in chat: "Payment declined. Please try again."
  - Preserve cart for retry (24 hours)

charge.refunded:
  - Update order status: "refunded"
  - Send refund confirmation email
```

**3D Secure & SCA Compliance:**
- For card_present: Stripe handles 3DS automatically
- For card_not_present: Stripe requests customer authentication if needed
- Payment confirmation includes SCA status

**Error Handling:**
```python
# In payment confirmation endpoint
try:
    payment_intent = stripe.PaymentIntent.retrieve(payment_id)
    if payment_intent.status == "succeeded":
        order.status = "confirmed"
        order.payment_date = now()
        send_confirmation_email(order)
    elif payment_intent.status == "requires_action":
        return 400, "Payment requires additional authentication"
    else:
        return 400, "Payment failed. Please try again."
except stripe.error.CardError as e:
    return 400, {"code": "CARD_DECLINED", "message": e.user_message}
except stripe.error.RateLimitError:
    return 429, "Too many requests to payment processor"
except stripe.error.APIConnectionError:
    # Retry logic: exponential backoff
    return 503, "Payment service temporarily unavailable"
```

**PCI Compliance:**
- Never log card numbers or CVC
- Use Stripe tokenization (client-side only)
- Store only last 4 digits for customer reference
- All HTTPS (enforce in nginx config)

---

## 9.5 MCP Server Integration Requirements

### Expected MCP Server Capabilities

Your MCP product server **MUST** provide these tools:

| Tool | MCP Server Capability | Required Response | Timeout |
|------|---|---|---|
| `search_products` | Query product catalog by name, category, filters | Array of 5-10 products with {id, name, price, category, rating} | 10s |
| `get_product_details` | Fetch full product info | {id, name, price, specs, images, reviews, guarantee, in_stock} | 5s |
| `get_product_recommendations` | Recommend products based on preferences | Array of 3-5 products ranked by relevance | 10s |
| `check_stock` | Check real-time inventory | {product_id, in_stock, quantity, delivery_estimate} | 5s |

### MCP Server Schema Expectations

**Product Object:**
```json
{
  "product_id": "string (unique)",
  "name": "string",
  "category": "string",
  "price": "number (GBP)",
  "description": "string",
  "specs": [
    {"key": "material", "value": "cotton"},
    {"key": "warranty", "value": "7 years"}
  ],
  "images": [
    {"url": "https://...", "alt": "front view"},
    {"url": "https://...", "alt": "detail view"}
  ],
  "rating": "number (0-5)",
  "review_count": "number",
  "in_stock": "boolean",
  "stock_quantity": "number",
  "tags": ["firm", "hypoallergenic", "eco-friendly"],
  "guide_links": {
    "how_to_choose": "https://...",
    "care_instructions": "https://..."
  }
}
```

### Fallback Strategy

**If MCP Server is Down:**

1. **Cached Products (15-min cache):**
   ```python
   # Check Redis cache before querying MCP
   cached_products = redis.get(f"mcp:search:{query}")
   if cached_products:
       return cached_products  # Use cache
   ```

2. **Agent Graceful Degradation:**
   ```
   Agent: "I'm having trouble accessing our full catalog right now,
           but here are some products we know about:
           - Mattress A ($399)
           - Mattress B ($479)

           Would you like to proceed, or try again in a moment?"
   ```

3. **Read-Only Mode:**
   - Customers can view pre-cached products
   - Cannot add to cart or checkout
   - Agent suggests returning later

4. **Monitoring & Alerts:**
   - Alert if MCP server down > 5 minutes
   - Page on-call engineer immediately
   - Redirect traffic to maintenance page if down > 30 min

### MCP Server SLA

- **Uptime:** 99.5% (monthly)
- **Response time:** p95 < 3 seconds
- **Data freshness:** Inventory updates within 5 minutes

---

## 10. Deployment & Operations

### 10.1 Database Migrations

**On deployment:**
1. Create new tables: shopping_sessions, shopping_carts, shopping_orders, shopping_training_data
2. Add indexes for performance
3. No changes to existing ACOS tables

### 10.2 Configuration & Environment Variables

**Backend Configuration (.env or settings.json):**

```bash
# MCP Product Server Integration
MCP_PRODUCT_SERVER_URL=https://products.example.com/mcp
MCP_PRODUCT_SERVER_API_KEY=<secure_key>
MCP_PRODUCT_SERVER_TIMEOUT_SECONDS=10
MCP_PRODUCT_CACHE_TTL_MINUTES=15  # Cache products for 15 min

# Claude Agent Configuration
SHOPPING_AGENT_MODEL=claude-opus-4-6  # or claude-sonnet-4-6 for faster/cheaper
SHOPPING_AGENT_MAX_TOKENS=1024
SHOPPING_AGENT_TEMPERATURE=0.7  # Conversational tone
SHOPPING_AGENT_TIMEOUT_SECONDS=30  # End-to-end deadline

# Payment Processor Integration
STRIPE_API_KEY=sk_live_...  # or sk_test_... for dev
STRIPE_WEBHOOK_SECRET=whsec_...
PAYMENT_CURRENCY=GBP
PAYMENT_TAX_RATE=0.20  # 20% VAT for UK

# Session Management
SHOPPING_SESSION_EXPIRY_DAYS_GUEST=30
SHOPPING_SESSION_EXPIRY_DAYS_REGISTERED=null  # No expiry
SHOPPING_SESSION_TOKEN_LENGTH=32  # Bytes

# Database
SHOPPING_DB_POOL_SIZE=20
SHOPPING_DB_POOL_TIMEOUT_SECONDS=10
SHOPPING_DB_LOG_SLOW_QUERIES_MS=1000

# Conversation Context
SHOPPING_MAX_CONTEXT_MESSAGES=10
SHOPPING_MAX_CONTEXT_TOKENS=4000
SHOPPING_CONVERSATION_ARCHIVE_AFTER_HOURS=24

# Alerts & Monitoring
SHOPPING_ALERT_LATENCY_THRESHOLD_MS=5000  # 5 sec
SHOPPING_ALERT_ERROR_RATE_THRESHOLD=0.05  # 5%
SHOPPING_ALERT_MCP_DOWNTIME_THRESHOLD_MIN=5
MONITORING_ENABLED=true
PROMETHEUS_EXPORT_PORT=9090

# Feature Flags
SHOPPING_ENABLE_RECOMMENDATIONS=true
SHOPPING_ENABLE_ABANDONED_CART_RECOVERY=true
SHOPPING_ENABLE_PAYMENT_RETRY=true
SHOPPING_ENABLE_ANALYTICS=true
```

**Frontend Configuration (react env):**

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000
VITE_STRIPE_PUBLIC_KEY=pk_test_...
VITE_CHAT_WIDGET_ENABLED=true

# .env.production
VITE_API_BASE_URL=https://api.example.com/api
VITE_WS_URL=wss://api.example.com
VITE_STRIPE_PUBLIC_KEY=pk_live_...
VITE_CHAT_WIDGET_ENABLED=true
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

**Launch Readiness Checklist (Measurable):**

**Functionality:**
- [ ] Chat WebSocket endpoint handles 100+ concurrent connections
- [ ] Agent Executor successfully plans and executes tool calls
- [ ] All 10 shopping tools tested and integrated with MCP
- [ ] Session store persists conversation history, cart, preferences
- [ ] MCP product server integration tested with >1000 real products

**Performance:**
- [ ] Agent response latency p95 < 3 seconds (measured over 1000 requests)
- [ ] Tool execution timeouts enforced (retries up to 3x per tool)
- [ ] WebSocket message round-trip latency p95 < 1 second
- [ ] Database queries optimized (all tables indexed, <100ms queries)

**Testing:**
- [ ] E2E test suite: 100% of critical paths covered (guest flow, registered flow, payment, tracking)
- [ ] Unit tests: 80%+ code coverage (tool execution, session management, cart operations)
- [ ] Load test: 100+ concurrent users, <2% error rate
- [ ] Error scenarios tested: All 15+ edge cases from Section 5.2

**Client Compatibility:**
- [ ] Web: Works on Chrome, Firefox, Safari (desktop)
- [ ] Web: Responsive design (375px mobile, 768px tablet, 1280px+ desktop)
- [ ] Mobile: Works on iOS Safari and Android Chrome (WebView)
- [ ] Accessibility: WCAG 2.1 AA compliance (color contrast, keyboard navigation)

**Security & Compliance:**
- [ ] Authentication: Registered users via API key, guests via session token
- [ ] Authorization: Cart access control enforced (no cross-customer access)
- [ ] Payment: Zero card details logged; Stripe tokenization working
- [ ] GDPR: Customers can request data deletion
- [ ] PCI: Passed security review (no unencrypted PII at rest)

**Business Metrics:**
- [ ] Cart creation rate: >50 carts/day (baseline)
- [ ] Cart-to-order conversion: >30%
- [ ] Average order value: >£50
- [ ] Customer satisfaction: NPS >50 (post-purchase survey)

**Documentation & Operations:**
- [ ] API documentation: All 6+ endpoints documented with examples
- [ ] Deployment guide: Step-by-step setup for dev, staging, production
- [ ] Runbook: Troubleshooting guide for common issues (MCP down, payment failures, etc.)
- [ ] Monitoring: Dashboards set up (latency, errors, conversion funnel)
- [ ] Alerting: Automated alerts for critical issues (MCP > 5 min down, error rate > 5%)

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

## Appendix A: Complete API Contracts

### A.1 REST API Endpoints

#### Create Shopping Session
```
POST /api/shopping/sessions

Request:
{
  "type": "guest" | "authenticated",  # guest or authenticated user
  "customer_id": "uuid"  # required if type="authenticated"
}

Response (201):
{
  "session_id": "uuid",
  "customer_id": "uuid|null",
  "token": "session_token_xyz",  # used for WebSocket auth
  "expires_at": "2026-04-22T10:00:00Z",
  "created_at": "2026-03-22T10:00:00Z"
}

Error (400):
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required field: customer_id"
  }
}
```

#### Get Shopping Session
```
GET /api/shopping/sessions/{session_id}

Headers: Authorization: Bearer {session_token}

Response (200):
{
  "session_id": "uuid",
  "conversation_history": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "cart": {
    "items": [
      {"product_id": "prod_123", "quantity": 2, "price": 399.99, "name": "..."}
    ],
    "subtotal": 799.98,
    "tax": 0,
    "total": 799.98
  },
  "customer_preferences": {
    "inferred_budget": 500,
    "product_categories": ["mattresses"],
    "firmness": "firm"
  }
}

Error (404):
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session has expired or does not exist"
  }
}
```

#### Update Cart Item
```
POST /api/shopping/sessions/{session_id}/cart/items

Request:
{
  "product_id": "prod_123",
  "quantity": 2,  # 0 to remove, >0 to add/update
  "action": "add|update|remove"
}

Response (200):
{
  "item_id": "prod_123",
  "quantity": 2,
  "price": 399.99,
  "cart_total": 879.98,
  "message": "Added 2 x Mattress A to cart"
}

Error (400):
{
  "error": {
    "code": "OUT_OF_STOCK",
    "message": "Only 1 unit available",
    "available": 1
  }
}
```

#### Initiate Checkout
```
POST /api/shopping/sessions/{session_id}/checkout

Request:
{
  "customer_info": {
    "email": "customer@example.com",
    "name": "John Doe"
  },
  "delivery_address": {
    "street": "123 Main St",
    "city": "London",
    "postcode": "SW1A 1AA",
    "country": "UK"
  },
  "payment_method": "stripe"  # or "paypal", etc.
}

Response (200):
{
  "order_id": "uuid",
  "amount": 879.98,
  "currency": "GBP",
  "payment": {
    "method": "stripe",
    "client_secret": "pi_xxxxx",  # For Stripe client-side
    "status": "requires_payment"
  },
  "expires_at": "2026-03-22T10:30:00Z"  # 30 min to complete payment
}

Error (400):
{
  "error": {
    "code": "EMPTY_CART",
    "message": "Cannot checkout with empty cart"
  }
}
```

#### Confirm Payment
```
POST /api/shopping/orders/{order_id}/confirm-payment

Request:
{
  "payment_intent_id": "pi_xxxxx",  # From Stripe
  "payment_token": "tok_xxx"  # Alternative: direct token
}

Response (200):
{
  "order_id": "uuid",
  "status": "confirmed",
  "items": [...],
  "total": 879.98,
  "delivery_estimate": "2026-03-27 - 2026-03-29",
  "confirmation_email": "sent to customer@example.com"
}

Error (400):
{
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Card declined",
    "retry_after": 10  # seconds
  }
}
```

#### Track Order
```
GET /api/shopping/orders/{order_id}?email=customer@example.com

Response (200):
{
  "order_id": "uuid",
  "status": "shipped",  # pending, confirmed, shipped, delivered
  "items": [...],
  "created_at": "2026-03-22T10:00:00Z",
  "shipped_at": "2026-03-24T14:00:00Z",
  "estimated_delivery": "2026-03-27",
  "tracking_url": "https://carrier.com/track/xxxxx",
  "tracking_number": "1Z999AA10123456784"
}

Error (401):
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Email does not match order"
  }
}
```

---

### A.2 WebSocket Message Format

**Client → Server (Chat):**
```json
{
  "type": "message",
  "content": "I need a firm mattress under $500",
  "timestamp": "2026-03-22T10:00:00Z"
}
```

**Server → Client (Streaming Response):**
```json
{
  "type": "response",
  "content": "Let me find firm mattresses under $500 for you...",
  "status": "thinking"
}
```

**Server → Client (With Products):**
```json
{
  "type": "response",
  "content": "Great! I found 3 options:\n• Mattress A: $399 - Firm support, 4.8★\n• Mattress B: $479 - Premium comfort, 4.6★",
  "products": [
    {
      "product_id": "prod_123",
      "name": "Mattress A",
      "price": 399.99,
      "image_url": "https://...",
      "rating": 4.8,
      "reviews_count": 245,
      "in_stock": true
    }
  ],
  "status": "complete"
}
```

**Server → Client (Error):**
```json
{
  "type": "error",
  "error_code": "MCP_SERVER_UNAVAILABLE",
  "message": "I'm having trouble accessing our catalog right now. Please try again in a moment.",
  "status": "error",
  "recovery_hint": "Check back in 30 seconds"
}
```

---

### A.3 Tool Call Format (Internal Agent → Tool Use Layer)

```json
{
  "tool": "search_products",
  "params": {
    "query": "firm mattress",
    "price_max": 500,
    "category": "mattresses",
    "limit": 5,
    "sort_by": "relevance"
  },
  "timeout_seconds": 10,
  "retry_strategy": "exponential_backoff"
}
```

---

### A.4 Standard Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",  # Machine-readable (e.g., OUT_OF_STOCK, SESSION_EXPIRED)
    "message": "Human-readable error message",
    "details": {
      "field": "product_id",  # Optional: which field caused error
      "value": "prod_999",
      "reason": "Product not found in catalog"
    },
    "retry_after": 10  # Optional: seconds to wait before retry
  },
  "timestamp": "2026-03-22T10:00:00Z",
  "request_id": "req_xyz123"  # For debugging
}
```

---

### A.5 Common HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 201 | Resource created (session, order) |
| 400 | Bad request (invalid product_id, empty cart) |
| 401 | Unauthorized (invalid session token, email mismatch) |
| 404 | Not found (session expired, product removed) |
| 429 | Rate limited (100 req/min exceeded) |
| 500 | Internal error (MCP server error, DB error) |
| 503 | Service unavailable (MCP server down) |

---

## Document History

| Version | Date | Author | Status |
|---------|------|--------|--------|
| 1.0 | 2026-03-22 | Design Team | Approved |

