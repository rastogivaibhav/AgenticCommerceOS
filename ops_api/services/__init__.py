"""
ops_api.services — Service layer for shopping chatbot operations.

This package contains service classes for managing core shopping chatbot
functionality including session management, cart operations, and preferences.
"""

from ops_api.services.shopping_sessions import SessionManager

__all__ = ["SessionManager"]
