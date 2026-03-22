# ACOS Control Plane - API Reference

**Complete API endpoint documentation for developers and integrations**

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Workflow Endpoints](#workflow-endpoints)
4. [Experiment Endpoints](#experiment-endpoints)
5. [Analytics Endpoints](#analytics-endpoints)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## API Overview

### Base URL

```
http://localhost:8000  (Development)
https://yourdomain.com (Production)
```

### API Documentation

Two interactive documentation interfaces:

**Swagger UI (OpenAPI):**
```
http://localhost:8000/docs
```

**ReDoc (Alternative UI):**
```
http://localhost:8000/redoc
```

**Health Check:**
```
GET http://localhost:8000/health
```

### Response Format

All responses are JSON:

**Success Response:**
```json
{
  "success": true,
  "data": { /* response data */ },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2026-03-22T15:30:00Z"
}
```

---

## Authentication

### API Key Authentication

All endpoints (except `/health`) require authentication via API key.

**How to Use:**

Include API key in request header:
```
Authorization: Bearer YOUR_API_KEY_HERE
```

### Obtaining an API Key

**Development:**
```bash
# Generate test API key
export API_KEY=$(openssl rand -hex 32)
echo $API_KEY
```

**Production:**
- Contact administrator for API key
- Keys are unique per user/application
- Treat keys as sensitive (like passwords)
- Rotate regularly for security

### Example Request with Auth

```bash
curl -X GET http://localhost:8000/workflows \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json"
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:8000/workflows', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  }
});
```

**Python Example:**
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}

response = requests.get('http://localhost:8000/workflows', headers=headers)
```

---

## Workflow Endpoints

### List Workflows

**Endpoint:**
```
GET /workflows
```

**Description:** Retrieve all workflows for the authenticated user.

**Parameters:**
- None required

**Query Parameters:**
| Name | Type | Optional | Description |
|------|------|----------|-------------|
| `skip` | integer | Yes | Skip first N workflows (default: 0) |
| `limit` | integer | Yes | Return max N workflows (default: 100) |
| `status` | string | Yes | Filter by status: draft, published, archived |

**Request Example:**
```bash
curl -X GET "http://localhost:8000/workflows?skip=0&limit=10&status=published" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "workflow-001",
      "name": "Search Workflow",
      "status": "published",
      "version": 2,
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-22T14:30:00Z",
      "steps": [
        {
          "id": "step-001",
          "type": "input",
          "name": "User Query",
          "config": {
            "field_name": "query",
            "field_type": "string",
            "required": true
          }
        }
      ]
    }
  ],
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Get Workflow

**Endpoint:**
```
GET /workflows/{workflow_id}
```

**Description:** Retrieve details of a specific workflow.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workflow_id` | string | Yes | ID of the workflow |

**Request Example:**
```bash
curl -X GET http://localhost:8000/workflows/workflow-001 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "workflow-001",
    "name": "Search Workflow",
    "description": "AI-powered search workflow",
    "status": "published",
    "version": 2,
    "created_at": "2026-03-20T10:00:00Z",
    "updated_at": "2026-03-22T14:30:00Z",
    "created_by": "user@example.com",
    "steps": [
      {
        "id": "step-001",
        "type": "input",
        "name": "User Query",
        "position": 0,
        "config": {
          "field_name": "query",
          "field_type": "string",
          "required": true
        }
      },
      {
        "id": "step-002",
        "type": "agent_call",
        "name": "Search Agent",
        "position": 1,
        "config": {
          "agent_type": "search",
          "timeout": 30,
          "retries": 2
        }
      },
      {
        "id": "step-003",
        "type": "output",
        "name": "Return Results",
        "position": 2,
        "config": {
          "output_format": "json"
        }
      }
    ]
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Workflow not found",
  "code": "WORKFLOW_NOT_FOUND",
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Create Workflow

**Endpoint:**
```
POST /workflows
```

**Description:** Create a new workflow.

**Request Body:**
```json
{
  "name": "New Search Workflow",
  "description": "Optional description",
  "steps": [
    {
      "type": "input",
      "name": "Query Input",
      "config": {
        "field_name": "search_query",
        "field_type": "string",
        "required": true
      }
    },
    {
      "type": "agent_call",
      "name": "Search Agent",
      "config": {
        "agent_type": "search",
        "timeout": 30,
        "parameters": {
          "depth": "standard"
        }
      }
    },
    {
      "type": "output",
      "name": "Results",
      "config": {
        "output_format": "json",
        "include_metadata": true
      }
    }
  ]
}
```

**Request Example:**
```bash
curl -X POST http://localhost:8000/workflows \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Search Workflow",
    "steps": [...]
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "workflow-new-123",
    "name": "Search Workflow",
    "status": "draft",
    "version": 1,
    "created_at": "2026-03-22T15:30:00Z",
    "steps": [
      {
        "id": "step-001",
        "type": "input",
        "name": "Query Input",
        "config": { ... }
      }
    ]
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Invalid workflow structure",
  "code": "INVALID_WORKFLOW",
  "details": {
    "steps": ["At least one step is required"]
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Update Workflow

**Endpoint:**
```
PATCH /workflows/{workflow_id}
```

**Description:** Update a draft workflow.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workflow_id` | string | Yes | ID of the workflow |

**Request Body (fields to update):**
```json
{
  "name": "Updated Workflow Name",
  "description": "Updated description",
  "steps": [ /* updated steps */ ]
}
```

**Request Example:**
```bash
curl -X PATCH http://localhost:8000/workflows/workflow-001 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Workflow Name",
    "steps": [...]
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "workflow-001",
    "name": "Updated Workflow Name",
    "status": "draft",
    "version": 1,
    "updated_at": "2026-03-22T15:35:00Z"
  },
  "timestamp": "2026-03-22T15:35:00Z"
}
```

**Error Response (409 Conflict):**
```json
{
  "success": false,
  "error": "Cannot update published workflow",
  "code": "INVALID_STATUS",
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Create Workflow Version

**Endpoint:**
```
POST /workflows/{workflow_id}/versions
```

**Description:** Create a new version of a published workflow.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workflow_id` | string | Yes | ID of the workflow |

**Request Body:**
```json
{
  "changes": "Updated agent timeout",
  "steps": [ /* new steps */ ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "workflow-001",
    "version": 3,
    "status": "draft",
    "created_at": "2026-03-22T15:30:00Z"
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Publish Workflow

**Endpoint:**
```
POST /workflows/{workflow_id}/publish
```

**Description:** Publish a draft workflow to production.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "workflow-001",
    "status": "published",
    "version": 1,
    "published_at": "2026-03-22T15:30:00Z"
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

---

## Experiment Endpoints

### Create Experiment

**Endpoint:**
```
POST /experiments
```

**Description:** Create a new A/B experiment.

**Request Body:**
```json
{
  "name": "Search Timeout Test",
  "workflow_id": "workflow-001",
  "sample_size": 100,
  "variant_a": {
    "name": "Baseline",
    "config": {
      "timeout": 30,
      "retries": 2
    }
  },
  "variant_b": {
    "name": "Fast Timeout",
    "config": {
      "timeout": 15,
      "retries": 2
    }
  }
}
```

**Request Example:**
```bash
curl -X POST http://localhost:8000/experiments \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Search Timeout Test",
    "workflow_id": "workflow-001",
    "sample_size": 100,
    "variant_a": { "name": "Baseline", "config": { "timeout": 30 } },
    "variant_b": { "name": "Fast", "config": { "timeout": 15 } }
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "experiment-001",
    "name": "Search Timeout Test",
    "workflow_id": "workflow-001",
    "status": "created",
    "sample_size": 100,
    "variant_a": {
      "name": "Baseline",
      "config": { "timeout": 30, "retries": 2 }
    },
    "variant_b": {
      "name": "Fast",
      "config": { "timeout": 15, "retries": 2 }
    },
    "created_at": "2026-03-22T15:30:00Z"
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### List Experiments

**Endpoint:**
```
GET /experiments
```

**Description:** Retrieve all experiments.

**Query Parameters:**
| Name | Type | Optional | Description |
|------|------|----------|-------------|
| `skip` | integer | Yes | Skip first N (default: 0) |
| `limit` | integer | Yes | Return max N (default: 100) |
| `status` | string | Yes | Filter: created, running, completed |
| `workflow_id` | string | Yes | Filter by workflow |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "experiment-001",
      "name": "Search Timeout Test",
      "workflow_id": "workflow-001",
      "status": "completed",
      "sample_size": 100,
      "started_at": "2026-03-22T14:00:00Z",
      "completed_at": "2026-03-22T14:30:00Z"
    }
  ],
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Get Experiment

**Endpoint:**
```
GET /experiments/{experiment_id}
```

**Description:** Retrieve experiment details.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "experiment-001",
    "name": "Search Timeout Test",
    "workflow_id": "workflow-001",
    "status": "completed",
    "sample_size": 100,
    "variant_a": {
      "name": "Baseline",
      "config": { "timeout": 30 }
    },
    "variant_b": {
      "name": "Fast",
      "config": { "timeout": 15 }
    },
    "results": {
      "variant_a": {
        "total_runs": 50,
        "avg_score": 78.5,
        "success_rate": 0.95,
        "avg_cost": 2.00
      },
      "variant_b": {
        "total_runs": 50,
        "avg_score": 75.2,
        "success_rate": 0.90,
        "avg_cost": 1.50
      },
      "winner": "variant_a",
      "confidence": 0.92
    },
    "created_at": "2026-03-22T14:00:00Z"
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Run Experiment

**Endpoint:**
```
POST /experiments/{experiment_id}/run
```

**Description:** Execute an experiment (start running variant tests).

**Request Body:**
```json
{
  "start_immediately": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "experiment-001",
    "status": "running",
    "progress": {
      "variant_a": { "completed": 0, "total": 50 },
      "variant_b": { "completed": 0, "total": 50 }
    },
    "started_at": "2026-03-22T15:30:00Z"
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Get Experiment Results

**Endpoint:**
```
GET /experiments/{experiment_id}/results
```

**Description:** Get results for completed experiment.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "variant_a": {
      "name": "Baseline",
      "total_runs": 50,
      "avg_score": 78.5,
      "std_dev": 8.2,
      "success_rate": 0.95,
      "avg_cost": 2.00,
      "min_score": 45.0,
      "max_score": 95.0
    },
    "variant_b": {
      "name": "Fast",
      "total_runs": 50,
      "avg_score": 75.2,
      "std_dev": 9.1,
      "success_rate": 0.90,
      "avg_cost": 1.50,
      "min_score": 40.0,
      "max_score": 92.0
    },
    "comparison": {
      "winner": "variant_a",
      "score_difference": 3.3,
      "confidence": 0.92,
      "statistically_significant": true,
      "recommended_action": "Deploy variant_a"
    }
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

---

## Analytics Endpoints

### Get Metrics

**Endpoint:**
```
GET /analytics/metrics
```

**Description:** Get aggregated system metrics.

**Query Parameters:**
| Name | Type | Optional | Description |
|------|------|----------|-------------|
| `period` | string | Yes | Time range: 7d, 30d, 90d, all (default: 30d) |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_runs": 1234,
    "avg_score": 81.5,
    "total_cost": 2340.56,
    "success_rate": 0.97,
    "avg_execution_time": 2.34,
    "workflows_count": 5,
    "experiments_count": 12,
    "period": "30d",
    "updated_at": "2026-03-22T15:30:00Z"
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Get Time Series Data

**Endpoint:**
```
GET /analytics/timeseries
```

**Description:** Get daily metrics over time.

**Query Parameters:**
| Name | Type | Optional | Description |
|------|------|----------|-------------|
| `period` | string | Yes | Time range: 7d, 30d, 90d (default: 30d) |
| `metric` | string | Yes | Metric: runs, score, cost, success_rate |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "metric": "runs",
    "period": "7d",
    "data": [
      {
        "date": "2026-03-16",
        "value": 145,
        "trend": "up"
      },
      {
        "date": "2026-03-17",
        "value": 152,
        "trend": "up"
      },
      {
        "date": "2026-03-18",
        "value": 148,
        "trend": "down"
      },
      {
        "date": "2026-03-19",
        "value": 168,
        "trend": "up"
      },
      {
        "date": "2026-03-20",
        "value": 156,
        "trend": "down"
      },
      {
        "date": "2026-03-21",
        "value": 175,
        "trend": "up"
      },
      {
        "date": "2026-03-22",
        "value": 182,
        "trend": "up"
      }
    ]
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Get Workflow Metrics

**Endpoint:**
```
GET /analytics/workflows
```

**Description:** Get metrics broken down by workflow.

**Query Parameters:**
| Name | Type | Optional | Description |
|------|------|----------|-------------|
| `skip` | integer | Yes | Skip first N (default: 0) |
| `limit` | integer | Yes | Return max N (default: 100) |
| `sort_by` | string | Yes | Sort field: score, runs, cost (default: runs) |
| `order` | string | Yes | Order: asc, desc (default: desc) |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "workflow_id": "workflow-001",
      "name": "Search Workflow",
      "status": "active",
      "total_runs": 456,
      "avg_score": 82.1,
      "std_dev": 7.5,
      "total_cost": 1234.56,
      "success_rate": 0.98,
      "avg_execution_time": 2.1,
      "last_run": "2026-03-22T15:25:00Z"
    },
    {
      "workflow_id": "workflow-002",
      "name": "Analysis Workflow",
      "status": "active",
      "total_runs": 234,
      "avg_score": 78.5,
      "std_dev": 8.2,
      "total_cost": 890.12,
      "success_rate": 0.95,
      "avg_execution_time": 1.8,
      "last_run": "2026-03-22T15:20:00Z"
    }
  ],
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Export Analytics Data

**Endpoint:**
```
GET /analytics/export
```

**Description:** Export analytics data in specified format.

**Query Parameters:**
| Name | Type | Optional | Description |
|------|------|----------|-------------|
| `format` | string | Yes | csv or json (default: csv) |
| `period` | string | Yes | Time range: 7d, 30d, 90d, all |

**Request Example (CSV):**
```bash
curl -X GET "http://localhost:8000/analytics/export?format=csv&period=30d" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > analytics.csv
```

**Request Example (JSON):**
```bash
curl -X GET "http://localhost:8000/analytics/export?format=json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > analytics.json
```

**CSV Response:**
```
Workflow Name,Status,Total Runs,Avg Score,Total Cost,Success Rate
Search,Active,456,82.1,1234.56,0.98
Analysis,Active,234,78.5,890.12,0.95
Summarize,Active,544,85.2,1256.80,0.99
```

**JSON Response:**
```json
{
  "success": true,
  "data": {
    "export_date": "2026-03-22T15:30:00Z",
    "period": "30d",
    "workflows": [
      {
        "name": "Search",
        "total_runs": 456,
        "avg_score": 82.1,
        "total_cost": 1234.56,
        "success_rate": 0.98
      }
    ]
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing/invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Operation conflicts with state |
| 422 | Unprocessable | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |
| 503 | Service Unavailable | Server temporarily down |

### Error Response Structure

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field_name": ["Error for this field"],
    "another_field": ["Error details"]
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

### Common Errors

**Missing API Key:**
```json
{
  "success": false,
  "error": "Missing authorization header",
  "code": "MISSING_AUTH",
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Invalid API Key:**
```json
{
  "success": false,
  "error": "Invalid API key",
  "code": "INVALID_AUTH",
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Validation Error:**
```json
{
  "success": false,
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "name": ["Name is required"],
    "sample_size": ["Sample size must be between 10 and 1000"]
  },
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Resource Not Found:**
```json
{
  "success": false,
  "error": "Workflow not found",
  "code": "WORKFLOW_NOT_FOUND",
  "timestamp": "2026-03-22T15:30:00Z"
}
```

---

## Rate Limiting

### Rate Limits

All API endpoints are rate-limited:

**Limit:** 100 requests per minute per API key

**Headers Returned:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1648000260
```

### Handling Rate Limits

**When Rate Limited (429 Response):**
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60,
  "timestamp": "2026-03-22T15:30:00Z"
}
```

**Recommended Response:**

```python
import requests
import time

def call_api_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            retry_after = response.json()['retry_after']
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue

        return response

    raise Exception("Max retries exceeded")
```

---

## Examples

### Example 1: Creating and Running a Workflow

**Step 1: Create Workflow**
```bash
curl -X POST http://localhost:8000/workflows \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Workflow",
    "steps": [
      {
        "type": "input",
        "name": "Query",
        "config": {
          "field_name": "search_query",
          "field_type": "string",
          "required": true
        }
      },
      {
        "type": "output",
        "name": "Results",
        "config": {
          "output_format": "json"
        }
      }
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "wf-abc123",
    "name": "My First Workflow",
    "status": "draft"
  }
}
```

**Step 2: Publish Workflow**
```bash
curl -X POST http://localhost:8000/workflows/wf-abc123/publish \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "wf-abc123",
    "status": "published"
  }
}
```

### Example 2: Running an A/B Experiment

**Create Experiment:**
```bash
curl -X POST http://localhost:8000/experiments \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Speed Test",
    "workflow_id": "wf-abc123",
    "sample_size": 50,
    "variant_a": {
      "name": "Standard",
      "config": {"timeout": 30}
    },
    "variant_b": {
      "name": "Fast",
      "config": {"timeout": 15}
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "exp-xyz789",
    "status": "created"
  }
}
```

**Run Experiment:**
```bash
curl -X POST http://localhost:8000/experiments/exp-xyz789/run \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Get Results (after completion):**
```bash
curl -X GET http://localhost:8000/experiments/exp-xyz789/results \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "variant_a": {
      "avg_score": 78.5,
      "success_rate": 0.95
    },
    "variant_b": {
      "avg_score": 75.2,
      "success_rate": 0.90
    },
    "winner": "variant_a"
  }
}
```

### Example 3: Accessing Analytics

**Get Current Metrics:**
```bash
curl -X GET "http://localhost:8000/analytics/metrics" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_runs": 1234,
    "avg_score": 81.5,
    "total_cost": 2340.56,
    "success_rate": 0.97
  }
}
```

**Get Daily Trends:**
```bash
curl -X GET "http://localhost:8000/analytics/timeseries?period=7d&metric=runs" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Export Data:**
```bash
curl -X GET "http://localhost:8000/analytics/export?format=csv&period=30d" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -o metrics.csv
```

### Example 4: JavaScript/Fetch Integration

```javascript
const API_KEY = 'your-api-key-here';
const BASE_URL = 'http://localhost:8000';

// Helper function
async function apiCall(endpoint, options = {}) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`${error.code}: ${error.error}`);
  }

  return response.json();
}

// Usage examples
async function example() {
  try {
    // List workflows
    const workflows = await apiCall('/workflows');
    console.log('Workflows:', workflows.data);

    // Get specific workflow
    const workflow = await apiCall('/workflows/wf-abc123');
    console.log('Workflow:', workflow.data);

    // Create experiment
    const experiment = await apiCall('/experiments', {
      method: 'POST',
      body: JSON.stringify({
        name: 'Speed Test',
        workflow_id: 'wf-abc123',
        sample_size: 50,
        variant_a: { name: 'A', config: { timeout: 30 } },
        variant_b: { name: 'B', config: { timeout: 15 } }
      })
    });
    console.log('Experiment created:', experiment.data);

  } catch (error) {
    console.error('API Error:', error.message);
  }
}
```

### Example 5: Python Integration

```python
import requests

API_KEY = 'your-api-key-here'
BASE_URL = 'http://localhost:8000'

class AcosClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def list_workflows(self):
        response = requests.get(
            f'{BASE_URL}/workflows',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['data']

    def create_experiment(self, name, workflow_id, sample_size, variant_a, variant_b):
        response = requests.post(
            f'{BASE_URL}/experiments',
            headers=self.headers,
            json={
                'name': name,
                'workflow_id': workflow_id,
                'sample_size': sample_size,
                'variant_a': variant_a,
                'variant_b': variant_b
            }
        )
        response.raise_for_status()
        return response.json()['data']

    def get_metrics(self, period='30d'):
        response = requests.get(
            f'{BASE_URL}/analytics/metrics?period={period}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['data']

# Usage
client = AcosClient(API_KEY)
workflows = client.list_workflows()
print(f"Found {len(workflows)} workflows")

metrics = client.get_metrics()
print(f"Total runs: {metrics['total_runs']}")
```

---

## Webhooks (Future)

Webhooks for event notifications are planned for a future release.

**Planned Events:**
- Workflow published
- Experiment completed
- Alert triggered (low success rate, high cost)

**Coming:** v1.1 release

---

**Questions?** Review [INSTALLATION.md](./INSTALLATION.md) for local setup or contact support.

**Last Updated:** March 22, 2026
**Version:** 1.0.0
