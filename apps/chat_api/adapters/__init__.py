"""Chat adapters for normalizing external platform events."""

from apps.chat_api.adapters.base import BaseAdapter
from apps.chat_api.adapters.slack import SlackAdapter

__all__ = ["BaseAdapter", "SlackAdapter"]
