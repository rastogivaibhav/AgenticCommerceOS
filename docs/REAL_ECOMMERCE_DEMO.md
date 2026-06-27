# Real Ecommerce Demo: ACOS + Spree

This demo starts ACOS beside a real Spree Commerce backend. It is designed to prove the adapter pattern:

- Spree is the reference ecommerce system.
- ACOS is the agentic control plane.
- Agents call governed ACOS tools.
- The tools call real Spree Store API endpoints.
- ACOS records evidence and keeps safe local fallbacks.
- ACOS verifies signed Spree webhook events.

Use this wording for a general audience:

> This is not a chatbot controlling a website. It is an agentic commerce control plane connected to a real ecommerce backend through approved APIs. Spree is the reference implementation; the same adapter pattern can be built for Shopify, Salesforce Commerce Cloud, Adobe Commerce, commercetools, custom OMS/PIM stacks, or enterprise vendors that expose approved APIs.

Avoid saying ACOS can directly control public websites such as johnlewis.com or waitrose.com. The accurate claim is that ACOS can integrate with comparable enterprise commerce backends when the brand provides API or partner access.

## Start The Demo

From the repository root:

```bash
cp .env.ecom-demo.example .env.ecom-demo
docker compose --env-file .env.ecom-demo -f docker-compose.yml -f docker-compose.ecom-demo.yml up --build -d
```

Or:

```bash
make ecom-demo-up
```

First startup can take a while because Docker may need to pull the Spree image and build the ACOS image.

## Verify The Demo

```bash
python scripts/ecom_demo_verify.py --env-file .env.ecom-demo
```

Or:

```bash
make ecom-demo-verify
```

The verifier checks:

- ACOS Ops API health.
- Spree health.
- Spree Store API products.
- ACOS agent journey uses `source: "spree"`.
- Ops connector registry shows Spree.
- ACOS accepts a correctly signed Spree webhook payload.

## Run The Browser Demo

The Playwright demo opens the real ACOS Ops UI, runs the proof journey, checks Spree connector health, and saves screenshots/videos.

```bash
npm --prefix harness/playwright install
npm --prefix harness/playwright run test:ecom-demo
```

Or:

```bash
make ecom-demo-playwright
```

On Windows, the all-in-one runner is:

```powershell
.\scripts\run_ecom_demo.ps1
```

To watch the browser:

```powershell
.\scripts\run_ecom_demo.ps1 -Headed
```

Screenshots are written to:

```text
harness/playwright/output/playwright/ecom-demo
```

Playwright videos and traces are written under:

```text
harness/playwright/test-results
```

## Open The Demo

- ACOS Ops UI: <http://localhost:8081/ui/estate>
- Spree backend/API: <http://localhost:3000>
- Spree Store API products: <http://localhost:3000/api/v3/store/products>

For local demo auth in ACOS:

```text
http://localhost:8081/dev/auth/bootstrap/admin?redirect=/ui/estate
```

## What To Show

1. Open Spree products endpoint or backend to show real ecommerce data exists.
2. Open ACOS Estate Dashboard.
3. Run the ACOS proof journey.
4. Run the verifier and point at `source: "spree"`.
5. Explain that the agent did not scrape or click a site. It called governed tools, and those tools called Spree APIs.
6. Show the signed webhook verifier result.

## Why Trust This With An LLM?

Do not ask the audience to trust the LLM. Ask them to trust the system boundary.

In this architecture, the LLM is not allowed to freely mutate commerce state. It can propose or request an action, but the platform controls execution:

- Tools are explicit: `catalog.search`, `inventory.check_stock`, `cart.add_item`, `orders.get_order`, and so on.
- Tool calls are typed and routed through ACOS.
- Tenant config decides which backend is active.
- HTTPS is enforced unless a local demo explicitly allows HTTP.
- Secrets are masked and not stored in prompts.
- Errors fall back safely instead of silently corrupting a journey.
- Every tool call records evidence.
- The Ops UI can inspect the journey, tools, sources, and results.

So the trust story is:

> We are not trusting the model to run the store. We are using the model as a planner and language interface around governed, deterministic commerce tools.

## Why This Is Still Agentic Without An LLM

Without an LLM, ACOS is still useful. It becomes an agentic headless omnichannel retail system:

- Headless: commerce actions happen through APIs, not through a browser UI.
- Omnichannel: the same journey can start from web, WhatsApp, Telegram, Slack, store partner, or contact centre.
- Agentic: specialist agents, routing rules, tool permissions, workflows, evidence, and fallbacks coordinate the work.
- Deterministic: the local/fallback runtime can route intents, call tools, and produce repeatable outputs.
- Governed: every action is observable and reviewable.

In other words:

> The LLM improves natural language and flexible reasoning, but the operating system is the tool-routing, workflow, evidence, policy, and connector layer.

## What Is Still Demo-Grade

- The LLM path can run in local/deterministic fallback mode. No LLM key is required to prove the architecture.
- Payment completion depends on the Spree demo configuration and sandbox payment setup.
- The included demo API key and webhook secret are local-only values.
- The ACOS auth settings in `.env.ecom-demo.example` are for local demonstration only.
- The prebuilt Spree production image blocks webhooks to Docker-internal/private URLs as SSRF protection. For a live emitted Spree webhook demo, expose ACOS through an approved public callback URL or tunnel and set `ACOS_SPREE_WEBHOOK_URL` to that URL.

## Stop The Demo

```bash
docker compose --env-file .env.ecom-demo -f docker-compose.yml -f docker-compose.ecom-demo.yml down
```

Or:

```bash
make ecom-demo-down
```

To reset all demo data, remove volumes too:

```bash
docker compose --env-file .env.ecom-demo -f docker-compose.yml -f docker-compose.ecom-demo.yml down -v
```
