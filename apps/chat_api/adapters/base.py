"""Base adapter interface for normalizing external chat events."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from apps.chat_api.models.chat import ChatMessage


class BaseAdapter(ABC):
    """Abstract base class for chat platform adapters.

    Adapters normalize platform-specific events into a common internal format.
    """

    @abstractmethod
    def normalize_event(self, event: Dict[str, Any]) -> ChatMessage:
        """Normalize a platform-specific event to internal ChatMessage format.

        Args:
            event: Platform-specific event data (typically from webhook).

        Returns:
            ChatMessage: Normalized message in internal format.

        Raises:
            ValueError: If required fields are missing or event is invalid.
        """
        pass

    @abstractmethod
    def send_message(
        self,
        channel_id: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a message back to the platform.

        Args:
            channel_id: ID of the channel to send message to.
            text: Text content of the message.
            thread_ts: Optional thread timestamp if replying in a thread.
            blocks: Optional block elements for rich formatting.

        Returns:
            Dict with platform-specific response (should include ok/status).

        Raises:
            RuntimeError: If message send fails.
        """
        pass
