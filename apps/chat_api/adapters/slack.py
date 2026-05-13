"""Slack-specific adapter for normalizing Slack events."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from apps.chat_api.adapters.base import BaseAdapter
from apps.chat_api.models.chat import ChatMessage

logger = logging.getLogger(__name__)


class SlackAdapter(BaseAdapter):
    """Adapter for normalizing Slack events to internal ChatMessage format."""

    def __init__(self, slack_client):
        """Initialize SlackAdapter with a Slack client.

        Args:
            slack_client: Slack Bolt SDK client or similar with chat_postMessage method.
        """
        self.slack_client = slack_client

    def normalize_event(self, event: Dict[str, Any]) -> ChatMessage:
        """Normalize a Slack message event to ChatMessage format.

        Slack events come as JSON from the Events API. This method extracts
        relevant fields and validates required data.

        Args:
            event: Slack event data from webhook.

        Returns:
            ChatMessage: Normalized message with extracted Slack data.

        Raises:
            ValueError: If required fields are missing or event is invalid.
        """
        # Validate event type
        event_type = event.get("type")
        if event_type != "message":
            raise ValueError(
                f"Expected event type 'message', got '{event_type}'"
            )

        # Extract and validate required fields
        user_id = event.get("user")
        if not user_id:
            raise ValueError("Missing required field: user")

        channel_id = event.get("channel")
        if not channel_id:
            raise ValueError("Missing required field: channel")

        text = event.get("text")
        if text is None:
            raise ValueError("Missing required field: text")

        ts = event.get("ts")
        if not ts:
            raise ValueError("Missing required field: ts")

        # Parse Slack timestamp (format: "seconds.microseconds")
        try:
            timestamp = self._parse_slack_timestamp(ts)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid timestamp format: {ts}") from e

        # Optional fields
        thread_ts = event.get("thread_ts")

        # Create normalized message
        message = ChatMessage(
            id=ts,
            channel_id=channel_id,
            user_id=user_id,
            text=text,
            timestamp=timestamp,
            thread_ts=thread_ts,
            reactions=None,
        )

        logger.debug(
            f"Normalized Slack message from {user_id} in {channel_id}: {text[:50]}..."
        )

        return message

    def send_message(
        self,
        channel_id: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel.

        Args:
            channel_id: Slack channel ID (e.g., "C12345").
            text: Message text (used as fallback if blocks provided).
            thread_ts: Optional thread timestamp to reply in thread.
            blocks: Optional Block Kit elements for rich formatting.

        Returns:
            Dict with response from Slack API (should contain "ok" and "ts").

        Raises:
            RuntimeError: If message send fails.
        """
        try:
            # Build message payload
            payload = {
                "channel": channel_id,
                "text": text,
                "thread_ts": thread_ts,
            }

            # Add blocks if provided
            if blocks:
                payload["blocks"] = blocks

            # Send message via Slack client
            response = self.slack_client.chat_postMessage(**payload)

            # Check for success
            if not response.get("ok"):
                error_msg = response.get("error", "unknown error")
                raise RuntimeError(
                    f"Failed to send message to {channel_id}: {error_msg}"
                )

            logger.debug(
                f"Sent message to {channel_id} "
                f"(thread_ts={thread_ts}): {text[:50]}..."
            )

            return response

        except Exception as e:
            logger.error(f"Error sending message to {channel_id}: {e}")
            raise

    @staticmethod
    def _parse_slack_timestamp(ts: str) -> datetime:
        """Parse Slack timestamp format (seconds.microseconds).

        Args:
            ts: Slack timestamp as string (e.g., "1234567890.001234").

        Returns:
            datetime: Parsed datetime in UTC.

        Raises:
            ValueError: If timestamp format is invalid.
        """
        try:
            # Slack timestamps are Unix time in seconds.microseconds format
            timestamp_float = float(ts)
            return datetime.fromtimestamp(timestamp_float, tz=timezone.utc)
        except (ValueError, TypeError, OSError) as e:
            raise ValueError(f"Invalid Slack timestamp format: {ts}") from e
