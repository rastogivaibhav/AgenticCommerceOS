# ACOS North-Star Demo Runbook

## Purpose

This runbook explains how to demo ACOS as a multi-agent omnichannel retail control plane.

The demo should prove that ACOS is not a chatbot. It should prove that one customer request becomes a session, journey, intent, multi-agent orchestration run, retail tool calls, human handoff, evidence, replay and readiness proof.

## Pre-demo setup

```bash
make setup
make test-northstar
make smoke-northstar
make runtime-check
make ui-build
```

For a Docker-enabled environment:

```bash
make compose-prod-up
make db-migrate
```

If RBAC is enabled:

```bash
export ACOS_NORTHSTAR_REQUIRE_AUTH=1
export ACOS_NORTHSTAR_API_KEYS='demo-key:default:admin|ops|analyst|viewer'
```

In the browser console or application storage, set:

```js
localStorage.setItem('northstar_api_key', 'demo-key')
```

## Demo navigation

1. Open `/ui/demo-guide`.
2. Explain the product narrative and success criteria.
3. Open `/ui/studio-proof`.
4. Run the golden journey dry test.
5. Show agents, tools, evidence, handoff and replay proof.
6. Open `/ui/test-center`.
7. Explain how the same proof can be tested via CLI, CI, API and Docker.

## Demo message

```text
I need an outfit for a winter wedding under £200, available for pickup near Reading
```

## What to prove

- The message creates a conversation session and journey.
- The retail intent is classified.
- Discovery, Stylist, Inventory and Service agents participate.
- Catalog, pricing, promotion, inventory and case tools are called.
- Evidence is recorded for message, intent, agent, tools, handoff and response.
- A human handoff can be created.
- Replay snapshots are captured.
- Readiness checks are transparent.

## Talk track

> ACOS is the control plane for agentic retail operations. It takes a customer request, resolves the omnichannel session, routes it through retail-specific agents, calls governed tools, records evidence, and gives operations teams a Studio view to test, approve, replay and govern the journey.

## Known external checks

Docker Compose and cloud deployment proof must be completed on a Docker-enabled runner or target cloud environment.
