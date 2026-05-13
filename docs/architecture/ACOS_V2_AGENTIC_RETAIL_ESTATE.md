# ACOS v2 — Omnichannel Agentic Retail Estate

This build adds the ACOS v2 foundation for a John Lewis-style agentic retail estate.

## Core model

Customer or Partner intent is received by an orchestrating layer. The orchestrator resolves capabilities, invokes specialist agents through an A2A-style contract, calls shared tools, merges specialist responses, applies channel mode/tone, and records traceable evidence.

## Implemented modules

- Agent Registry with seed specialist agents.
- Capability Registry with capability-to-agent coverage.
- A2A invocation and trace model.
- Channel modes for customer direct, store Partner, contact centre and internal ops.
- Tone profiles.
- Evaluation summary and agent split recommendations.
- Guardrails, FinOps and memory-access proof endpoints.
- Route-to-production summary.
- Alembic migration baseline for ACOS v2 tables.
- React screens for estate dashboard, registry, capabilities, A2A trace, channel modes, evaluation and governance.

## Demo journey

> “I’m buying a cot mattress for a newborn under £250, and I need to know if my previous nursery order can be returned.”

Expected flow:

1. Orchestrator receives Partner/customer intent.
2. Capability Registry resolves nursery, mattress, shopping/order and returns capabilities.
3. A2A layer invokes Nursery Advisor, Mattress Recommender, Shopping/WISMO/Returns specialists.
4. Shared tools prove catalog, inventory, order and return checks.
5. Response merge creates one coherent John Lewis answer.
6. Trace captures agents, tasks, tools, cost and final response.

## UI routes

- `/ui/estate`
- `/ui/agent-registry`
- `/ui/agent-detail/:id`
- `/ui/capabilities`
- `/ui/a2a-trace`
- `/ui/channel-modes`
- `/ui/evaluations`
- `/ui/governance`
