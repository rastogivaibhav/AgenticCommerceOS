# ACOS Documentation Library

This folder is the working product and architecture library for ACOS.

It is designed to anchor future prompt-by-prompt development so that each iteration:
- ships a runnable, containerized slice
- improves the current codebase without breaking the operating model
- moves the product toward an enterprise-grade AI commerce control plane

## Document Map

- `architecture/01-vision-and-principles.md`
  Core vision, business framing, and architectural principles.
- `architecture/02-reference-architecture.md`
  Target system architecture, bounded contexts, runtime topology, and non-functional requirements.
- `architecture/03-workflow-operating-model.md`
  Execution model for agents, skills, workflows, runs, policies, and control-plane behavior.
- `architecture/04-canonical-resource-model.md`
  Canonical domain objects, minimum fields, relationships, and invariants for enterprise implementation.
- `architecture/05-retail-capability-map.md`
  Retail-specific capability map showing how ACOS fits across the commerce operating model.
- `architecture/06-environment-and-release-governance.md`
  Environment model, promotion controls, release gates, and operational governance.
- `product/01-prd-control-plane-foundation.md`
  Product requirements for the next meaningful control-plane foundation.
- `product/02-iterative-delivery-contract.md`
  Rules for modular, shippable, enterprise-grade development in future prompts.
- `product/03-operator-journeys-and-raci.md`
  Operator task flows, role responsibilities, and ownership model for the control plane.
- `product/04-go-live-prd.md`
  Enterprise go-live PRD and readiness criteria for ACOS as a managed AI commerce platform.
- `product/05-document-set-review.md`
  Multi-disciplinary review of the full document set, including readiness view and residual gaps.
- `design/01-design-library.md`
  UX architecture, design principles, component guidance, and control-plane design language.

## How To Use These Docs

- Treat the current repository as the starting baseline, not the finished target state.
- Use the PRD and delivery contract before implementing any new slice.
- Keep every new feature aligned to the reference architecture and workflow model.
- Prefer a thin vertical slice over partial implementation of multiple areas.
- Every slice should run via Docker and include enough verification to be trusted.

## Current Baseline

Today the repository contains:
- a shopper-facing FastAPI service
- an ops-facing FastAPI service
- a Postgres schema and repository layer
- mock commerce capabilities for catalog, pricing, promotions, loyalty, checkout, orders, and returns
- an inline ops dashboard plus a not-yet-integrated Vite React app

This means ACOS is currently a prototype of an AI-driven commerce orchestration platform.
The target is a true operating system and control plane for AI-driven commerce.
