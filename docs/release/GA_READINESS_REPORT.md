# ACOS GA Readiness Report

Generated: 2026-05-11T10:36:16.025210+00:00

## Automated checks

### northstar pytest — PASS

```
........                                                                 [100%]
=============================== warnings summary ===============================
../../../opt/pyvenv/lib/python3.13/site-packages/ddtrace/internal/module.py:313
  /opt/pyvenv/lib/python3.13/site-packages/ddtrace/internal/module.py:313: DeprecationWarning: The 'lia' package has been renamed to 'cross_web'. Please update your imports from 'from lia import ...' to 'from cross_web import ...'. The 'lia' package will be removed in a future version.
    self.loader.exec_module(module)

apps/ops_api/main.py:170
  /mnt/data/acos_next/apps/ops_api/main.py:170: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

../../../opt/pyvenv/lib/python3.13/site-packages/fastapi/applications.py:4495
  /opt/pyvenv/lib/python3.13/site-packages/fastapi/applications.py:4495: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
8 passed, 3 warnings in 2.32s

```

### northstar smoke — PASS

```
ACOS north-star smoke status: success
Intent: stock_availability
Agent: Inventory Agent
Tool calls: 4
Evidence events: 8
Response: For a winter wedding under £200, I recommend: Navy Satin Midi Dress (£89, 4 in Reading); Silver Wrap Shawl (£35, 8 in Reading); Black Block-Heel Court Shoes (£59, 3 in Reading).

```

### week11/12 uat and production gate tests — PASS

```
...........................                                              [100%]
=============================== warnings summary ===============================
../../../opt/pyvenv/lib/python3.13/site-packages/ddtrace/internal/module.py:313
  /opt/pyvenv/lib/python3.13/site-packages/ddtrace/internal/module.py:313: DeprecationWarning: The 'lia' package has been renamed to 'cross_web'. Please update your imports from 'from lia import ...' to 'from cross_web import ...'. The 'lia' package will be removed in a future version.
    self.loader.exec_module(module)

apps/ops_api/main.py:170
  /mnt/data/acos_next/apps/ops_api/main.py:170: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    @app.on_event("startup")

../../../opt/pyvenv/lib/python3.13/site-packages/fastapi/applications.py:4495
  /opt/pyvenv/lib/python3.13/site-packages/fastapi/applications.py:4495: DeprecationWarning: 
          on_event is deprecated, use lifespan event handlers instead.
  
          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
          
    return self.router.on_event(event_type)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
27 passed, 3 warnings in 0.50s

```

### Docker runtime proof

```
BLOCKED: docker executable not found in this sandbox
```

## GA status

This package is now a hardened north-star pilot foundation. It is not a fully certified enterprise GA release until Docker Compose, cloud deployment, production RBAC, Postgres migrations, and full-harness completion are proven in CI.

## Implemented north-star capabilities

- Omnichannel message envelope and session/journey spine.
- Durable SQLite-backed pilot state for sessions, identities, journeys, messages, and evidence.
- Intent router and multi-agent retail routing skeleton.
- Native retail tool layer with catalog, inventory, order, returns, loyalty, and case tools.
- Evidence events for messages, intent, agent selection, tool calls, and responses.
- Optional API-key guardrails for north-star and hosted MCP endpoints.
- MCP client/router foundation and ACOS MCP JSON-RPC server.
- GraphQL endpoint for Studio/Ops composition.
- Golden winter-wedding retail journey smoke path.

## Remaining GA blockers

1. Docker Compose runtime proof in a Docker-enabled environment.
2. Postgres migrations/repositories for north-star tables.
3. Production-default RBAC and tenant isolation for GraphQL, MCP, and north-star APIs.
4. Full legacy harness completion without timeout.
5. Frontend bundle splitting and production performance budget.
6. MCP validation against target client implementations.
7. Cloud deployment smoke test.
## Gap Closure Sprint Update

The gap-closure sprint improved golden journey proof, added GraphQL Studio mutations, introduced a SQLite outbox event backbone, added optional Postgres north-star repository code, extended retail tools, and added workflow `intentNode` / `humanHandoffNode` support.

Latest verified evidence in this sandbox:

- North-star tests: 12 passed
- Week 11/12 UAT and production gate tests: 27 passed
- Golden journey smoke: success, 4 participating agents, 7 tool calls, 15 evidence events
- Frontend build: successful after `npm ci`

Remaining GA blockers are still Docker/cloud proof, production RBAC/tenant isolation, full Postgres runtime switch, complete Agent Studio v2 UI, replay proof, governance/FinOps/DLP hardening, and external MCP client validation.
