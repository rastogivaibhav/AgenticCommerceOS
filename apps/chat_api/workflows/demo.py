"""Demo workflow implementations for the chat pipeline.

These are simple demonstration workflows that show how the system processes
different types of customer requests:
1. Account workflow - balance checks, account info, settings
2. Discovery workflow - product search and recommendations
3. Support workflow - order issues, returns, complaints
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AccountWorkflow:
    """Demo workflow for account-related queries."""

    def execute(self, message_text: str, context: Dict[str, Any]) -> str:
        """Execute account workflow.

        Args:
            message_text: User message text
            context: Session context with user/session info

        Returns:
            Response message
        """
        text = message_text.lower()

        if "balance" in text:
            return "Your current account balance is £1,250.50. You have £500 available credit."
        elif "account" in text and "info" in text:
            return "Account Info:\n- Email: user@example.com\n- Member since: Jan 2023\n- Status: Gold Member"
        elif "password" in text or "settings" in text:
            return "You can update your account settings in Settings > Account. Password change requires email verification."
        elif "loyalty" in text or "points" in text:
            return "You have 2,450 loyalty points. Redeem them in the Rewards section for discounts and exclusive perks."
        else:
            return "I can help with your account. Ask me about balance, account info, settings, or loyalty points."


class DiscoveryWorkflow:
    """Demo workflow for product discovery and recommendations."""

    def execute(self, message_text: str, context: Dict[str, Any]) -> str:
        """Execute discovery workflow.

        Args:
            message_text: User message text
            context: Session context with user/session info

        Returns:
            Response message with product recommendations
        """
        text = message_text.lower()

        # Simulated product catalog
        products = {
            "red dresses": [
                "Red Midi Dress - £45 (4.5★)",
                "Elegant Red Gown - £89.99 (4.8★)",
                "Casual Red Shirt Dress - £32 (4.3★)",
            ],
            "shoes": [
                "Leather Oxfords - £65 (4.6★)",
                "Running Trainers - £75 (4.7★)",
                "Comfort Walking Shoes - £52 (4.4★)",
            ],
            "jackets": [
                "Winter Wool Coat - £120 (4.7★)",
                "Denim Jacket - £55 (4.5★)",
                "Leather Bomber - £95 (4.6★)",
            ],
            "bags": [
                "Canvas Tote Bag - £35 (4.4★)",
                "Leather Crossbody - £78 (4.7★)",
                "Backpack - £60 (4.5★)",
            ],
        }

        # Check for category matches (including plural/singular)
        for category, items in products.items():
            category_singular = category.rstrip('s')  # Remove trailing 's' for singular
            if any(cat in text for cat in [category, category_singular]):
                result = f"Found {len(items)} {category}:\n"
                for item in items:
                    result += f"• {item}\n"
                result += "\nWould you like more details on any of these?"
                return result

        # Default: show featured items
        return (
            "Here are our featured items today:\n"
            "• Bestselling Red Dress - £45\n"
            "• New Autumn Coats - from £80\n"
            "• Designer Shoes Sale - 30% off\n"
            "What type of product are you looking for?"
        )


class SupportWorkflow:
    """Demo workflow for customer support and issue resolution."""

    def execute(self, message_text: str, context: Dict[str, Any]) -> str:
        """Execute support workflow.

        Args:
            message_text: User message text
            context: Session context with user/session info

        Returns:
            Response message with support info
        """
        text = message_text.lower()

        if "return" in text or "refund" in text:
            return (
                "Returns are easy! You have 30 days to return most items.\n"
                "Status: Ready to accept your return\n"
                "Next step: Click 'Start Return' in your Orders section\n"
                "Need help? Reply with your order number."
            )
        elif "order" in text and ("problem" in text or "issue" in text or "help" in text):
            return (
                "I'm here to help! Common order issues:\n"
                "• Delayed delivery - Check tracking or contact carrier\n"
                "• Wrong item - Start a return immediately\n"
                "• Missing items - File a claim within 48 hours\n"
                "What's the issue with your order?"
            )
        elif "shipping" in text or "delivery" in text:
            return "Your order is expected to arrive in 3-5 business days. Tracking: #TRK123456. Click for live updates."
        elif "damaged" in text or "broken" in text:
            return (
                "Sorry to hear your item arrived damaged!\n"
                "We'll send a replacement immediately and arrange pickup.\n"
                "Please reply with photos for our records."
            )
        else:
            return (
                "I'm here to help with any issues. Ask about:\n"
                "• Returns and refunds\n"
                "• Order problems\n"
                "• Shipping and delivery\n"
                "• Damaged items\n"
                "What can I help you with?"
            )


def get_demo_workflow(workflow_id: str) -> Any:
    """Get demo workflow instance by ID.

    Args:
        workflow_id: One of 'wf-account', 'wf-discovery', 'wf-support'

    Returns:
        Workflow instance or None if not found
    """
    workflows = {
        "wf-account": AccountWorkflow(),
        "wf-discovery": DiscoveryWorkflow(),
        "wf-support": SupportWorkflow(),
    }
    return workflows.get(workflow_id)
