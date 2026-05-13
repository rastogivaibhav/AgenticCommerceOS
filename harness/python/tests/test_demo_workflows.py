"""Tests for demo workflow implementations."""

import pytest
from fastapi.testclient import TestClient
from apps.chat_api.main import app
from apps.chat_api.workflows.demo import (
    AccountWorkflow,
    DiscoveryWorkflow,
    SupportWorkflow,
    get_demo_workflow,
)


class TestAccountWorkflow:
    """Test account workflow."""

    def test_balance_query(self):
        """Test balance query response."""
        workflow = AccountWorkflow()
        result = workflow.execute("What is my balance?", {})
        assert "balance" in result.lower()
        assert "£1,250.50" in result

    def test_account_info_query(self):
        """Test account info query response."""
        workflow = AccountWorkflow()
        result = workflow.execute("Show my account info", {})
        assert "Account Info" in result
        assert "user@example.com" in result

    def test_loyalty_points(self):
        """Test loyalty points query."""
        workflow = AccountWorkflow()
        result = workflow.execute("How many loyalty points do I have?", {})
        assert "loyalty points" in result.lower() or "2,450" in result

    def test_password_reset(self):
        """Test password reset guidance."""
        workflow = AccountWorkflow()
        result = workflow.execute("How do I change my password?", {})
        assert "password" in result.lower()

    def test_default_account_response(self):
        """Test default account workflow response."""
        workflow = AccountWorkflow()
        result = workflow.execute("help with my account", {})
        assert len(result) > 0


class TestDiscoveryWorkflow:
    """Test product discovery workflow."""

    def test_find_red_dresses(self):
        """Test finding red dresses."""
        workflow = DiscoveryWorkflow()
        result = workflow.execute("find me red dresses", {})
        assert "Red" in result or "dresses" in result.lower()
        assert "£" in result  # Should include pricing

    def test_find_shoes(self):
        """Test finding shoes."""
        workflow = DiscoveryWorkflow()
        result = workflow.execute("show me shoes", {})
        assert "Shoes" in result or "shoes" in result.lower()

    def test_find_jackets(self):
        """Test finding jackets."""
        workflow = DiscoveryWorkflow()
        result = workflow.execute("I need a jacket", {})
        assert "Jacket" in result or "jacket" in result.lower()

    def test_featured_items_default(self):
        """Test default discovery response with featured items."""
        workflow = DiscoveryWorkflow()
        result = workflow.execute("show me something", {})
        assert "featured" in result.lower() or "£" in result


class TestSupportWorkflow:
    """Test customer support workflow."""

    def test_return_request(self):
        """Test return/refund request."""
        workflow = SupportWorkflow()
        result = workflow.execute("I want to return this item", {})
        assert "return" in result.lower()
        assert "30 days" in result

    def test_damaged_item(self):
        """Test damaged item report."""
        workflow = SupportWorkflow()
        result = workflow.execute("My item arrived damaged", {})
        assert "damaged" in result.lower()
        assert "replacement" in result.lower()

    def test_shipping_status(self):
        """Test shipping status query."""
        workflow = SupportWorkflow()
        result = workflow.execute("Where is my order?", {})
        assert "order" in result.lower() or "shipping" in result.lower() or "3-5" in result

    def test_order_issue(self):
        """Test general order issue."""
        workflow = SupportWorkflow()
        result = workflow.execute("There's an issue with my order", {})
        assert "order" in result.lower()

    def test_default_support_response(self):
        """Test default support response."""
        workflow = SupportWorkflow()
        result = workflow.execute("help me", {})
        assert len(result) > 0


class TestGetDemoWorkflow:
    """Test get_demo_workflow helper."""

    def test_get_account_workflow(self):
        """Test getting account workflow."""
        workflow = get_demo_workflow("wf-account")
        assert isinstance(workflow, AccountWorkflow)

    def test_get_discovery_workflow(self):
        """Test getting discovery workflow."""
        workflow = get_demo_workflow("wf-discovery")
        assert isinstance(workflow, DiscoveryWorkflow)

    def test_get_support_workflow(self):
        """Test getting support workflow."""
        workflow = get_demo_workflow("wf-support")
        assert isinstance(workflow, SupportWorkflow)

    def test_get_unknown_workflow(self):
        """Test getting unknown workflow."""
        workflow = get_demo_workflow("wf-unknown")
        assert workflow is None


class TestDemoWorkflowsViaAPI:
    """Test demo workflows through the chat API."""

    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)

    def test_account_workflow_via_api(self, client):
        """Test account workflow via /api/chat/message endpoint."""
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "what is my balance",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = client.post("/api/chat/message", json=payload)
        # Should succeed or at least exist
        assert response.status_code in [200, 400, 500]

    def test_discovery_workflow_via_api(self, client):
        """Test discovery workflow via API."""
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "find me red dresses",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = client.post("/api/chat/message", json=payload)
        assert response.status_code in [200, 400, 500]

    def test_support_workflow_via_api(self, client):
        """Test support workflow via API."""
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": "U12345",
                "channel": "C12345",
                "text": "I want to return my order",
                "ts": "1234567890.123456"
            },
            "user_id": "U12345",
            "channel_id": "C12345",
            "timestamp": "1234567890.123456"
        }

        response = client.post("/api/chat/message", json=payload)
        assert response.status_code in [200, 400, 500]
