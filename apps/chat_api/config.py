"""Chat API configuration – loads Slack credentials and settings."""

import os
from typing import Optional


class SlackConfig:
    """Slack configuration from environment variables."""

    def __init__(self):
        self.bot_token: Optional[str] = os.environ.get("SLACK_BOT_TOKEN")
        self.signing_secret: Optional[str] = os.environ.get("SLACK_SIGNING_SECRET")
        self.workspace_id: Optional[str] = os.environ.get("SLACK_WORKSPACE_ID", "default")

    def is_configured(self) -> bool:
        """Check if Slack is properly configured."""
        return bool(self.bot_token and self.signing_secret)


class ChatConfig:
    """Chat API configuration."""

    def __init__(self):
        self.slack = SlackConfig()
        self.environment = os.environ.get("OPS_ENVIRONMENT", "dev")
        self.version = os.environ.get("APP_VERSION", "1.0.0")
        self.allowed_origins = [
            o.strip()
            for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
            if o.strip()
        ]


config = ChatConfig()
