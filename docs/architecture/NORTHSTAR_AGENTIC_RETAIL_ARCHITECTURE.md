# ACOS North-Star Agentic Retail Architecture

ACOS is now oriented around a core north-star: omnichannel session spine, multi-agent orchestration, retail tools, MCP interoperability, GraphQL-powered Studio/Ops views, and evidence-first governance.

## Core flow

```text
Channel message
→ MessageEnvelope
→ ConversationSession + Journey
→ Intent classifier
→ Agent router
→ Retail tools / MCP tools
→ Evidence timeline
→ Customer response / human handoff
```

## Protocol split

- REST: webhooks, execution, health, operational APIs.
- GraphQL: Agent Studio and Ops Console composition.
- MCP: agent-to-tool and external-agent interoperability.

## Golden journey

Customer: “I need an outfit for a winter wedding under £200, available for pickup near Reading.”

The system resolves a session and journey, classifies intent, selects a retail agent, calls catalog and inventory tools, records evidence, and returns an explainable recommendation.
