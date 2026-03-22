"""
ops_api.models.schemas — Pydantic v2 schemas for request/response validation.

This module provides request and response validation schemas for the shopping
chatbot API, including:
- Session creation and management
- Chat message handling
- Shopping cart operations
- Checkout and order processing
- Error responses

All schemas use Pydantic v2 with frozen immutability for response objects.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# SESSION SCHEMAS
# =============================================================================


class SessionCreateRequest(BaseModel):
    """Request schema for creating a new shopping session.

    Attributes:
        type: Session type identifier
        customer_id: Optional customer ID (null for guests)
    """
    type: str = Field(
        ...,
        description="Type of session (e.g., 'shopping', 'browsing')"
    )
    customer_id: Optional[str] = Field(
        None,
        description="Optional customer ID for authenticated sessions"
    )


class SessionResponse(BaseModel):
    """Response schema for session creation and retrieval.

    Attributes:
        session_id: Unique session identifier
        customer_id: Optional customer ID
        token: Session authentication token
        expires_at: Session expiration timestamp
        created_at: Session creation timestamp
    """
    model_config = {"frozen": True}

    session_id: str = Field(
        ...,
        description="Unique session identifier (UUID)"
    )
    customer_id: Optional[str] = Field(
        None,
        description="Associated customer ID if authenticated"
    )
    token: str = Field(
        ...,
        description="Session authentication token"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Session expiration time (null for registered users)"
    )
    created_at: datetime = Field(
        ...,
        description="Session creation timestamp"
    )


# =============================================================================
# CHAT MESSAGE SCHEMAS
# =============================================================================


class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message.

    Attributes:
        content: Message content text
        timestamp: Optional message timestamp (defaults to now)
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content"
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="Message timestamp (defaults to current time)"
    )

    @field_validator("content")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading and trailing whitespace from content."""
        return v.strip()


class ChatMessage(BaseModel):
    """Response schema for chat messages.

    Represents a single message in the conversation history.

    Attributes:
        role: Message sender role ('user' or 'assistant')
        content: Message content text
        timestamp: Message timestamp
    """
    model_config = {"frozen": True}

    role: Literal["user", "assistant"] = Field(
        ...,
        description="Message sender role"
    )
    content: str = Field(
        ...,
        description="Message content"
    )
    timestamp: datetime = Field(
        ...,
        description="Message timestamp"
    )


# =============================================================================
# CART SCHEMAS
# =============================================================================


class CartItem(BaseModel):
    """Schema representing a single item in a shopping cart.

    Attributes:
        product_id: Product identifier
        quantity: Item quantity
        price: Unit price (Decimal for accuracy)
        name: Product name
        image_url: Optional product image URL
    """
    product_id: str = Field(
        ...,
        description="Unique product identifier"
    )
    quantity: int = Field(
        ...,
        ge=1,
        le=999,
        description="Quantity (1-999)"
    )
    price: Decimal = Field(
        ...,
        decimal_places=2,
        description="Unit price in currency"
    )
    name: str = Field(
        ...,
        description="Product name"
    )
    image_url: Optional[str] = Field(
        None,
        description="Product image URL"
    )

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Ensure price is non-negative."""
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v


class CartResponse(BaseModel):
    """Response schema for cart contents and totals.

    Attributes:
        items: List of items in cart
        subtotal: Subtotal before tax (Decimal)
        tax: Tax amount (Decimal)
        total: Total amount including tax (Decimal)
    """
    model_config = {"frozen": True}

    items: List[CartItem] = Field(
        default_factory=list,
        description="Items in shopping cart"
    )
    subtotal: Decimal = Field(
        ...,
        decimal_places=2,
        description="Subtotal before tax"
    )
    tax: Decimal = Field(
        ...,
        decimal_places=2,
        description="Tax amount"
    )
    total: Decimal = Field(
        ...,
        decimal_places=2,
        description="Total (subtotal + tax)"
    )

    @field_validator("total")
    @classmethod
    def validate_total(cls, v: Decimal, info: Any) -> Decimal:
        """Ensure total equals subtotal + tax."""
        data = info.data
        if "subtotal" in data and "tax" in data:
            expected = data["subtotal"] + data["tax"]
            if v != expected:
                raise ValueError(f"Total must equal subtotal + tax ({expected})")
        return v


# =============================================================================
# CHECKOUT & ORDER SCHEMAS
# =============================================================================


class CheckoutRequest(BaseModel):
    """Request schema for checkout and order creation.

    Attributes:
        customer_info: Dictionary with customer details
        delivery_address: Dictionary with delivery address
        payment_method: Payment method identifier
    """
    customer_info: Dict[str, Any] = Field(
        ...,
        description="Customer information (name, email, phone, etc.)"
    )
    delivery_address: Dict[str, Any] = Field(
        ...,
        description="Delivery address (street, city, postal_code, country, etc.)"
    )
    payment_method: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Payment method identifier (e.g., 'card', 'paypal')"
    )

    @field_validator("customer_info")
    @classmethod
    def validate_customer_info(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure customer info has required fields."""
        required_fields = {"name", "email"}
        if not required_fields.issubset(v.keys()):
            raise ValueError(
                f"customer_info must contain at least: {required_fields}"
            )
        return v

    @field_validator("delivery_address")
    @classmethod
    def validate_address(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure delivery address has required fields."""
        required_fields = {"street", "city", "postal_code", "country"}
        if not required_fields.issubset(v.keys()):
            raise ValueError(
                f"delivery_address must contain at least: {required_fields}"
            )
        return v


class OrderResponse(BaseModel):
    """Response schema for order creation and retrieval.

    Attributes:
        order_id: Unique order identifier
        status: Order status (pending, confirmed, shipped, etc.)
        items: Items in the order
        total: Order total amount
        delivery_estimate: Optional estimated delivery date
        confirmation_email: Optional confirmation email address
    """
    model_config = {"frozen": True}

    order_id: str = Field(
        ...,
        description="Unique order identifier (UUID)"
    )
    status: Literal[
        "pending", "confirmed", "shipped", "delivered", "cancelled"
    ] = Field(
        ...,
        description="Order status"
    )
    items: List[CartItem] = Field(
        ...,
        description="Items in the order"
    )
    total: Decimal = Field(
        ...,
        decimal_places=2,
        description="Order total amount"
    )
    delivery_estimate: Optional[datetime] = Field(
        None,
        description="Estimated delivery date"
    )
    confirmation_email: Optional[str] = Field(
        None,
        description="Order confirmation email sent to customer"
    )


# =============================================================================
# ERROR SCHEMAS
# =============================================================================


class ErrorDetails(BaseModel):
    """Response schema for API error responses.

    Provides structured error information for client handling.

    Attributes:
        code: Machine-readable error code
        message: Human-readable error message
        details: Optional additional error details
        retry_after: Optional seconds to wait before retrying
    """
    model_config = {"frozen": True}

    code: str = Field(
        ...,
        description="Machine-readable error code (e.g., 'INVALID_SESSION')"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details and context"
    )
    retry_after: Optional[int] = Field(
        None,
        ge=0,
        description="Seconds to wait before retrying (for rate limits)"
    )
