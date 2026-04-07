# Chat API Workflows Documentation

## Overview

The ACOS Chat API includes three demo workflows that demonstrate how the platform processes different types of customer requests:

1. **Account Workflow** - Handles account-related queries
2. **Discovery Workflow** - Handles product search and recommendations
3. **Support Workflow** - Handles customer support requests

## Architecture

### Message Processing Flow

```
Slack Message
    ↓
SlackAdapter (normalize message)
    ↓
SessionStore (retrieve/create session)
    ↓
HandlerRouter (detect workflow, route to handler)
    ↓
SyncHandler (< 2s)  OR  AsyncHandler (> 2s)
    ↓
Demo Workflow (account, discovery, support)
    ↓
Response (immediate or job status)
```

### Workflow Detection

Workflows are detected automatically based on message keywords:

- **Account**: balance, account, loyalty, points, settings, password
- **Discovery**: red dresses, shoes, jackets, bags, items, products
- **Support**: return, refund, damage, issue, shipping, delivery, order problem

### Sync vs Async Execution

- **Sync (< 2s)**: Fast workflows return results immediately
- **Async (> 2s)**: Slow workflows queue jobs for background processing

## Demo Workflows

### 1. Account Workflow

Handles account-related customer inquiries.

**Capabilities:**
- Account balance inquiries
- Account information display
- Loyalty points management
- Account settings guidance
- Password reset assistance

**Example Messages:**
```
"What is my account balance?"
"Show my account info"
"How many loyalty points do I have?"
"How do I change my password?"
```

**Response Example:**
```json
{
  "status": "success",
  "workflow_id": "wf-account",
  "result": "Your current account balance is £1,250.50. You have £500 available credit.",
  "execution_time_ms": 145
}
```

### 2. Discovery Workflow

Handles product discovery and recommendations.

**Capabilities:**
- Product category search
- Product recommendations
- Price and rating display
- Featured items listing
- Category browsing

**Example Messages:**
```
"Find me red dresses"
"Show me shoes"
"I need a jacket"
"What products are on sale?"
```

**Response Example:**
```json
{
  "status": "success",
  "workflow_id": "wf-discovery",
  "result": "Found 3 red dresses:\n• Red Midi Dress - £45 (4.5★)\n• Elegant Red Gown - £89.99 (4.8★)\n• Casual Red Shirt Dress - £32 (4.3★)\n\nWould you like more details?",
  "execution_time_ms": 198
}
```

### 3. Support Workflow

Handles customer support and issue resolution.

**Capabilities:**
- Return and refund processing
- Order status tracking
- Shipping information
- Damaged item claims
- Order issue resolution

**Example Messages:**
```
"I want to return this item"
"Where is my order?"
"My item arrived damaged"
"What's the return policy?"
```

**Response Example:**
```json
{
  "status": "success",
  "workflow_id": "wf-support",
  "result": "Returns are easy! You have 30 days to return most items.\nStatus: Ready to accept your return\nNext step: Click 'Start Return' in your Orders section\nNeed help? Reply with your order number.",
  "execution_time_ms": 167
}
```

## API Endpoints

### Send Message

**POST /api/chat/message**

Sends a message to the chat API for processing.

**Request:**
```json
{
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
```

**Response (Sync):**
```json
{
  "status": "success",
  "workflow_id": "wf-discovery",
  "result": "Found 3 red dresses...",
  "execution_time_ms": 198,
  "request_id": "req_abc123",
  "executed_at": "2026-04-07T10:30:45.123456+00:00"
}
```

**Response (Async):**
```json
{
  "status": "queued",
  "job_id": "job_xyz789",
  "workflow_id": "wf-complex-search",
  "request_id": "req_abc123",
  "polling_endpoint": "/api/jobs/job_xyz789/status",
  "result_endpoint": "/api/jobs/job_xyz789/result"
}
```

### Get Job Status

**GET /api/jobs/{job_id}/status**

Gets the status of an async job.

**Response:**
```json
{
  "job_id": "job_xyz789",
  "status": "processing",
  "workflow_id": "wf-discovery",
  "progress": 45,
  "created_at": "2026-04-07T10:30:40.000000+00:00"
}
```

### Get Job Result

**GET /api/jobs/{job_id}/result**

Gets the result of a completed async job.

**Response:**
```json
{
  "job_id": "job_xyz789",
  "status": "completed",
  "result": "Found 12 items matching your search...",
  "execution_time_ms": 3250,
  "completed_at": "2026-04-07T10:31:45.000000+00:00"
}
```

## Error Handling and Fallbacks

The Chat API includes comprehensive error handling with fallback strategies:

### Session Not Found

**Behavior:** If a session doesn't exist, the system automatically creates a new session.

**Response:**
```json
{
  "status": "recovered",
  "recovery_action": "created_new_session",
  "session_id": "sess_new_123"
}
```

### Workflow Not Found

**Behavior:** If a workflow can't be found, the system falls back to the default discovery workflow.

**Response:**
```json
{
  "status": "degraded",
  "recovery_action": "used_default_workflow",
  "workflow_id": "wf-discovery",
  "message": "Using default discovery workflow as fallback"
}
```

### Execution Timeout

**Behavior:** If a workflow takes too long, the system returns a partial result or timeout message.

**Response:**
```json
{
  "status": "timeout",
  "timeout_seconds": 5,
  "recovery_action": "returned_partial_result",
  "message": "Request took too long. Please try again or simplify your query."
}
```

## Usage Examples

### Python

```python
import requests

api_url = "http://localhost:8000/api/chat/message"

message = {
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

response = requests.post(api_url, json=message)
result = response.json()

print(f"Status: {result['status']}")
print(f"Result: {result['result']}")
```

### cURL

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "source": "slack",
    "event": {
      "type": "message",
      "user": "U12345",
      "channel": "C12345",
      "text": "What is my balance?",
      "ts": "1234567890.123456"
    },
    "user_id": "U12345",
    "channel_id": "C12345",
    "timestamp": "1234567890.123456"
  }'
```

## Testing

### Unit Tests

Run demo workflow tests:
```bash
pytest tests/test_demo_workflows.py -v
```

### Error Handling Tests

Run error handling tests:
```bash
pytest tests/test_error_handling.py -v
```

### Integration Tests

Run all chat gateway tests:
```bash
pytest tests/integration/test_chat_gateway_slack.py -v
```

## Demo Script

Run the interactive demo:
```bash
python scripts/demo_chat_workflows.py
```

Or run specific workflow demo:
```bash
python scripts/demo_chat_workflows.py --workflow account
python scripts/demo_chat_workflows.py --workflow discovery
python scripts/demo_chat_workflows.py --workflow support
```

## Load Testing

Run load tests with Locust:

**With Web UI:**
```bash
locust -f scripts/load_test_chat_api.py --host=http://localhost:8000
```

**Headless (100 users, 5m duration):**
```bash
locust -f scripts/load_test_chat_api.py --host=http://localhost:8000 \
       --users=100 --spawn-rate=10 --run-time=5m --headless
```

## Performance Characteristics

### Expected Response Times

| Workflow | P50 | P95 | P99 |
|----------|-----|-----|-----|
| Account | 120ms | 250ms | 400ms |
| Discovery | 150ms | 300ms | 500ms |
| Support | 140ms | 280ms | 450ms |

### Expected Throughput

- **Single instance**: 100-200 requests/second
- **With error recovery**: 95-190 requests/second (5% fallback overhead)

## Workflow Extensibility

To add a new workflow:

1. **Create workflow class** in `apps/chat_api/workflows/demo.py`
2. **Implement execute()** method
3. **Add to workflow factory** in `get_demo_workflow()`
4. **Update detection** in `BaseHandler._detect_workflow_id()`
5. **Add tests** in `tests/test_demo_workflows.py`

Example:
```python
class CustomWorkflow:
    def execute(self, message_text: str, context: dict) -> str:
        text = message_text.lower()
        if "custom" in text:
            return "Custom workflow response"
        return "Default response"
```

## Troubleshooting

### API Not Responding

**Problem:** Connection error to API

**Solution:**
1. Check API is running: `docker-compose up` or `uvicorn apps.chat_api.main:app`
2. Verify URL: default is `http://localhost:8000`
3. Check logs for errors

### Workflow Not Detected

**Problem:** Message doesn't trigger expected workflow

**Solution:**
1. Check message keywords match detection logic
2. Review `BaseHandler._detect_workflow_id()` for keyword patterns
3. Falls back to discovery workflow if no match

### Timeouts on Load

**Problem:** Requests timing out under load

**Solution:**
1. Reduce concurrent users
2. Increase server resources
3. Check for database bottlenecks
4. Review application logs for errors

## Additional Resources

- **DEPLOYMENT.md** - How to deploy the Chat API
- **API.md** - Full API reference
- **tests/** - Comprehensive test suite
- **scripts/** - Demo and load testing scripts

## Summary

The ACOS Chat API provides a flexible, scalable platform for handling customer requests across multiple domains. The demo workflows showcase automatic message routing, sync/async execution, and comprehensive error handling with fallback strategies.
