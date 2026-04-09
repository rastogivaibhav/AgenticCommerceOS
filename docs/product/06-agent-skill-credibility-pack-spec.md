# 06 Agent + Skill Credibility Pack Spec

## Document Control
- Version: v1.0
- Date: 2026-04-09
- Status: Proposed
- Owner: Product + Platform Engineering
- Related docs:
  - `docs/product/04-go-live-prd.md`
  - `docs/week12_production_gate_evidence_pack.md`
  - `docs/RUNBOOK_GO_LIVE.md`

## 1. Summary
This spec defines a **go-live-safe implementation** to make the Agents and Skills tabs operationally credible without delaying launch by a full platform rewrite.

The implementation focus is:
1. Make Agents and Skills executable in a controlled way.
2. Add real ecommerce sandbox validation (not just mocks).
3. Preserve existing go-live trajectory by explicitly de-scoping marketplace-grade features.

## 2. Problem Statement
Current behavior creates trust risk for internal stakeholders and pilot customers:
1. Agents and Skills can be created in UI, but execution and runtime binding are incomplete.
2. Some UI options imply provider support that is not yet wired in backend runtime.
3. Mock and fixture-heavy routes can be mistaken for production-grade runtime behavior.

Result: perception risk of "demo-ware" even though core journey runtime is real.

## 3. Goals
1. Deliver a minimally complete **build -> bind -> test -> promote** path for agentic commerce workflows.
2. Prove end-to-end execution against at least one real ecommerce platform sandbox.
3. Produce evidence artifacts that leadership can use for go-live confidence.
4. Keep implementation within the current go-live window (+2 to +3 weeks max).

## 4. Non-Goals (Explicit De-Scope)
1. No full plugin marketplace.
2. No multi-provider LLM runtime expansion before go-live.
3. No generalized low-code workflow platform rebuild.
4. No broad connector matrix beyond the chosen sandbox path.

## 5. Scope (Credibility Pack)

### 5.1 Agents Tab: Operational Minimum
1. Keep create/edit/list behavior.
2. Add explicit fields required for execution:
   - `runtime_provider` (`google_genai`, `local_fallback`)
   - `model_name` (default `gemini-2.0-flash`)
   - `agent_version`
   - `bound_skills[]`
3. Add "Test Run" action from Agents UI.
4. Add "Supported now" and "Roadmap" labels in UI for provider options.

### 5.2 Skills Tab: Executable Minimum
1. Keep skill create/edit/list.
2. Add required contract metadata:
   - `input_schema`
   - `output_schema`
   - `timeout_seconds`
   - `retries`
   - `execution_mode` (`local`, `http_connector`)
3. Add "Test Skill" action with fixture input and contract validation.
4. Allow skill binding to agents from UI.

### 5.3 Real Ecommerce Sandbox Validation
1. Implement one default credibility path:
   - Shopify test store (catalog + order lookup)
   - Optional Stripe test mode (refund path simulation)
2. Add reusable sandbox scenario runner:
   - order status
   - return eligibility
   - refund triage
   - loyalty fallback response
3. Persist run evidence artifacts in `deploy/k8s/observability/evidence/`.

### 5.4 Production Clarity and Risk Reduction
1. Gate fixture/mock API routes behind explicit dev/test flag.
2. Add startup warning if mock routes are enabled in non-dev environments.
3. Ensure docs/UI clearly distinguish:
   - Production runtime APIs
   - Mock/testing APIs

## 6. Current Supported Runtime (Truth in Product)
This section must be reflected in UI and sales materials.

### Supported Today (Implemented)
1. Internal ADK runtime (`ADKRuntime`).
2. Google GenAI via `GOOGLE_API_KEY` or `GEMINI_API_KEY`.
3. Active default model: `gemini-2.0-flash`.
4. Local deterministic fallback when no GenAI key is set.

### Not Yet Supported in Production Runtime
1. CrewAI
2. Salesforce Agentforce
3. ServiceNow Agent
4. OpenAI Agent

UI may show these as roadmap providers only, not selectable production providers.

## 7. Functional Requirements

### FR-1 Agent Runtime Binding
1. Agent records must include provider and model metadata.
2. Agent test execution must fail fast on invalid provider config.
3. Agent test response must include:
   - provider used
   - model used
   - bound skills executed
   - duration and status

### FR-2 Skill Contract Enforcement
1. Skill test execution must validate input schema before run.
2. Skill output must validate against output schema.
3. Contract violations must return structured error payloads.

### FR-3 Workflow Integration
1. Workflow versions can reference `agent_bindings`.
2. Journey runtime resolves active workflow + agent bindings at execution time.
3. Run payload stores agent and skill version metadata for traceability.

### FR-4 Sandbox Evidence
1. Scenario runner executes all 4 standard ecommerce scenarios.
2. Each run writes machine-readable evidence with pass/fail and metrics.
3. Evidence pack is exportable for go-live review.

### FR-5 Environment Safety
1. Mock route groups disabled by default in stage/prod.
2. Enabling mock routes requires explicit `ALLOW_MOCK_ROUTES=1`.
3. Startup validation fails in non-dev if mock routes are enabled without override.

## 8. API and Data Model Changes

### 8.1 API Additions
1. `POST /api/v1/agents/{agent_id}/test`
2. `POST /api/v1/skills/{skill_id}/test`
3. `POST /api/v1/agents/{agent_id}/bind-skill`
4. `POST /api/v1/sandbox/execute-scenarios`

### 8.2 API Update (Backward-Compatible)
1. Extend `POST /api/v1/agents` payload with:
   - `runtime_provider`
   - `model_name`
   - `agent_version`
   - `bound_skills`
2. Extend `POST /api/v1/skills` payload with:
   - `input_schema`
   - `output_schema`
   - `execution_mode`
   - `timeout_seconds`
   - `retries`

### 8.3 Data Persistence
Add nullable fields to existing records first for non-breaking rollout.

Agents:
1. `runtime_provider` TEXT
2. `model_name` TEXT
3. `agent_version` TEXT
4. `bound_skills` JSONB

Skills:
1. `input_schema` JSONB
2. `output_schema` JSONB
3. `execution_mode` TEXT
4. `timeout_seconds` INT
5. `retries` INT

Runs:
1. `agent_metadata` JSONB
2. `skill_metadata` JSONB

## 9. UX Requirements
1. Agents UI shows provider options as:
   - Supported: selectable
   - Roadmap: non-selectable with tooltip
2. Skills UI adds contract editor and test panel.
3. Test results show compact scorecard:
   - status
   - latency
   - contract pass/fail
   - connector source (`remote` or `local_fallback`)

## 10. Observability and Acceptance Evidence
For every agent/skill/sandbox test run, capture:
1. request id
2. trace id
3. tenant id
4. workflow id/version
5. provider + model
6. contract validation result
7. scenario name
8. duration and final status

Evidence artifacts must be generated in JSON and included in go-live evidence pack.

## 11. Rollout Plan

### Phase A (Week 1)
1. Add backend schema extensions and API contracts.
2. Add agent/skill test endpoints.
3. Add mock-route environment gating.

### Phase B (Week 2)
1. Wire Agents UI for provider/model/version fields.
2. Wire Skills UI for contract fields and test runner.
3. Add provider capability labels in UI.

### Phase C (Week 3)
1. Build Shopify sandbox scenario runner.
2. Run standard scenario suite and publish evidence pack.
3. Go/no-go review with leadership.

## 12. Milestones, Owners, and ETA
1. Backend Contracts + Migrations
   - Owner: Backend Lead
   - ETA: 2026-04-16
2. UI Enhancements (Agents/Skills/Test Panels)
   - Owner: Frontend Lead
   - ETA: 2026-04-22
3. Sandbox Runner + Evidence Pack
   - Owner: Solutions Engineer
   - ETA: 2026-04-29
4. Go-Live Readiness Sign-Off
   - Owner: Product + Platform
   - ETA: 2026-04-30

## 13. Success Metrics (Must Hit)
1. Time to first agent test run < 15 minutes in configured environment.
2. Time to first sandbox scenario pass < 60 minutes from setup.
3. 100% run evidence captured with trace + provider + contract result.
4. Zero ambiguity in UI between supported and roadmap providers.

## 14. Risks and Mitigations
1. Risk: Scope creep into full platform rewrite.
   - Mitigation: Enforce non-goals and freeze roadmap-only items.
2. Risk: Connector instability in sandbox.
   - Mitigation: Keep local fallback and explicit degraded-mode reporting.
3. Risk: Team confusion from duplicate/legacy routes.
   - Mitigation: Environment gating + release checklist validation.

## 15. Go/No-Go Criteria
Go if:
1. Agent and Skill test endpoints are stable.
2. At least 3 of 4 sandbox scenarios pass end-to-end.
3. Evidence pack generated and reviewed.
4. Mock route gating verified in non-dev environment.

No-Go if:
1. Supported provider labeling is still ambiguous.
2. Runtime behavior depends on mock-only routes in target environment.
3. Evidence pack cannot prove reproducible scenario outcomes.

