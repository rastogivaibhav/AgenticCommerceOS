"""
ops_api.models — Database models and schemas for shopping chatbot system.

This package provides:
- SQLAlchemy ORM models (shopping.py)
- Pydantic validation schemas (schemas.py)
"""

from ops_api.models.shopping import (
    CartStatus,
    OrderStatus,
    PaymentStatus,
    ShoppingCart,
    ShoppingOrder,
    ShoppingSession,
    ShoppingTrainingData,
)
from ops_api.models.schemas import (
    CartItem,
    CartResponse,
    ChatMessage,
    ChatMessageRequest,
    CheckoutRequest,
    ErrorDetails,
    OrderResponse,
    SessionCreateRequest,
    SessionResponse,
)

__all__ = [
    # Enums
    "CartStatus",
    "OrderStatus",
    "PaymentStatus",
    # Models
    "ShoppingSession",
    "ShoppingCart",
    "ShoppingOrder",
    "ShoppingTrainingData",
    # Schemas
    "SessionCreateRequest",
    "SessionResponse",
    "ChatMessageRequest",
    "ChatMessage",
    "CartItem",
    "CartResponse",
    "CheckoutRequest",
    "OrderResponse",
    "ErrorDetails",
]
