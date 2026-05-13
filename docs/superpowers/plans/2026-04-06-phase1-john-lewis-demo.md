# Phase 1: John Lewis Demo Implementation Plan (4 Weeks)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver working John Lewis demo with Slack integration, async job execution, and multi-agent orchestration running live in 4 weeks.

**Architecture:** Slack → Chat Gateway → normalize → route (sync/async) → Celery job queue → workflow executor → Slack response

**Tech Stack:** FastAPI, Slack Bolt SDK, Celery, Redis, PostgreSQL, Pydantic

---

## Week-by-Week Timeline

### Week 1: Foundation (Job Queue + Session Store)
**Output:** Celery workers, Redis, job queue, session management all working locally

- Task 1: Job Queue Service (Celery + Redis)
- Task 2: Session/Context Store

### Week 2: Chat Gateway (Slack Integration)
**Output:** Slack messages normalized, routed to handlers

- Task 3: Chat Gateway API Structure
- Task 4: Slack Adapter & Normalization

### Week 3: Execution Handlers & Integration
**Output:** Sync and async flows working end-to-end

- Task 5: Sync & Async Handlers
- Task 6: Message & Job Endpoints

### Week 4: Demo Workflows & Polish
**Output:** 3 sample workflows, error handling, demo-ready

- Task 7: Demo Workflows (3x discovery, support, account)
- Task 8: Error Handling & Retry Logic
- Task 9: Demo Testing & Documentation

---

## Critical Path Tasks

### Task 1: Job Queue Service (8 hours)

**Purpose:** Establish async execution foundation

**Files to Create:**
- `acosplatform/job_queue/__init__.py`
- `acosplatform/job_queue/models.py`
- `acosplatform/job_queue/celery_app.py`
- `acosplatform/job_queue/service.py`
- `tests/unit/job_queue/test_service.py`

**Key Implementation:**
- Celery app with Redis broker
- Job lifecycle (QUEUED → PROCESSING → COMPLETED/FAILED)
- Redis caching for fast status lookups
- Job TTL (24 hours)

**Deliverable:** `JobQueueService` with create_job(), get_job(), mark_job_*() methods

---

### Task 2: Session Store (6 hours)

**Purpose:** Maintain conversation context across messages

**Files to Create:**
- `acosplatform/session/__init__.py`
- `acosplatform/session/models.py`
- `acosplatform/session/store.py`
- `tests/unit/session/test_store.py`

**Key Implementation:**
- Redis-backed session storage with 24h TTL
- Conversation history (list of messages)
- User context (preferences, cart, etc)
- Session lifecycle (active → closed → archived)

**Deliverable:** `SessionStore` with create_session(), add_message(), update_context() methods

---

### Task 3: Chat Gateway API (8 hours)

**Purpose:** Build FastAPI app structure

**Files to Create:**
- `apps/chat_api/main.py` - FastAPI app
- `apps/chat_api/config.py` - Configuration
- `apps/chat_api/models/chat.py` - Request/response models
- `apps/chat_api/routers/message.py` - Message endpoint (stub)
- `apps/chat_api/routers/jobs.py` - Job status endpoints (stub)
- `Dockerfile.chat_api`
- Update: `docker-compose.yml`

**Key Implementation:**
- FastAPI on port 8001
- CORS enabled (for Slack webhooks)
- Health check endpoint
- Docker compose with Redis, Celery, Chat API services

**Deliverable:** Chat Gateway running on http://localhost:8001 with `/health` endpoint working

---

### Task 4: Slack Adapter (6 hours)

**Purpose:** Normalize Slack events to internal format

**Files to Create:**
- `apps/chat_api/adapters/base.py` - Abstract adapter
- `apps/chat_api/adapters/slack.py` - Slack implementation
- `tests/unit/chat_api/test_slack_adapter.py`

**Key Implementation:**
- Parse Slack message events
- Extract user_id, channel_id, message text
- Handle threaded messages
- Send messages back to Slack

**Deliverable:** SlackAdapter that converts Slack events to NormalizedMessage

---

### Task 5: Sync/Async Handlers (8 hours)

**Purpose:** Route messages to appropriate executor

**Files to Create:**
- `apps/chat_api/handlers/router.py` - Route decision logic
- `apps/chat_api/handlers/sync.py` - Sync executor
- `apps/chat_api/handlers/async.py` - Async job submission
- `tests/integration/test_sync_async_routing.py`

**Key Implementation:**
- Route based on workflow timeout (2s threshold)
- Sync: Execute inline, return immediately
- Async: Queue job, return job_id

**Deliverable:** Routing logic that splits requests correctly

---

### Task 6: Chat Endpoints (10 hours)

**Purpose:** Wire message input to execution pipeline

**Files to Modify:**
- `apps/chat_api/routers/message.py` - Full implementation
- `apps/chat_api/routers/jobs.py` - Full implementation
- `tests/integration/test_chat_gateway_slack.py`

**Key Flows:**
1. POST /api/chat/message
   - Normalize message (Slack adapter)
   - Create/get session
   - Route to handler (sync/async)
   - Return response or job_id

2. GET /api/jobs/{job_id}/status
   - Poll job progress
   - Return current step + ETA

3. GET /api/jobs/{job_id}/result
   - Get final result
   - Return 202 if still processing

**Deliverable:** Full message → execution pipeline working

---

### Task 7: Demo Workflows (12 hours)

**Purpose:** Create 3 workflows for John Lewis demo

**Workflows:**
1. **wf-account-query** (sync, < 1s)
   - Input: "What's my balance?"
   - Output: "Your balance is £1,250"
   - Steps: Lookup account → Return balance

2. **wf-discovery** (async, 8-10s)
   - Input: "Show me blue dresses under £50"
   - Output: Product list with recommendations
   - Steps: Search → Filter by price → Filter by free returns → Recommend

3. **wf-support** (async, 5-8s)
   - Input: "I want to return this item"
   - Output: Return instructions + label
   - Steps: Verify order → Check return window → Generate label → Send instructions

**Files to Create/Modify:**
- `acosplatform/workflow_execution/executor.py` - Workflow executor
- `acosplatform/workflows/service.py` - Add demo workflows to registry
- `tests/e2e/test_slack_demo_workflows.py`

**Key Implementation:**
- Workflow executor that runs steps sequentially/parallel
- Each step returns output for next step
- Mock external services (product DB, account service)
- Format responses as natural language for Slack

**Deliverable:** 3 working workflows, demo-ready

---

### Task 8: Error Handling (6 hours)

**Purpose:** Handle failures gracefully

**Implementation:**
- Catch missing workflows → fallback response
- Catch job execution errors → mark job failed + error message
- Catch Slack API errors → log + retry
- Timeout protection on all Celery tasks (30min)

**Deliverable:** Jobs fail gracefully with meaningful error messages

---

### Task 9: Demo Testing & Documentation (8 hours)

**Purpose:** Verify end-to-end demo works

**Testing:**
- Load test: 10 concurrent Slack sessions
- Latency check: sync < 2s, async < 30s
- Error scenarios: invalid queries, service failures
- Manual demo run with sample questions

**Documentation:**
- How to run demo (setup Slack bot, env vars)
- Sample queries to ask during demo
- Troubleshooting guide
- Architecture diagram for presentation

**Deliverable:** Demo runs smoothly, documented, ready for customer

---

## File Structure Summary

```
apps/chat_api/
  ├── main.py
  ├── config.py
  ├── models/
  │   ├── chat.py
  │   └── job.py
  ├── routers/
  │   ├── message.py
  │   └── jobs.py
  └── adapters/
      ├── base.py
      └── slack.py

acosplatform/
  ├── job_queue/
  │   ├── service.py
  │   ├── models.py
  │   └── celery_app.py
  ├── session/
  │   ├── store.py
  │   └── models.py
  └── workflow_execution/
      └── executor.py

tests/
  ├── unit/
  │   ├── job_queue/test_service.py
  │   ├── session/test_store.py
  │   └── chat_api/test_slack_adapter.py
  ├── integration/
  │   ├── test_sync_async_routing.py
  │   └── test_chat_gateway_slack.py
  └── e2e/
      └── test_slack_demo_workflows.py

docker-compose.yml (updated)
Dockerfile.chat_api (new)
.env.example (updated)
```

---

## Success Criteria (End of Week 4)

### Functional
- ✅ Chat Gateway API running on port 8001
- ✅ Slack messages normalize correctly
- ✅ Messages route to sync or async handlers appropriately
- ✅ Async jobs queue to Celery and execute
- ✅ Job status polling returns accurate progress
- ✅ 3 demo workflows execute and return results
- ✅ Slack adapter sends responses back to channel

### Performance
- ✅ Sync queries respond in < 2 seconds
- ✅ Async jobs start within 5 seconds
- ✅ Can handle 10 concurrent Slack conversations

### Quality
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Error handling for missing workflows, failed jobs
- ✅ Logs include request ID tracking

### Demo Readiness
- ✅ Slack bot installed in test workspace
- ✅ 3 workflows loaded with sample data
- ✅ Demo script with ~10 sample questions
- ✅ Documented setup instructions
- ✅ Ready for live customer demo (4 hours max without downtime)

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Slack bot token issues | Can't connect | Use test workspace, verify token early (Day 1) |
| Celery/Redis startup | Jobs won't queue | Docker compose health checks, local testing first |
| Job timeout (30min limit) | Demo workflows blocked | Test with realistic data, optimize step execution |
| Workflow not found | 500 error | Fallback response with helpful message |
| Redis memory | Sessions lost | Configure TTL (24h), monitor usage |
| Slack API rate limits | Message delivery fails | Implement exponential backoff |

---

## Next Steps

1. **Get approval** on this plan
2. **Week 1 kickoff**: Task 1 (Job Queue)
3. **Daily standups**: 15 min, track progress against tasks
4. **Weekly demos**: Show progress to stakeholders (Fri EOD)
5. **Go-live**: Friday EOW4 with John Lewis

---

**Document Version:** 1.0
**Created:** 2026-04-06
**Status:** Ready for Execution

