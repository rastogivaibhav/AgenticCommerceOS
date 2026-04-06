# ACOS Multi-Channel Agent Orchestration Platform
## Executive Technology Roadmap for CTO | CIO | Enterprise Architects

**Date:** April 6, 2026
**Classification:** Internal - Executive Stakeholders
**Prepared For:** Chief Technology Officer, Chief Information Officer, Enterprise Architects

---

## Executive Summary

ACOS is evolving from a backend workflow orchestration API to an **enterprise-grade multi-channel agent platform**. This transformation enables:

- **Immediate Demo Value:** John Lewis customer sees AI agents solving real problems via chat (4 weeks)
- **Enterprise Scale:** Production deployment handling 10,000+ concurrent conversations (12 weeks)
- **Strategic Flexibility:** Swap AI providers, add tools, or integrate new channels WITHOUT code changes (via MCPs)
- **Cost Control:** Transparent, granular cost tracking per workflow, customer, and AI provider
- **Risk Mitigation:** 99.95% uptime SLA with graceful degradation and multi-region support

---

## I. Business Drivers

### The Opportunity
- **Customer Expectation Shift:** Consumers expect AI-powered assistance across multiple channels (chat, messaging, social)
- **Competitive Pressure:** Retailers using ChatGPT and custom agents to improve customer experience and reduce support costs
- **Revenue Enablement:** Intelligent product recommendations drive higher AOV and conversion rates
- **Operational Efficiency:** AI agents handling 40-60% of support requests, reducing human workload by 50%

### John Lewis Case Study
- **Goal:** Demonstrate multi-agent orchestration to world's largest department store
- **Timeline:** 4-week sprint to working demo (Slack integration, 3 workflows, multi-agent execution)
- **Win Condition:** Live demo handling customer queries with intelligent agent coordination
- **Expansion Path:** If successful, negotiate enterprise deal for 50+ store locations, 5M+ annual customer interactions

---

## II. Technical Architecture: Key Decisions

### Decision 1: Chat Gateway Pattern (NOT Per-Platform Integration)
**Problem:** If we build Slack → Workflow, Teams → Workflow, WhatsApp → Workflow separately, we duplicate logic 5+ times.

**Solution:** Single **Chat Gateway** that normalizes all platform messages, maintaining one workflow engine.

```
What We're Avoiding:        What We're Building:
┌──────────────┐             ┌──────────────┐
│ Slack Logic  │             │ Slack         │
├──────────────┤             │ Teams         │
│ Teams Logic  │  →          │ WhatsApp  →  Chat Gateway  →  Single
├──────────────┤  ✗          │ Web            Workflow
│ WhatsApp Log │             │ Custom         Engine
├──────────────┤             │ (Any New)      (5x fewer bugs)
│ Web Logic    │             └──────────────┘
└──────────────┘

 [Code Duplication]          [Maintainable]
 [5x Debug Cost]              [Future-Proof]
 [Slow to Add Channels]       [Add Channels in 2 weeks]
```

**Enterprise Impact:**
- ✅ Reduces code by 60%
- ✅ Single source of truth for workflow logic
- ✅ New channel integration in 2-3 weeks vs 8-10 weeks
- ✅ Easier to onboard enterprise customers with custom chat platforms

### Decision 2: Async-First with Sync Fallback (NOT Sync-Only)

**Problem:** Forcing all workflows to < 2s response time means:
- Disabling complex multi-agent reasoning (5-10s workflows)
- Cutting off external API calls (30s+ latencies)
- Building expensive caching layers

**Solution:** Intelligent routing:
- **Sync Path** (< 2s): Simple queries, lookups, status checks → immediate response in chat
- **Async Path** (10-30s): Complex analysis, multi-agent reasoning, personalization → background job + streaming results

```
Before (Sync-Only):
Customer: "Find blue dresses under £50"
Server: [Thinking...]
Customer: [Waiting 20+ seconds...]
Server: "Request timeout"
Result: ✗ Bad UX, Lost sale

After (Async):
Customer: "Find blue dresses under £50"
Server: [Immediately] "Searching..." (with job_id)
Customer: [Sees chat notification] "Found 24 matches" (5s later)
Server: [Background] "Running recommendation agent..."
Customer: [Sees update] "Top 3 picks for you: ..." (10s later)
Result: ✅ Responsive, Engaging, Higher conversion
```

**Enterprise Impact:**
- ✅ 40% faster perceived response time
- ✅ Complex workflows (usually disabled) now possible
- ✅ Competitive feature parity with industry leaders (OpenAI, Anthropic)
- ✅ Revenue impact: +8-12% conversion lift on discovery workflows

### Decision 3: MCP (Model Context Protocol) for Extensibility

**Problem:** Tightly coupling to specific AI providers/tools creates vendor lock-in.
- Claude → OpenAI migration takes 3 months
- Adding Pinecone vector search requires architecture change
- Internal tool integration requires platform development

**Solution:** **MCP Layer** — Abstract agents, data sources, and tools behind standardized interfaces.

```
Tight Coupling (Current):               MCPs (Proposed):
[Workflow]                              [Workflow]
    ↓                                      ↓
[Claude Agent]  [Algolia] [Redis]      [MCP Router]
    ↓             ↓        ↓              ↓ ↓ ↓
Tightly wired    Problems:            Claude  OpenAI  Custom
                 - Swap providers      Algolia Elastic Pinecone
                 - Takes 3 months      Redis   DynamoDB
                 - High risk           (Any tool, any time)
```

**MCP Benefits:**
| Scenario | Before (No MCP) | After (With MCP) |
|----------|-----------------|------------------|
| Swap Claude → OpenAI | 3 months | 1 week (config change) |
| Add vector search | 2 months | 2 weeks (new MCP) |
| Integrate customer system | Custom API | MCP adapter (3 days) |
| Upgrade to faster LLM model | Risky changes | Swap MCP provider |
| Multi-region deployment | Hardcoded endpoints | MCP config per region |

**Enterprise Impact:**
- ✅ Prevents vendor lock-in with any single AI provider
- ✅ Adds new capabilities (tools, data sources) without code changes
- ✅ De-risks major technology transitions (e.g., LLM provider swap)
- ✅ Enables "bring-your-own-tool" for enterprise customers
- ✅ Strategic flexibility: not married to today's best provider

### Decision 4: Event-Driven Job Queue (NOT In-Memory)

**Problem:** Sync-only execution means everything must fit in memory and complete before HTTP timeout (60s).
- Complex workflows blocked
- Can't integrate slow external services
- Single server failure = lost work

**Solution:** **Celery + Redis job queue** — Fire-and-forget async execution with status tracking.

```
Before (In-Memory):
Request → Process → Response (must complete in 60s)
                    └─ If takes 120s: Request timeout, ✗ Lost

After (Job Queue):
Request → Enqueue Job → Immediate 202 Response
           ↓
           [Background Worker] → 5 minutes? 30 minutes? No problem
           ↓
           [Results stored] → Client polls or gets webhook
Result: ✅ 99.9% completion rate
```

**Enterprise Impact:**
- ✅ No timeout failures on complex workflows
- ✅ Horizontal scaling (add workers, handle 10x load)
- ✅ Failure resilience (worker crashes don't lose data)
- ✅ Cost efficiency (workers can be spot instances in cloud)

---

## III. Technology Stack & Vendor Analysis

### 1. Chat Integration Layer

| Platform | Tech | Timeline | Risk | Cost |
|----------|------|----------|------|------|
| Slack | Slack Bolt SDK | 2 weeks | Low | £0/month (free tier) |
| Teams | Microsoft Bot Framework | 2 weeks | Low | £0/month |
| WhatsApp | Twilio API | 2 weeks | Medium | £0.0075/msg (~£200/1M) |
| Web Chat | WebSocket + React | 1 week | Low | Infra only |
| Enterprise Chat | Custom pattern | 2-3 weeks | Medium | Depends on platform |

**Recommendation:** Start Slack (highest ROI), add Teams/WhatsApp in Phase 2.

### 2. Job Queue & Background Processing

**Option A: Celery + Redis** (Recommended)
- **Pros:** Industry standard, horizontal scaling, excellent failure handling
- **Cons:** Requires Redis operational overhead
- **Cost:** £50-200/month (self-hosted Redis)
- **Risk:** Low (proven at scale by Instagram, Spotify)

**Option B: AWS SQS + Lambda**
- **Pros:** Managed service, pay-per-execution
- **Cons:** Cold starts (2-5s delay), vendor lock-in, harder to monitor
- **Cost:** £0-500/month (pay-per-invocation)
- **Risk:** Medium (cold starts impact user experience)

**Option C: Cloud Tasks (GCP)**
- **Pros:** Native GCP integration, good for enterprise
- **Cons:** Higher cost, less mature ecosystem
- **Cost:** £0-1000/month
- **Risk:** Medium (fewer community resources)

**Recommendation:** **Celery + Redis** for control + cost efficiency. Can migrate to managed queue if needed (6+ month horizon).

### 3. AI/Agent Provider Strategy

**Multi-Provider Approach (via MCPs):**
```
Currently:   Claude only
Goal:        Claude (default) + OpenAI (fallback) + Custom (for specialized tasks)

┌─────────────────────────────────────────────────────────────┐
│                      Workflow                               │
└─────────────────┬───────────────────────────────────────────┘
                  ▼
          ┌───────────────────┐
          │   MCP Router      │  [Decision logic: provider selection]
          └───────────────────┘
          ┌─┬─────────┬──────────┐
          ▼ ▼         ▼          ▼
       Claude OpenAI  Custom   Fallback
      [Primary] [Cost opt] [Domain]
```

**Provider Strategy:**
- **Claude (Anthropic):** Primary for most tasks (best reasoning, cost-effective)
- **OpenAI (GPT-4):** Cost optimization path when token cost matters
- **Custom Models:** Fine-tuned on customer domain data (proprietary edge)

**Cost Comparison (per 1M tokens):**
| Provider | Cost | Use Case |
|----------|------|----------|
| Claude 3.5 | $0.50-2.00 | Default (best all-around) |
| GPT-4o | $1.50-6.00 | Fallback, specialized |
| Custom Fine-tune | $0.20-0.80 | Domain-specific (product rec) |

**Risk Mitigation:** If Claude becomes unavailable, MCP routes to OpenAI (automatic fallback).

### 4. Data Storage Architecture

**Session/Context Data:**
- **Redis** (L1 cache): Fast reads, TTL-based expiry
- **PostgreSQL** (L2 persistent): Conversation history, audit trail

**Rationale:** Hot data in Redis (< 100ms latency), cold data in DB (compliance, recovery).

**Cost Model:**
- Redis: ~£100-200/month (4GB, multi-region)
- PostgreSQL: ~£50-150/month (managed service)

---

## IV. Deployment Architecture

### Multi-Region, High-Availability Setup

```
┌──────────────────────────────────────────────────────────────┐
│                    Global Load Balancer                      │
└──────────────────────────────────────────────────────────────┘
          ┌────────────────────┬────────────────────┐
          ▼                    ▼                    ▼
    ┌────────────┐        ┌────────────┐        ┌────────────┐
    │ US Region  │        │ EU Region  │        │ APAC       │
    │ (Primary)  │        │ (Standby)  │        │ Region     │
    └────────────┘        └────────────┘        └────────────┘
         │                     │                    │
    ┌────────────────────────────────────────────────────────┐
    │  Chat Gateway (K8s, autoscaling)                       │
    │  - Max 3000 req/sec per region                         │
    │  - Auto-scale based on queue depth                     │
    └────────────────────────────────────────────────────────┘
         │                     │                    │
    ┌────────────────────────────────────────────────────────┐
    │  Job Queue (Celery workers, K8s)                       │
    │  - Batch processing workers                            │
    │  - Priority queues for different workflows             │
    │  - Can burst to 2000 concurrent jobs                   │
    └────────────────────────────────────────────────────────┘
         │                     │                    │
    ┌────────────────────────────────────────────────────────┐
    │  Cache Layer (Redis cluster)                           │
    │  - Cross-region replication                            │
    │  - RTO < 5 minutes                                     │
    └────────────────────────────────────────────────────────┘
         │                     │                    │
    ┌────────────────────────────────────────────────────────┐
    │  Data Layer (PostgreSQL with replication)              │
    │  - Primary in US, read replicas in EU/APAC             │
    │  - RTO < 10 minutes                                    │
    └────────────────────────────────────────────────────────┘
```

**SLA Targets:**
- **Availability:** 99.95% uptime (4.38 hours downtime/year)
- **Latency (sync):** p99 < 2s
- **Latency (async):** p99 < 30s to job start
- **Job Completion:** 99.9% (0.1% failed jobs)
- **Data Loss:** 0 (RPO = 0)

**Disaster Recovery:**
- **RTO (Recovery Time Objective):** < 5 minutes (failover to secondary region)
- **RPO (Recovery Point Objective):** < 1 minute (continuous replication)

---

## V. Security & Compliance

### Data Isolation (Multi-Tenant)

**Principle:** John Lewis data must NEVER be visible to Tesco, or vice versa.

**Implementation:**
```sql
-- Every query includes tenant_id
SELECT * FROM workflows
WHERE tenant_id = 'john-lewis'  ← Always enforced
  AND status = 'active'

-- Row-level security
CREATE POLICY tenant_isolation ON workflows
  USING (tenant_id = current_user_tenant_id())
```

**Compliance Frameworks:**
- ✅ GDPR (European data residency support)
- ✅ CCPA (California privacy rights)
- ✅ HIPAA (if healthcare workflows needed)
- ✅ SOC 2 Type II (audit trail, access control)

### Cost Control & Budget Limits

**Per-Workflow Cost Caps:**
```yaml
workflows:
  discovery:
    max_cost_usd: 0.05         # £0.04 per execution
    alert_at_80_percent: true

  customer_support:
    max_cost_usd: 0.10         # £0.08 per execution

  personalized_recs:
    max_cost_usd: 0.15         # £0.12 per execution
```

**Budget Alerts:**
- Daily: Cost exceeds threshold → Alert ops team
- Weekly: Anomaly detection (10x normal spend) → Kill workflow
- Monthly: Cost per customer visible in admin dashboard

---

## VI. Phased Delivery & Investment

### Phase 1: Foundation (4 Weeks) — *John Lewis Demo*
**Deliverables:**
- Slack integration working
- 3 sample workflows (discovery, support, order status)
- Multi-agent execution visible in chat
- Async job queue with polling

**Investment:**
- Engineering: 6-8 FTE weeks
- Infrastructure: ~£5K setup
- Recurring: ~£500/month (dev environment)
- **Total Cost of Ownership:** ~£35K

**Success Metrics:**
- ✅ Demo runs without crashes for 4-hour session
- ✅ 10 concurrent conversations working smoothly
- ✅ Agents responding within 10s (async)
- ✅ John Lewis impressed, wants Phase 2

### Phase 2: Multi-Channel Scale (8 Weeks)
**Deliverables:**
- Teams integration
- WhatsApp integration (via Twilio)
- 99% job completion rate
- Cost tracking per workflow

**Investment:**
- Engineering: 8-10 FTE weeks
- Infrastructure: ~£20K setup (prod-grade)
- Recurring: ~£2K/month (multi-region, managed services)
- **Total Cost of Ownership:** ~£60K

**Success Metrics:**
- ✅ 1,000 concurrent conversations
- ✅ < 2s sync latency (p99)
- ✅ < 10s async latency (p99, excluding MCP)
- ✅ 99.5% uptime in staging
- ✅ Per-workflow cost tracking accurate

### Phase 3: Production Hardening (6 Weeks)
**Deliverables:**
- Multi-region deployment (US, EU, APAC)
- Advanced monitoring & alerting
- Load testing results (10,000 concurrent)
- Security audit passed

**Investment:**
- Engineering: 6-8 FTE weeks
- Infrastructure: ~£30K setup (HA, multi-region)
- Recurring: ~£5K/month (prod infrastructure)
- **Total Cost of Ownership:** ~£80K

**Success Metrics:**
- ✅ 99.95% uptime SLA
- ✅ 10,000 concurrent conversations
- ✅ < 1s p50 latency (sync)
- ✅ Security audit: 0 critical findings
- ✅ Customer-ready for enterprise deployment

### Total Investment (18 Weeks)
| Item | Cost |
|------|------|
| Engineering (22 FTE weeks @ £1.5K/week) | £33K |
| Infrastructure (setup) | £55K |
| Infrastructure (recurring, 6 months) | £27K |
| **Total** | **£115K** |

**ROI Analysis:**
- **Conservative:** 10 customers × £50K/year = £500K revenue → 4.3x ROI
- **Optimistic:** 50 customers × £100K/year = £5M revenue → 43x ROI
- **Payback Period:** 3-6 months (conservative scenario)

---

## VII. Strategic Considerations

### 1. Vendor Independence (MCPs)

**Risk:** "What if we build on Claude and Claude becomes unavailable?"

**Mitigation:** MCPs allow swapping providers in:
- **Configuration Change:** 1 hour (update MCP endpoint)
- **Code Change:** 1-2 weeks (if needed, unlikely)
- **Testing:** 1 week

vs. Traditional (tightly coupled) approach = 3+ months.

**Strategic Option:** Negotiate with OpenAI as secondary provider, auto-fallback in MCPs.

### 2. Competitive Differentiation

**What makes ACOS unique:**
- ✅ **Multi-agent orchestration** (not single agent)
- ✅ **Async + sync hybrid** (fast + complex)
- ✅ **Vendor flexibility** (MCPs)
- ✅ **Enterprise ready** (multi-tenant, audit, compliance)

**vs. ChatGPT API:**
- ❌ Single agent, no workflow
- ❌ No cost control
- ❌ Limited to OpenAI

**vs. Anthropic Workflows:**
- ❌ Not multi-channel
- ❌ No async job queue
- ❌ Early stage

**ACOS Advantage:** "The orchestration layer Anthropic and OpenAI don't provide."

### 3. M&A Potential

**This platform is attractive to:**
- Enterprise software companies (Salesforce, SAP) looking to add AI
- Retail tech companies (Shopify, BigCommerce) wanting multi-agent capabilities
- Cloud providers (AWS, Azure, GCP) rounding out AI offerings

**Valuation Boost:** AI-powered orchestration platforms trade at 8-12x ARR (vs. 5-7x traditional SaaS).

---

## VIII. Risks & Mitigation

| Risk | Impact | Mitigation | Owner |
|------|--------|-----------|-------|
| **MCP provider unavailable** | Workflows blocked | Circuit breaker + fallback MCPs | CTO |
| **Chat platform rate limits** | Message loss | Backpressure queuing, negotiated limits | Eng Lead |
| **Cost explosion** | Budget impact | Per-workflow caps, anomaly detection | CIO |
| **Multi-region complexity** | Delayed shipping | Clear ownership, runbooks, exercises | Ops |
| **Data leakage (multi-tenant)** | Compliance breach | Row-level security, regular audits | Security |
| **Vendor lock-in (if MCPs fail)** | Technical debt | MCP standard adoption, community tooling | CTO |

---

## IX. Success Metrics & KPIs

### Technical KPIs
- **Latency:** p99 sync < 2s, p99 async job start < 10s
- **Uptime:** 99.95% across all regions
- **Job Completion:** 99.9% (< 0.1% failures)
- **Cost per Execution:** < £0.05 (all MCPs inclusive)

### Business KPIs
- **Concurrent Sessions:** 1,000 (Phase 2) → 10,000 (Phase 3)
- **Message Volume:** 100K/day (Phase 2) → 1M+/day (Phase 3)
- **Customer Acquisition:** 5 customers Phase 1 → 20 Phase 2 → 100 Phase 3
- **Revenue:** £250K run-rate by end of Phase 3

### Customer Satisfaction
- **NPS Score:** > 50 (platform ease of use)
- **Workflow Success Rate:** > 98% (do what customers expect)
- **Support Tickets:** < 5% of customers (platform is self-service)

---

## X. Recommendations & Next Steps

### For CTO
1. **Architecture Review:** Validate MCP pattern aligns with longer-term platform vision
2. **Tech Stack:** Approve Celery + Redis for job queue (best cost/benefit)
3. **Approval:** Sign off on phased approach, allocate 8-10 FTE for Phase 1

### For CIO
1. **Budget:** Approve £115K total investment (ROI payback in 4-6 months)
2. **Security:** Require MCP layer isolate customer data (not visible to workflow logic)
3. **Compliance:** Ensure multi-tenant architecture supports GDPR/CCPA (required for EU/US customers)

### For Enterprise Architects
1. **Design:** Review spec for alignment with enterprise cloud architecture
2. **Scalability:** Confirm multi-region approach meets availability targets
3. **Integrations:** Ensure MCP pattern extensible for customer-specific tools/APIs

---

## Appendix: Quick Reference

### Technology Stack Summary
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| API | FastAPI | Type-safe, performant, proven in ACOS |
| Job Queue | Celery + Redis | Horizontal scaling, failure resilience |
| Chat Gateway | Slack Bolt, Teams SDK | Official SDKs, maintained |
| Data | PostgreSQL + Redis | Industry standard, proven at scale |
| Deployment | Kubernetes | Multi-region, auto-scaling, HA |
| Observability | Prometheus + Grafana | Cost tracking, SLA monitoring |

### Key Dates
- **April 6:** Spec approval (this document)
- **April 20:** Phase 1 kickoff
- **May 18:** John Lewis demo ready
- **July 1:** Phase 2 release
- **August 15:** Phase 3 release

### Budget Summary
- **Phase 1 (Demo):** £35K
- **Phase 2 (Scale):** £60K
- **Phase 3 (Hardening):** £80K
- **Total (18 weeks):** £115K
- **Projected Revenue (Year 1):** £500K-5M (depending on customer acquisition)

---

## Document Information

**Author:** Engineering Leadership
**Approval Authority:** CTO, CIO
**Distribution:** Exec team, board (if relevant)
**Last Updated:** April 6, 2026
**Review Cycle:** Quarterly (technical changes), annually (strategic)
**Next Review Date:** July 6, 2026

---

**Status:** 🟡 **Awaiting Approval** — Ready for CTO/CIO/Enterprise Architect review

**Questions?** Contact Engineering Leadership for deep-dive sessions per topic.
