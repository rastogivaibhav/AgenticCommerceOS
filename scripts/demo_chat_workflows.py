#!/usr/bin/env python
"""Demo script for Chat API with demo workflows.

This script demonstrates how the three demo workflows (account, discovery, support)
work in the chat pipeline. It shows:
1. How messages are processed through the chat API
2. How workflows are detected from message content
3. How sync/async execution works
4. Error handling and fallback strategies

Usage:
    python scripts/demo_chat_workflows.py

Or run specific demo:
    python scripts/demo_chat_workflows.py --workflow account
    python scripts/demo_chat_workflows.py --workflow discovery
    python scripts/demo_chat_workflows.py --workflow support
"""

import sys
import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Chat API URL
CHAT_ENDPOINT = "/api/chat/message"
JOBS_ENDPOINT = "/api/jobs"

# Demo messages for each workflow
DEMO_MESSAGES = {
    "account": [
        "What is my account balance?",
        "Show my account info",
        "How many loyalty points do I have?",
        "How do I change my password?",
    ],
    "discovery": [
        "Find me red dresses",
        "Show me shoes",
        "I need a jacket",
        "What do you recommend?",
    ],
    "support": [
        "I want to return this item",
        "Where is my order?",
        "My item arrived damaged",
        "What's the return policy?",
    ],
}


def send_chat_message(
    message_text: str,
    user_id: str = "U_demo_12345",
    channel_id: str = "C_demo_67890",
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a chat message to the API.

    Args:
        message_text: Message to send
        user_id: User identifier
        channel_id: Channel identifier
        session_id: Optional session ID

    Returns:
        Response dict from API
    """
    payload = {
        "source": "slack",
        "event": {
            "type": "message",
            "user": user_id,
            "channel": channel_id,
            "text": message_text,
            "ts": str(time.time()),
        },
        "user_id": user_id,
        "channel_id": channel_id,
        "timestamp": str(time.time()),
    }

    try:
        response = requests.post(f"{BASE_URL}{CHAT_ENDPOINT}", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Cannot reach {BASE_URL}")
        print("   Make sure the Chat API is running (see DEPLOYMENT.md)")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        return {"error": str(e)}


def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get status of an async job.

    Args:
        job_id: Job identifier

    Returns:
        Job status dict
    """
    try:
        response = requests.get(f"{BASE_URL}{JOBS_ENDPOINT}/{job_id}/status", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get job status: {str(e)}")
        return {"error": str(e)}


def print_response(response: Dict[str, Any], indent: int = 2) -> None:
    """Pretty print API response.

    Args:
        response: Response dict
        indent: Indentation level
    """
    spaces = " " * indent
    for key, value in response.items():
        if isinstance(value, dict):
            print(f"{spaces}{key}:")
            print_response(value, indent + 2)
        elif isinstance(value, list):
            print(f"{spaces}{key}:")
            for item in value:
                if isinstance(item, dict):
                    print_response(item, indent + 2)
                else:
                    print(f"{spaces}  - {item}")
        else:
            print(f"{spaces}{key}: {value}")


def demo_account_workflow() -> None:
    """Demo account workflow."""
    print("\n" + "=" * 70)
    print("🔐 ACCOUNT WORKFLOW DEMO")
    print("=" * 70)
    print("\nThis workflow handles account-related queries:")
    print("  • Balance checks")
    print("  • Account information")
    print("  • Loyalty points")
    print("  • Account settings\n")

    for message in DEMO_MESSAGES["account"]:
        print(f"\n📝 User: {message}")
        print("-" * 70)

        response = send_chat_message(message)

        if "error" in response:
            print(f"❌ Error: {response['error']}")
        else:
            print(f"✓ Status: {response.get('status', 'unknown')}")
            if "result" in response:
                print(f"💬 Response:\n{response['result']}")
            print(f"⏱️  Execution time: {response.get('execution_time_ms', 'N/A')}ms")


def demo_discovery_workflow() -> None:
    """Demo product discovery workflow."""
    print("\n" + "=" * 70)
    print("🔍 PRODUCT DISCOVERY WORKFLOW DEMO")
    print("=" * 70)
    print("\nThis workflow handles product search and recommendations:")
    print("  • Product searches")
    print("  • Category browsing")
    print("  • Recommendations")
    print("  • Featured items\n")

    for message in DEMO_MESSAGES["discovery"]:
        print(f"\n📝 User: {message}")
        print("-" * 70)

        response = send_chat_message(message)

        if "error" in response:
            print(f"❌ Error: {response['error']}")
        else:
            print(f"✓ Status: {response.get('status', 'unknown')}")
            if "result" in response:
                print(f"🛍️  Products:\n{response['result']}")
            print(f"⏱️  Execution time: {response.get('execution_time_ms', 'N/A')}ms")


def demo_support_workflow() -> None:
    """Demo customer support workflow."""
    print("\n" + "=" * 70)
    print("💬 CUSTOMER SUPPORT WORKFLOW DEMO")
    print("=" * 70)
    print("\nThis workflow handles customer support requests:")
    print("  • Returns and refunds")
    print("  • Order issues")
    print("  • Shipping status")
    print("  • Damaged items\n")

    for message in DEMO_MESSAGES["support"]:
        print(f"\n📝 User: {message}")
        print("-" * 70)

        response = send_chat_message(message)

        if "error" in response:
            print(f"❌ Error: {response['error']}")
        else:
            print(f"✓ Status: {response.get('status', 'unknown')}")
            if "result" in response:
                print(f"🎯 Help:\n{response['result']}")
            print(f"⏱️  Execution time: {response.get('execution_time_ms', 'N/A')}ms")


def demo_error_handling() -> None:
    """Demo error handling and fallbacks."""
    print("\n" + "=" * 70)
    print("⚠️  ERROR HANDLING & FALLBACKS DEMO")
    print("=" * 70)
    print("\nThis demo shows how the system handles errors gracefully:\n")

    # Test 1: Valid message (should succeed)
    print("1. Valid message (should succeed):")
    print("   User: 'What is my balance?'")
    response = send_chat_message("What is my balance?")
    print(f"   Status: ✓ {response.get('status', 'unknown')}")

    # Test 2: Message that might trigger fallback behavior
    print("\n2. Message that uses demo workflow:")
    print("   User: 'Find me red dresses'")
    response = send_chat_message("Find me red dresses")
    print(f"   Status: ✓ {response.get('status', 'unknown')}")
    if "result" in response:
        result = response["result"]
        if isinstance(result, str):
            print(f"   Found products: {result.count('£')} items listed")


def demo_all() -> None:
    """Run all demos."""
    print("\n\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  ACOS CHAT API - DEMO WORKFLOWS".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    print(f"\nAPI Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    demo_account_workflow()
    demo_discovery_workflow()
    demo_support_workflow()
    demo_error_handling()

    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\nKey takeaways:")
    print("  ✓ Demo workflows handle different types of customer requests")
    print("  ✓ Message content determines which workflow is invoked")
    print("  ✓ Fast operations (< 2s) execute synchronously")
    print("  ✓ Slow operations queue jobs for async execution")
    print("  ✓ Error handling with fallback strategies ensures reliability")
    print("\nFor more information, see:")
    print("  • DEPLOYMENT.md - How to run the Chat API")
    print("  • docs/CHAT_API.md - API documentation")
    print("  • tests/test_demo_workflows.py - Workflow tests")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Demo Chat API workflows")
    parser.add_argument(
        "--workflow",
        choices=["account", "discovery", "support", "errors", "all"],
        default="all",
        help="Which demo to run (default: all)",
    )
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help=f"Chat API base URL (default: {BASE_URL})",
    )

    args = parser.parse_args()
    BASE_URL = args.url

    if args.workflow == "account":
        demo_account_workflow()
    elif args.workflow == "discovery":
        demo_discovery_workflow()
    elif args.workflow == "support":
        demo_support_workflow()
    elif args.workflow == "errors":
        demo_error_handling()
    else:
        demo_all()
