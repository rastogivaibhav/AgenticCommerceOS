# ACOS Product Truth

## What is real in this package

- FastAPI ops/shopper/chat services from the existing codebase.
- React Ops UI source from the existing codebase.
- New north-star session/journey spine.
- New intent router and retail agent registry skeleton.
- New retail mock tool layer.
- New MCP JSON-RPC server and local MCP tool router.
- New GraphQL endpoint mounted on Ops API.
- New golden retail journey smoke path.

## What is still not GA-certified

- Docker Compose runtime was not fully certified in this environment.
- Frontend build depends on Node/npm installation and must be verified in CI.
- External Shopify/Salesforce/WhatsApp credentials are not certified here.
- Security, tenancy hardening, RBAC for GraphQL/MCP, and persistent evidence tables need production-grade implementation.

## Correct current positioning

ACOS is a north-star foundation for a multi-agent omnichannel retail operating system. It is ready for iterative pilot hardening, not yet a fully certified enterprise GA release.
