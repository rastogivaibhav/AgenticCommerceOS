"""
ops_api.models.shopping — SQLAlchemy ORM models for shopping chatbot system.

This module defines all database models for the shopping chatbot, including:
- Session management (shopping_sessions)
- Shopping carts (shopping_carts)
- Orders and transactions (shopping_orders)
- Product knowledge enrichment (shopping_training_data)

Models correspond directly to the PostgreSQL schema defined in:
  ops_api/migrations/001_create_shopping_tables.sql
"""

import datetime
import uuid
from decimal import Decimal
from enum import Enum as PythonEnum

from sqlalchemy import (
    DECIMAL,
    JSON,
    TIMESTAMP,
    Column,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create declarative base for all models
Base = declarative_base()


# =============================================================================
# ENUMS (before Base)
# =============================================================================


class CartStatus(str, PythonEnum):
    """Enum for shopping cart status states.

    Values:
    - ACTIVE: Cart is currently being used
    - ABANDONED: Cart was not converted to order
    - CONVERTED: Cart was successfully converted to order
    """
    ACTIVE = "active"
    ABANDONED = "abandoned"
    CONVERTED = "converted"


class OrderStatus(str, PythonEnum):
    """Enum for shopping order status states.

    Values:
    - PENDING: Order created but not confirmed
    - CONFIRMED: Order confirmed and payment processed
    - SHIPPED: Order has been shipped to customer
    - DELIVERED: Order delivered to customer
    - CANCELLED: Order was cancelled
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, PythonEnum):
    """Enum for payment processing status.

    Values:
    - PENDING: Payment processing initiated but not completed
    - SUCCEEDED: Payment successfully processed
    - FAILED: Payment processing failed
    """
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


# =============================================================================
# DATABASE MODELS
# =============================================================================


class ShoppingSession(Base):
    """SQLAlchemy model for shopping_sessions table.

    Manages conversation context for both guest and registered users.
    Stores conversation history, cart items, and user preferences for each session.

    Attributes:
        session_id: UUID primary key (auto-generated)
        customer_id: FK to users table (nullable for guests)
        conversation_history: JSONB array of conversation messages
        cart_items: JSONB array of items currently in cart
        session_preferences: JSONB object for user preferences
        created_at: Session creation timestamp
        last_activity: Last activity timestamp
        expires_at: Session expiration time (required for guests, optional for registered)
    """
    __tablename__ = "shopping_sessions"

    session_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique session identifier"
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        doc="Optional FK to customer (null for guests)"
    )
    conversation_history = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="Array of conversation messages"
    )
    cart_items = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="Array of items in the shopping cart"
    )
    session_preferences = Column(
        JSONB,
        nullable=True,
        doc="User preferences stored as JSON object"
    )
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=datetime.datetime.utcnow,
        doc="Session creation timestamp"
    )
    last_activity = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=datetime.datetime.utcnow,
        doc="Last activity timestamp"
    )
    expires_at = Column(
        TIMESTAMP(timezone=False),
        nullable=True,
        doc="Session expiration time (required for guests)"
    )

    # Relationships
    carts = relationship(
        "ShoppingCart",
        back_populates="session",
        cascade="all, delete-orphan",
        doc="Shopping carts associated with this session"
    )
    orders = relationship(
        "ShoppingOrder",
        back_populates="session",
        cascade="all, delete-orphan",
        doc="Orders created from this session"
    )

    def __repr__(self) -> str:
        """Return string representation of ShoppingSession."""
        return (
            f"<ShoppingSession("
            f"session_id={self.session_id}, "
            f"customer_id={self.customer_id}, "
            f"created_at={self.created_at})>"
        )


class ShoppingCart(Base):
    """SQLAlchemy model for shopping_carts table.

    Maintains persistent cart state with financial calculations.
    Maintains audit trail of cart state changes (active, abandoned, converted).

    Attributes:
        cart_id: UUID primary key (auto-generated)
        session_id: FK to shopping_sessions (required)
        customer_id: FK to users table (nullable)
        items: JSONB array of items in cart
        subtotal: Decimal amount before tax
        tax: Decimal tax amount
        total: Decimal total (must equal subtotal + tax)
        status: CartStatus enum (active, abandoned, converted)
        created_at: Cart creation timestamp
        updated_at: Last update timestamp
        converted_at: Timestamp when cart was converted to order
    """
    __tablename__ = "shopping_carts"

    cart_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique cart identifier"
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("shopping_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        doc="FK to shopping session"
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        doc="Optional FK to customer"
    )
    items = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="Array of items in cart"
    )
    subtotal = Column(
        DECIMAL(19, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Subtotal before tax"
    )
    tax = Column(
        DECIMAL(19, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Tax amount"
    )
    total = Column(
        DECIMAL(19, 4),
        nullable=False,
        default=Decimal("0.0000"),
        doc="Total (subtotal + tax)"
    )
    status = Column(
        Enum(CartStatus),
        nullable=False,
        default=CartStatus.ACTIVE,
        doc="Cart status (active, abandoned, converted)"
    )
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=datetime.datetime.utcnow,
        doc="Cart creation timestamp"
    )
    updated_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        doc="Last update timestamp"
    )
    converted_at = Column(
        TIMESTAMP(timezone=False),
        nullable=True,
        doc="Timestamp when cart was converted to order"
    )

    # Relationships
    session = relationship(
        "ShoppingSession",
        back_populates="carts",
        doc="Associated shopping session"
    )

    def __repr__(self) -> str:
        """Return string representation of ShoppingCart."""
        return (
            f"<ShoppingCart("
            f"cart_id={self.cart_id}, "
            f"status={self.status}, "
            f"total={self.total}, "
            f"created_at={self.created_at})>"
        )


class ShoppingOrder(Base):
    """SQLAlchemy model for shopping_orders table.

    Immutable order snapshots with pricing and payment tracking.
    Maintains complete audit trail for payment processing and fulfillment.

    Attributes:
        order_id: UUID primary key (auto-generated)
        customer_id: FK to users table (required)
        session_id: FK to shopping_sessions (nullable, can be set to null on session delete)
        items: JSONB array of items ordered (immutable snapshot)
        subtotal: Decimal subtotal before tax
        tax: Decimal tax amount
        total: Decimal total (must equal subtotal + tax)
        currency: Currency code (e.g., 'GBP')
        delivery_address: JSONB object with delivery address
        payment_method: Payment method identifier
        payment_intent_id: Stripe/payment processor intent ID (unique)
        payment_status: PaymentStatus enum (pending, succeeded, failed)
        status: OrderStatus enum (pending, confirmed, shipped, delivered, cancelled)
        created_at: Order creation timestamp
        confirmed_at: Order confirmation timestamp
        shipped_at: Shipment timestamp
        delivered_at: Delivery timestamp
        cancelled_at: Cancellation timestamp
    """
    __tablename__ = "shopping_orders"

    order_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique order identifier"
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="FK to customer (required)"
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("shopping_sessions.session_id", ondelete="SET NULL"),
        nullable=True,
        doc="FK to session (nullable if session deleted)"
    )
    items = Column(
        JSONB,
        nullable=False,
        doc="Immutable array of ordered items"
    )
    subtotal = Column(
        DECIMAL(19, 4),
        nullable=False,
        doc="Subtotal before tax"
    )
    tax = Column(
        DECIMAL(19, 4),
        nullable=False,
        doc="Tax amount"
    )
    total = Column(
        DECIMAL(19, 4),
        nullable=False,
        doc="Total (subtotal + tax)"
    )
    currency = Column(
        String(3),
        nullable=False,
        default="GBP",
        doc="Currency code (e.g., GBP, USD)"
    )
    delivery_address = Column(
        JSONB,
        nullable=True,
        doc="Delivery address as JSON object"
    )
    payment_method = Column(
        String(255),
        nullable=True,
        doc="Payment method identifier"
    )
    payment_intent_id = Column(
        String(255),
        unique=True,
        nullable=True,
        doc="Unique payment processor intent ID"
    )
    payment_status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        doc="Payment status (pending, succeeded, failed)"
    )
    status = Column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        doc="Order status (pending, confirmed, shipped, delivered, cancelled)"
    )
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=datetime.datetime.utcnow,
        doc="Order creation timestamp"
    )
    confirmed_at = Column(
        TIMESTAMP(timezone=False),
        nullable=True,
        doc="Order confirmation timestamp"
    )
    shipped_at = Column(
        TIMESTAMP(timezone=False),
        nullable=True,
        doc="Shipment timestamp"
    )
    delivered_at = Column(
        TIMESTAMP(timezone=False),
        nullable=True,
        doc="Delivery timestamp"
    )
    cancelled_at = Column(
        TIMESTAMP(timezone=False),
        nullable=True,
        doc="Cancellation timestamp"
    )

    # Relationships
    session = relationship(
        "ShoppingSession",
        back_populates="orders",
        doc="Associated shopping session"
    )

    def __repr__(self) -> str:
        """Return string representation of ShoppingOrder."""
        return (
            f"<ShoppingOrder("
            f"order_id={self.order_id}, "
            f"customer_id={self.customer_id}, "
            f"status={self.status}, "
            f"total={self.total}, "
            f"created_at={self.created_at})>"
        )


class ShoppingTrainingData(Base):
    """SQLAlchemy model for shopping_training_data table.

    Product knowledge for agent enrichment.
    Stores product information, FAQs, and embeddings for semantic search.

    Attributes:
        id: UUID primary key (auto-generated)
        product_id: Product identifier (VARCHAR)
        category: Product category (VARCHAR, optional)
        content: Full text content (TEXT)
        embedding: Vector embedding (1536 dimensions, optional)
        source: Source type (product_description, faq, review, guide)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "shopping_training_data"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique training data identifier"
    )
    product_id = Column(
        String(255),
        nullable=False,
        doc="Product identifier"
    )
    category = Column(
        String(100),
        nullable=True,
        doc="Product category"
    )
    content = Column(
        Text,
        nullable=False,
        doc="Full text content for training"
    )
    embedding = Column(
        String,  # Vector(1536) requires pgvector extension
        nullable=True,
        doc="Vector embedding (1536 dimensions)"
    )
    source = Column(
        String(50),
        nullable=False,
        doc="Source type (product_description, faq, review, guide)"
    )
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=datetime.datetime.utcnow,
        doc="Creation timestamp"
    )
    updated_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        doc="Last update timestamp"
    )

    def __repr__(self) -> str:
        """Return string representation of ShoppingTrainingData."""
        return (
            f"<ShoppingTrainingData("
            f"id={self.id}, "
            f"product_id={self.product_id}, "
            f"source={self.source}, "
            f"created_at={self.created_at})>"
        )
