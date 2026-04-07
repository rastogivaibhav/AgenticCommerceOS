#!/usr/bin/env python
"""Load testing script for Chat API using Locust.

This script performs load testing on the Chat API to measure:
- Request throughput
- Response times
- Error rates
- Workflow distribution

Usage:
    # Run with web UI
    locust -f scripts/load_test_chat_api.py --host=http://localhost:8000

    # Run headless
    locust -f scripts/load_test_chat_api.py --host=http://localhost:8000 \
           --users=100 --spawn-rate=10 --run-time=5m --headless

    # Run with custom distribution
    locust -f scripts/load_test_chat_api.py --host=http://localhost:8000 \
           --users=50 --spawn-rate=5 --run-time=10m --headless
"""

import random
import time
from locust import HttpUser, task, between, events
from datetime import datetime


class ChatWorkflowUser(HttpUser):
    """Simulated Chat API user performing workflow operations."""

    wait_time = between(0.5, 2.0)  # Wait 0.5-2 seconds between requests

    # Account workflow messages
    account_messages = [
        "What is my account balance?",
        "Show my account info",
        "How many loyalty points do I have?",
        "How do I change my password?",
    ]

    # Discovery workflow messages
    discovery_messages = [
        "Find me red dresses",
        "Show me shoes",
        "I need a jacket",
        "What do you recommend?",
        "Show me bags",
        "I'm looking for winter clothes",
    ]

    # Support workflow messages
    support_messages = [
        "I want to return this item",
        "Where is my order?",
        "My item arrived damaged",
        "What's the return policy?",
        "Help with my order",
        "How do I track my package?",
    ]

    def on_start(self):
        """Called when a new user starts."""
        self.user_id = f"U_user_{random.randint(1000, 9999)}"
        self.channel_id = f"C_channel_{random.randint(100, 999)}"
        self.request_count = 0
        self.error_count = 0

    @task(3)
    def account_workflow(self):
        """Account workflow - 30% of requests."""
        message = random.choice(self.account_messages)
        self._send_message(message, "account")

    @task(4)
    def discovery_workflow(self):
        """Discovery workflow - 40% of requests."""
        message = random.choice(self.discovery_messages)
        self._send_message(message, "discovery")

    @task(3)
    def support_workflow(self):
        """Support workflow - 30% of requests."""
        message = random.choice(self.support_messages)
        self._send_message(message, "support")

    def _send_message(self, message: str, workflow_type: str) -> None:
        """Send a chat message to the API.

        Args:
            message: Message text to send
            workflow_type: Type of workflow (account, discovery, support)
        """
        payload = {
            "source": "slack",
            "event": {
                "type": "message",
                "user": self.user_id,
                "channel": self.channel_id,
                "text": message,
                "ts": str(time.time()),
            },
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "timestamp": str(time.time()),
        }

        with self.client.post(
            "/api/chat/message",
            json=payload,
            catch_response=True,
        ) as response:
            self.request_count += 1

            if response.status_code == 200:
                response.success()
            else:
                self.error_count += 1
                response.failure(f"HTTP {response.status_code}")


# Event handlers for logging
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts."""
    print("\n" + "=" * 70)
    print("🚀 CHAT API LOAD TEST STARTED")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count}")
    print("=" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops."""
    print("\n" + "=" * 70)
    print("✅ CHAT API LOAD TEST COMPLETED")
    print("=" * 70)

    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Success Rate: {(1 - stats.total.fail_ratio) * 100:.1f}%")

    print(f"\nResponse Times:")
    print(f"  Min: {stats.total.min_response_time:.0f}ms")
    print(f"  Max: {stats.total.max_response_time:.0f}ms")
    print(f"  Average: {stats.total.avg_response_time:.0f}ms")
    print(f"  Median: {stats.total.median_response_time:.0f}ms")
    print(f"  95th percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  99th percentile: {stats.total.get_response_time_percentile(0.99):.0f}ms")

    print(f"\nThroughput:")
    if stats.total.total_response_time > 0:
        rps = stats.total.num_requests / (stats.total.total_response_time / 1000)
        print(f"  Requests/sec: {rps:.1f}")

    print("\nWorkflow Distribution:")
    for name, stat in stats.entries.items():
        if stat.num_requests > 0:
            percentage = (stat.num_requests / stats.total.num_requests) * 100
            print(
                f"  {name}: {stat.num_requests} requests ({percentage:.1f}%) - "
                f"Avg: {stat.avg_response_time:.0f}ms"
            )

    print("\n" + "=" * 70)


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Called when quitting the load test."""
    print("\n📊 Load test summary:")
    print("  • Test completed successfully")
    print("  • Check web UI for detailed metrics")
    print("  • Results can be exported for analysis")
