# ACOS Control Plane v1.0.0

Enterprise-grade platform for autonomous agent orchestration, experimentation, and customer engagement.

**Status**: Generally Available (GA) | **Release Date**: March 2026 | **License**: Apache 2.0

## Overview

The ACOS Control Plane is a production-ready system for building, testing, and deploying autonomous agent workflows. It combines powerful workflow orchestration with built-in A/B experimentation capabilities, real-time analytics, and customer-facing agent interfaces.

Designed for enterprise deployments with 99.5%+ uptime SLA, comprehensive audit logging, and multi-tenant support roadmap.

## Core Capabilities

| Capability | Description |
|---|---|
| **Visual Workflow Builder** | Drag-and-drop interface for designing complex agent workflows without code |
| **A/B Experimentation Framework** | Statistical testing framework for evaluating workflow variants with built-in hypothesis tracking |
| **Real-time Analytics Dashboard** | Live metrics, conversion tracking, and performance analysis with export capabilities |
| **Shopping Agent System** | Conversational AI for customer product discovery, cart management, and order tracking |
| **Multi-channel Chat Interface** | WebSocket-based real-time chat for web, mobile, and embedded deployments |
| **Payment Integration** | Stripe integration for secure order processing with PCI compliance |
| **Enterprise Authentication** | API key and JWT-based authentication with role-based access control |
| **Rate Limiting & Protection** | Built-in rate limiting (100 req/min), CORS protection, and DDoS mitigation |
| **Responsive Design** | Full support for mobile (375px+), tablet, and desktop viewports |
| **Data Export** | CSV, JSON, and PDF export formats for reporting and analysis |

## Getting Started

### Prerequisites

| Component | Version | Purpose |
|---|---|---|
| Python | 3.9+ | Backend runtime |
| Node.js | 18+ | Frontend build tool |
| PostgreSQL | 14+ | Primary data store |
| Docker (optional) | Latest | Containerization |

### Installation

**Option 1: Docker (Production Recommended)**

```bash
cd acos
docker compose up --build

# Services will be available at:
# - Control Plane UI: http://localhost:8000/ui
# - API: http://localhost:8000
# - Database: localhost:5432
```

**Option 2: Local Development Setup**

Backend:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://user:password@localhost:5432/acos"
export OPS_ENVIRONMENT="development"

python -m uvicorn ops_api.main:app --reload
# API available at http://localhost:8000
```

Frontend:
```bash
cd src
npm install
npm run dev
# UI available at http://localhost:5173
```

## Documentation

| Document | Purpose |
|---|---|
| **[Installation Guide](docs/INSTALLATION.md)** | System requirements, setup procedures, verification steps |
| **[User Guide](docs/USER_GUIDE.md)** | Workflow builder, experimentation framework, analytics dashboard |
| **[API Reference](docs/API.md)** | REST/WebSocket endpoints, request/response examples, error codes |
| **[Deployment Guide](docs/DEPLOYMENT.md)** | Production setup, scaling strategies, monitoring, backup procedures |
| **[Testing Guide](docs/TESTING.md)** | Unit test setup, integration test patterns, E2E test execution |
| **[Onboarding Guide](docs/ONBOARDING.md)** | 30-minute quickstart, first workflow, running experiments |
| **[Shopping Agent Guide](docs/SHOPPING_AGENT.md)** | Conversational shopping implementation, product integration, payment setup |
| **[Security Guide](docs/SECURITY.md)** | Vulnerability reporting, security best practices, compliance |
| **[Contributing Guidelines](docs/CONTRIBUTING.md)** | Development standards, commit conventions, PR process |

## Shopping Agent System

The ACOS Control Plane includes a production-ready shopping agent system for conversational commerce:

### Key Features

- **Conversational Shopping**: Claude-powered agent for product discovery and recommendations
- **Real-time Chat**: WebSocket-based interface for web and mobile applications
- **Product Integration**: MCP (Model Context Protocol) integration with product catalogs
- **Cart Management**: Persistent shopping cart with session state management
- **Payment Processing**: Stripe integration for secure order completion
- **Order Tracking**: Customer-facing order status and delivery tracking

### Quick Shopping Agent Example

```bash
# Start shopping chat session
curl -X POST http://localhost:8000/api/shopping/sessions \
  -H "Content-Type: application/json" \
  -d '{"type": "guest"}'

# Connect WebSocket for conversation
# ws://localhost:8000/ws/shopping-chat/{session_id}

# Send message
{
  "type": "message",
  "content": "I'm looking for a firm mattress under £500"
}
```

See [Shopping Agent Guide](docs/SHOPPING_AGENT.md) for complete integration documentation.

## Development Workflow

### Running Tests

```bash
# All tests with coverage report
pytest tests/ -v --cov=ops_api --cov-report=html

# Specific test module
pytest tests/unit/test_shopping_sessions.py -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (Playwright)
npx playwright test tests/e2e/
```

### Code Quality

```bash
# Format code
black ops_api/ src/
isort ops_api/

# Lint checks
flake8 ops_api/
eslint src/

# Type checking
mypy ops_api/
```

### Building for Production

```bash
# Frontend build
cd src && npm run build

# Verify all checks pass
pytest tests/ -v --cov=ops_api
npm run lint

# Ready for deployment
```

## System Architecture

The ACOS Control Plane is built on a modular, scalable architecture:

### Backend Layer (FastAPI)

| Component | Purpose | Technologies |
|---|---|---|
| **REST API** | Workflow management, analytics, experimentation | FastAPI, Pydantic |
| **WebSocket Server** | Real-time chat and agent communication | Starlette WebSockets |
| **Authentication** | API key and JWT token validation | Python-jose |
| **Rate Limiting** | Request throttling and DDoS protection | SlowAPI |
| **Tool Executor** | Agent tool invocation with retry logic | JSON-RPC |

### Frontend Layer (React + Vite)

| Component | Purpose | Technologies |
|---|---|---|
| **Workflow Builder** | Visual workflow design | React Flow |
| **Analytics Dashboard** | Real-time metrics and charts | Recharts, Zustand |
| **Shopping Chat Widget** | Conversational shopping interface | React, WebSocket |
| **Responsive UI** | Mobile/tablet/desktop support | Tailwind CSS, shadcn/ui |

### Data Layer (PostgreSQL + pgvector)

| Table | Purpose |
|---|---|
| `workflows` | Workflow definitions and configurations |
| `workflow_runs` | Execution history and results |
| `experiments` | A/B test configurations and variants |
| `analytics_events` | Aggregated metrics and KPIs |
| `shopping_sessions` | Conversation history and cart state |
| `shopping_orders` | Order records with payment status |
| `shopping_training_data` | Product knowledge for agent enrichment |

### Integration Points

- **MCP Servers**: Product catalog and inventory via Model Context Protocol
- **Stripe API**: Payment processing and webhook handling
- **Claude API**: LLM-powered agent intelligence
- **PostgreSQL pgvector**: Semantic search and embeddings

## Configuration

### Required Environment Variables

```env
# Database Connection
DATABASE_URL=postgresql://user:password@host:5432/acos

# Application Settings
OPS_ENVIRONMENT=production
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# Security & Authentication
ALLOWED_ORIGINS=https://example.com,https://api.example.com
JWT_SECRET=generate-with-openssl-rand-hex-32
OPS_JWT_SECRET=generate-with-openssl-rand-hex-32

# Shopping Agent (Optional)
SHOPPING_AGENT_MODEL=claude-opus-4-6
MCP_PRODUCT_SERVER_URL=https://products.example.com/mcp
STRIPE_API_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/project
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete configuration reference and security best practices.

## API Usage

### Workflow Operations

Create workflow:
```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Flow",
    "description": "Autonomous customer support agent",
    "family": "support"
  }'
```

List workflows:
```bash
curl -X GET http://localhost:8000/api/workflows \
  -H "Authorization: Bearer $API_KEY"
```

### Analytics Queries

Get workflow metrics:
```bash
curl -X GET "http://localhost:8000/api/analytics/metrics?workflow_id=xxx" \
  -H "Authorization: Bearer $API_KEY"
```

Export data:
```bash
curl -X GET "http://localhost:8000/api/analytics/export?format=csv" \
  -H "Authorization: Bearer $API_KEY" \
  > metrics.csv
```

### Shopping Agent Chat

See [Shopping Agent Guide](docs/SHOPPING_AGENT.md) for WebSocket chat integration examples.

## Performance & Reliability

### Response Time Targets
| Endpoint | P50 | P95 | P99 |
|---|---|---|---|
| Workflow CRUD | 50ms | 150ms | 300ms |
| Analytics Query | 100ms | 400ms | 800ms |
| WebSocket Chat | 200ms | 500ms | 1000ms |
| API Gateway | 10ms | 100ms | 200ms |

### Throughput & Capacity
- **Workflow Execution**: 10,000+ workflows/hour
- **Concurrent Connections**: 1000+ WebSocket sessions
- **Database Capacity**: Supports 100M+ workflow runs
- **Storage**: Scales to TB+ with PostgreSQL partitioning
- **Concurrent Users**: 5000+ simultaneous API consumers

### Availability
- **Target Uptime**: 99.5% (monthly SLA)
- **Recovery Time Objective (RTO)**: 15 minutes
- **Recovery Point Objective (RPO)**: 1 minute
- **Backup Frequency**: Hourly automated snapshots

## Security & Compliance

### Authentication & Authorization
- API key authentication with Bearer tokens
- JWT token support with configurable expiration
- Role-based access control (RBAC) with three tiers: viewer, editor, admin
- Session token validation on all protected endpoints

### Data Protection
- TLS 1.2+ encryption for all network traffic
- AES-256 encryption at rest for sensitive data (credentials, addresses)
- PCI DSS compliance for payment processing via Stripe tokenization
- GDPR support: Right to be forgotten, data export capabilities

### Security Measures
- Rate limiting: 100 requests/minute per API key
- CORS protection with configurable origins
- SQL injection prevention via parameterized queries
- XSS protection via React DOM escaping
- CSRF protection via HTTP-only cookie flags
- Audit logging of all administrative operations
- Security headers: CSP, X-Frame-Options, X-Content-Type-Options

### Vulnerability Reporting
Report security issues to `security@example.com` with:
- Severity level (Critical/High/Medium/Low)
- Affected component and version
- Steps to reproduce
- Potential impact

We will respond within 24 hours for critical issues.

## Support & Community

| Channel | Purpose |
|---|---|
| **Documentation** | Comprehensive guides in `/docs/` directory |
| **GitHub Issues** | Bug reports and feature requests |
| **GitHub Discussions** | Questions and community support |
| **Email Support** | Production issues: support@example.com |
| **Security Issues** | Critical vulnerabilities: security@example.com |

Response time targets:
- Critical bugs: 2 hours
- High priority: 4 hours
- Standard issues: 24 hours

## Product Roadmap

### v1.1.0 (Q2 2026)
- OAuth2 and SAML authentication
- Webhook triggers for external integrations
- Advanced workflow scheduling
- Workflow versioning and rollback
- Shopping agent: Multi-language support

### v1.2.0 (Q3 2026)
- Multi-tenant deployment support
- Advanced role-based access control (RBAC)
- Workflow execution audit trail UI
- Shopping agent: Inventory real-time sync
- Analytics: Custom metric framework

### v2.0.0 (Q4 2026)
- Native mobile applications (iOS/Android)
- Real-time collaborative workflow editing
- Advanced workflow analytics and insights
- Shopping agent: Multi-currency support
- Marketplace: Third-party integration framework

## License

ACOS Control Plane is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for full terms.

This license permits:
- Commercial use and modification
- Distribution and private use
- Patent protection through grant of patent rights
- SaaS and hosted deployments

Requires:
- Retention of copyright and license notices
- Notification of modifications
- Clear statement of changes

## Version History

### v1.0.0 (March 2026) - General Availability
**Core Platform**
- Visual workflow builder with real-time execution
- A/B experimentation framework with statistical analysis
- Real-time analytics dashboard with export (CSV, JSON, PDF)
- Rate limiting (100 req/min) and comprehensive audit logging
- Dark/light mode with theme persistence

**Shopping Agent System** (New)
- Conversational shopping interface with Claude LLM
- WebSocket-based real-time chat for web and mobile
- Shopping cart management and order tracking
- Stripe payment integration with webhook handling
- MCP product server integration with fallback caching
- Session persistence for guest and registered users

**Infrastructure**
- FastAPI backend with async support
- PostgreSQL with pgvector semantic search
- Docker containerization and orchestration
- Production deployment guides and monitoring setup
- Comprehensive test coverage (80%+ for core)

**Documentation**
- Installation, deployment, and onboarding guides
- Complete API reference with examples
- User guides for workflow builder and experimentation
- Shopping agent integration documentation
- Security and compliance guidelines

---

**Quick Links**
- [Deployment Instructions](docs/DEPLOYMENT.md)
- [API Reference](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)
- [Shopping Agent Setup](docs/SHOPPING_AGENT.md)
- [Security Guidelines](docs/SECURITY.md)
