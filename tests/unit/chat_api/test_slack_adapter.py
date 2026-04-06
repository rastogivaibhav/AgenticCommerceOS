"""Unit tests for Slack adapter."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from apps.chat_api.adapters.slack import SlackAdapter
from apps.chat_api.models.chat import ChatMessage


class TestSlackAdapter:
    """Tests for SlackAdapter."""

    @pytest.fixture
    def mock_slack_client(self):
        """Create a mock Slack client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def adapter(self, mock_slack_client):
        """Create a SlackAdapter instance with mock client."""
        return SlackAdapter(slack_client=mock_slack_client)

    def test_adapter_initialization(self, adapter, mock_slack_client):
        """Test adapter initializes with Slack client."""
        assert adapter.slack_client is mock_slack_client

    def test_normalize_simple_message(self, adapter):
        """Test normalizing a simple Slack message event."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "Hello, world!",
            "ts": "1234567890.001234",
        }

        message = adapter.normalize_event(event)

        assert isinstance(message, ChatMessage)
        assert message.user_id == "U12345"
        assert message.channel_id == "C67890"
        assert message.text == "Hello, world!"
        assert message.thread_ts is None
        assert message.id == "1234567890.001234"

    def test_normalize_threaded_message(self, adapter):
        """Test normalizing a Slack message in a thread."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "Reply in thread",
            "ts": "1234567890.002345",
            "thread_ts": "1234567890.001234",
        }

        message = adapter.normalize_event(event)

        assert message.user_id == "U12345"
        assert message.channel_id == "C67890"
        assert message.text == "Reply in thread"
        assert message.thread_ts == "1234567890.001234"
        assert message.id == "1234567890.002345"

    def test_normalize_message_with_timestamp_conversion(self, adapter):
        """Test that Slack timestamp is converted to datetime."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "Test message",
            "ts": "1609459200.000100",  # 2021-01-01 00:00:00 UTC
        }

        message = adapter.normalize_event(event)

        assert isinstance(message.timestamp, datetime)
        # Slack ts is in seconds.microseconds format
        assert message.timestamp.year == 2021
        assert message.timestamp.month == 1
        assert message.timestamp.day == 1

    def test_normalize_message_with_empty_text(self, adapter):
        """Test normalizing a message with empty text."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "",
            "ts": "1234567890.001234",
        }

        message = adapter.normalize_event(event)

        assert message.text == ""

    def test_normalize_missing_required_field_user(self, adapter):
        """Test error when user_id is missing."""
        event = {
            "type": "message",
            "channel": "C67890",
            "text": "No user",
            "ts": "1234567890.001234",
        }

        with pytest.raises(ValueError, match="Missing required field: user"):
            adapter.normalize_event(event)

    def test_normalize_missing_required_field_channel(self, adapter):
        """Test error when channel_id is missing."""
        event = {
            "type": "message",
            "user": "U12345",
            "text": "No channel",
            "ts": "1234567890.001234",
        }

        with pytest.raises(ValueError, match="Missing required field: channel"):
            adapter.normalize_event(event)

    def test_normalize_missing_required_field_text(self, adapter):
        """Test error when text is missing."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "ts": "1234567890.001234",
        }

        with pytest.raises(ValueError, match="Missing required field: text"):
            adapter.normalize_event(event)

    def test_normalize_missing_required_field_ts(self, adapter):
        """Test error when ts (timestamp) is missing."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "No timestamp",
        }

        with pytest.raises(ValueError, match="Missing required field: ts"):
            adapter.normalize_event(event)

    def test_normalize_wrong_event_type(self, adapter):
        """Test error when event type is not 'message'."""
        event = {
            "type": "app_mention",
            "user": "U12345",
            "channel": "C67890",
            "text": "Wrong type",
            "ts": "1234567890.001234",
        }

        with pytest.raises(ValueError, match="Expected event type 'message', got 'app_mention'"):
            adapter.normalize_event(event)

    def test_normalize_invalid_timestamp(self, adapter):
        """Test error with invalid Slack timestamp format."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "Invalid ts",
            "ts": "not-a-timestamp",
        }

        with pytest.raises(ValueError, match="Invalid timestamp format"):
            adapter.normalize_event(event)

    def test_send_message_to_channel(self, adapter, mock_slack_client):
        """Test sending a message to a Slack channel."""
        mock_slack_client.chat_postMessage.return_value = {
            "ok": True,
            "channel": "C67890",
            "ts": "1234567890.001234",
        }

        response = adapter.send_message(
            channel_id="C67890",
            text="Hello from adapter",
        )

        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel="C67890",
            text="Hello from adapter",
            thread_ts=None,
        )
        assert response["ok"] is True
        assert response["ts"] == "1234567890.001234"

    def test_send_message_to_thread(self, adapter, mock_slack_client):
        """Test sending a message to a thread."""
        mock_slack_client.chat_postMessage.return_value = {
            "ok": True,
            "channel": "C67890",
            "ts": "1234567890.002345",
        }

        response = adapter.send_message(
            channel_id="C67890",
            text="Reply in thread",
            thread_ts="1234567890.001234",
        )

        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel="C67890",
            text="Reply in thread",
            thread_ts="1234567890.001234",
        )
        assert response["ok"] is True

    def test_send_message_failure(self, adapter, mock_slack_client):
        """Test handling of failed message send."""
        mock_slack_client.chat_postMessage.return_value = {
            "ok": False,
            "error": "channel_not_found",
        }

        with pytest.raises(RuntimeError, match="Failed to send message"):
            adapter.send_message(
                channel_id="C67890",
                text="This will fail",
            )

    def test_send_message_with_blocks(self, adapter, mock_slack_client):
        """Test sending a message with formatting blocks."""
        mock_slack_client.chat_postMessage.return_value = {
            "ok": True,
            "channel": "C67890",
            "ts": "1234567890.001234",
        }

        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Hello"}}]

        response = adapter.send_message(
            channel_id="C67890",
            text="Fallback text",
            blocks=blocks,
        )

        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel="C67890",
            text="Fallback text",
            blocks=blocks,
            thread_ts=None,
        )
        assert response["ok"] is True

    def test_normalize_message_with_reactions(self, adapter):
        """Test normalizing a message with reactions."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "Message with reactions",
            "ts": "1234567890.001234",
        }

        message = adapter.normalize_event(event)

        assert message.reactions is None

    def test_adapter_is_instance_of_base_adapter(self, adapter):
        """Test that SlackAdapter inherits from BaseAdapter."""
        from apps.chat_api.adapters.base import BaseAdapter
        assert isinstance(adapter, BaseAdapter)

    def test_normalize_message_with_special_characters(self, adapter):
        """Test normalizing a message with special characters."""
        event = {
            "type": "message",
            "user": "U12345",
            "channel": "C67890",
            "text": "Special chars: <@U123> <#C456> :smile: *bold* _italic_",
            "ts": "1234567890.001234",
        }

        message = adapter.normalize_event(event)

        assert "Special chars:" in message.text
        assert "<@U123>" in message.text

    def test_normalize_bot_message_ignored(self, adapter):
        """Test that messages from bots are handled (subtype=bot_message)."""
        event = {
            "type": "message",
            "subtype": "bot_message",
            "bot_id": "B12345",
            "text": "Bot message",
            "channel": "C67890",
            "ts": "1234567890.001234",
        }

        # Bot messages should be normalized (no user field, but bot_id instead)
        # Adapter should handle this gracefully
        with pytest.raises(ValueError, match="Missing required field: user"):
            adapter.normalize_event(event)
