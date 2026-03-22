-- =============================================================================
-- Shopping Chatbot Database Schema Migration
-- Created: 2026-03-22
-- Purpose: Foundation for shopping chatbot with session management, cart,
--          orders, and product knowledge enrichment
-- =============================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- TABLE 1: shopping_sessions
-- Purpose: Manage conversation context for both guest and registered users
-- Stores conversation history, cart items, and user preferences for each session
-- =============================================================================

CREATE TABLE IF NOT EXISTS shopping_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    cart_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    session_preferences JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,

    -- Constraints: For guests, session must have expiry; registered users can have null expiry
    CONSTRAINT valid_guest_expiry CHECK (
        customer_id IS NOT NULL OR expires_at IS NOT NULL
    ),

    -- Validate conversation_history is an array
    CONSTRAINT conversation_history_is_array CHECK (
        jsonb_typeof(conversation_history) = 'array'
    ),

    -- Validate cart_items is an array
    CONSTRAINT cart_items_is_array CHECK (
        jsonb_typeof(cart_items) = 'array'
    )
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_sessions_customer
    ON shopping_sessions(customer_id)
    WHERE customer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
    ON shopping_sessions(expires_at)
    WHERE expires_at IS NOT NULL;

-- =============================================================================
-- TABLE 2: shopping_carts
-- Purpose: Persistent cart state with financial calculations
-- Maintains audit trail of cart state changes (active, abandoned, converted)
-- =============================================================================

CREATE TABLE IF NOT EXISTS shopping_carts (
    cart_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES shopping_sessions(session_id) ON DELETE CASCADE,
    customer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    subtotal DECIMAL(19,4) NOT NULL DEFAULT 0.0000,
    tax DECIMAL(19,4) NOT NULL DEFAULT 0.0000,
    total DECIMAL(19,4) NOT NULL DEFAULT 0.0000,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    converted_at TIMESTAMP,

    -- Validate status values
    CONSTRAINT valid_cart_status CHECK (
        status IN ('active', 'abandoned', 'converted')
    ),

    -- Validate cart items is an array
    CONSTRAINT cart_items_is_array CHECK (
        jsonb_typeof(items) = 'array'
    ),

    -- Validate financial amounts (total = subtotal + tax)
    CONSTRAINT valid_cart_totals CHECK (
        total = subtotal + tax
    ),

    -- Validate amounts are not negative
    CONSTRAINT non_negative_subtotal CHECK (subtotal >= 0),
    CONSTRAINT non_negative_tax CHECK (tax >= 0),
    CONSTRAINT non_negative_total CHECK (total >= 0)
);

-- Indexes for cart queries and analytics
CREATE INDEX IF NOT EXISTS idx_carts_session
    ON shopping_carts(session_id);

CREATE INDEX IF NOT EXISTS idx_carts_customer
    ON shopping_carts(customer_id)
    WHERE customer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_carts_status
    ON shopping_carts(status);

CREATE INDEX IF NOT EXISTS idx_carts_updated_at
    ON shopping_carts(updated_at);

-- =============================================================================
-- TABLE 3: shopping_orders
-- Purpose: Order snapshots with pricing and payment tracking
-- Immutable order record for audit trail and payment processing
-- =============================================================================

CREATE TABLE IF NOT EXISTS shopping_orders (
    order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES shopping_sessions(session_id) ON DELETE SET NULL,
    items JSONB NOT NULL,
    subtotal DECIMAL(19,4) NOT NULL,
    tax DECIMAL(19,4) NOT NULL,
    total DECIMAL(19,4) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'GBP',
    delivery_address JSONB,
    payment_method TEXT,
    payment_intent_id VARCHAR(255) UNIQUE,
    payment_status TEXT NOT NULL DEFAULT 'pending',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMP,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cancelled_at TIMESTAMP,

    -- Validate items is an array (snapshot, never modify)
    CONSTRAINT items_is_array CHECK (
        jsonb_typeof(items) = 'array'
    ),

    -- Validate financial amounts
    CONSTRAINT valid_order_totals CHECK (
        total = subtotal + tax
    ),

    -- Validate subtotal is positive
    CONSTRAINT positive_subtotal CHECK (
        subtotal > 0
    ),

    -- Validate amounts are not negative
    CONSTRAINT non_negative_tax_order CHECK (tax >= 0),
    CONSTRAINT non_negative_total_order CHECK (total >= 0),

    -- Validate payment status values
    CONSTRAINT valid_payment_status CHECK (
        payment_status IN ('pending', 'succeeded', 'failed')
    ),

    -- Validate order status values
    CONSTRAINT valid_order_status CHECK (
        status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')
    ),

    -- Validate delivery address is an object if present
    CONSTRAINT delivery_address_is_object CHECK (
        delivery_address IS NULL OR jsonb_typeof(delivery_address) = 'object'
    )
);

-- Indexes for order queries and tracking
CREATE INDEX IF NOT EXISTS idx_orders_customer
    ON shopping_orders(customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON shopping_orders(status);

CREATE INDEX IF NOT EXISTS idx_orders_created_at
    ON shopping_orders(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_payment_intent
    ON shopping_orders(payment_intent_id)
    WHERE payment_intent_id IS NOT NULL;

-- =============================================================================
-- TABLE 4: shopping_training_data
-- Purpose: Product knowledge for agent enrichment
-- Stores product information, FAQs, and embeddings for semantic search
-- =============================================================================

CREATE TABLE IF NOT EXISTS shopping_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    content TEXT NOT NULL,
    embedding vector(1536),
    source TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Validate source values
    CONSTRAINT valid_training_source CHECK (
        source IN ('product_description', 'faq', 'review', 'guide')
    )
);

-- Indexes for product knowledge queries
CREATE INDEX IF NOT EXISTS idx_training_data_product
    ON shopping_training_data(product_id);

CREATE INDEX IF NOT EXISTS idx_training_data_category
    ON shopping_training_data(category)
    WHERE category IS NOT NULL;

-- Vector similarity index for semantic search (pgvector)
CREATE INDEX IF NOT EXISTS idx_training_data_embedding
    ON shopping_training_data
    USING ivfflat (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;

-- =============================================================================
-- SUMMARY OF CONSTRAINTS AND INDEXES
-- =============================================================================
-- shopping_sessions:
--   - Constraints: valid_guest_expiry, conversation_history_is_array, cart_items_is_array
--   - Indexes: idx_sessions_customer, idx_sessions_expires_at
--
-- shopping_carts:
--   - Constraints: valid_cart_status, cart_items_is_array, valid_cart_totals,
--                 non_negative_subtotal, non_negative_tax, non_negative_total
--   - Indexes: idx_carts_session, idx_carts_customer, idx_carts_status, idx_carts_updated_at
--
-- shopping_orders:
--   - Constraints: items_is_array, valid_order_totals, positive_subtotal,
--                 non_negative_tax_order, non_negative_total_order,
--                 valid_payment_status, valid_order_status, delivery_address_is_object
--   - Indexes: idx_orders_customer, idx_orders_status, idx_orders_created_at,
--              idx_orders_payment_intent
--
-- shopping_training_data:
--   - Constraints: valid_training_source
--   - Indexes: idx_training_data_product, idx_training_data_category,
--              idx_training_data_embedding (vector similarity)
-- =============================================================================
