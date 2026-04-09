# Changelog

All notable changes to ACOS Control Plane are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Documentation

- Rewrote `README.md` with a production-control-plane-first narrative, runnable quick start, and concrete operational examples.
- Refreshed `DOCUMENTATION_INDEX.md` and `docs/README.md` to reflect the current docs map, runbooks, and readiness artifacts.
- Updated `CONTRIBUTING.md` with current repo workflows, test gates, and docs update expectations.
- Updated `SECURITY.md` with current disclosure guidance and operational security controls.
- Added and linked Week 12 operational runbooks and evidence pack:
  - `docs/RUNBOOK_GO_LIVE.md`
  - `docs/RUNBOOK_WORKFLOW_PROMOTION.md`
  - `docs/RUNBOOK_INCIDENT_RESPONSE.md`
  - `docs/week12_production_gate_evidence_pack.md`

## [1.0.0] - 2026-03-22

### Initial Release

**ACOS Control Plane v1.0.0** is the first General Availability (GA) release of the enterprise workflow orchestration platform.

#### Added

**Core Features**
- Workflow Builder: Visual designer for composing AI agent pipelines
- Experimentation Framework: A/B testing with statistical analysis
- Analytics Dashboard: Real-time metrics and performance tracking
- REST API: 15+ endpoints for programmatic access

**Frontend**
- React 19 with Vite build tool
- Tailwind CSS responsive design system
- Dark and light theme support with automatic detection
- Zustand state management
- Full keyboard navigation support
- WCAG AA accessibility compliance
- Support for mobile (375px+), tablet (768px+), and desktop (1280px+)

**Backend**
- FastAPI application framework
- PostgreSQL relational database
- SQLAlchemy ORM with connection pooling
- Pydantic validation and serialization
- API key authentication with rate limiting (100 req/min)
- Gunicorn/Uvicorn production server

**Security**
- TLS 1.2+ encryption in transit
- SQL injection prevention via parameterized queries
- XSS protection via React escaping
- CSRF protection with HTTP-only cookies
- Input validation on all endpoints
- Audit logging for API operations

**Testing**
- 34 E2E tests (Playwright) - 100% passing
- 119 unit tests (Vitest + pytest) - 100% passing
- 100% test coverage for critical paths
- Pre-commit hooks for code quality

**Documentation**
- README with feature overview and architecture
- Installation guide for dev and production
- User onboarding guide (30-minute quickstart)
- Complete user guide with feature documentation
- API reference with examples
- Testing guide with procedures
- Deployment guide with production checklist

**Operations**
- Docker and Docker Compose support
- Systemd service configuration
- Nginx reverse proxy examples
- Let's Encrypt SSL integration
- PostgreSQL backup automation
- Health check endpoints
- Structured logging
- Performance metrics collection

#### Performance

- Frontend page load: <2 seconds (p95)
- API response time: 50-100ms (p95)
- Database query time: 30-50ms (p95)
- Frontend bundle size: 465 KB (gzipped)
- API memory footprint: ~150 MB base
- Concurrent request handling: 500+ RPS per instance

#### Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

#### Known Limitations

- Single-instance deployment (horizontal scaling in v1.1)
- No multi-tenant support (planned for v1.3)
- No workflow templates (planned for v1.2)
- Basic monitoring (advanced in v1.1)
- No mobile app (planned for v2.0)

---

## Unreleased

### [1.1.0] - Planned Q2 2026

#### Planned Features

- Multi-instance deployment with load balancing
- Advanced workflow analytics and metrics
- Custom metric definitions
- Workflow templates library
- Team collaboration features
- RBAC (Role-Based Access Control)
- Enhanced audit logging
- Webhook integration support
- GraphQL API option (alongside REST)
- Performance profiling tools

#### Planned Improvements

- Optimized database indexes for large datasets
- Caching layer for frequently accessed data
- UI performance improvements
- Extended browser compatibility
- Mobile-responsive design enhancements

#### Planned Security Enhancements

- Multi-factor authentication (MFA)
- Secrets rotation automation
- Advanced threat detection
- Security compliance certifications (SOC 2)

---

### [1.2.0] - Planned Q4 2026

#### Planned Features

- AI-assisted workflow creation
- Workflow optimization recommendations
- Integration marketplace
- Advanced scheduling and cron triggers
- Custom webhook actions
- Workflow versioning and rollback
- Performance prediction models
- Cost optimization suggestions

---

### [2.0.0] - Planned 2027

#### Planned Features

- Multi-tenant architecture
- Mobile application (iOS/Android)
- Offline-first capabilities
- Advanced scheduling engine
- Workflow templates and marketplace
- Enhanced analytics and reporting
- Custom Python/JavaScript step support
- Stream processing capabilities
- Real-time collaboration

---

## Release Notes

### Installation

For upgrade instructions from previous versions, see [UPGRADE.md](./UPGRADE.md)

For production deployment, see [DEPLOYMENT.md](./DEPLOYMENT.md)

### Support

- **Documentation:** See [docs/](./docs/) directory
- **Issues:** [GitHub Issues](https://github.com/yourorg/acos/issues)
- **Security:** [security@acos.dev](mailto:security@acos.dev)
- **Support:** [support@acos.dev](mailto:support@acos.dev)

---

## Version Numbering

ACOS uses semantic versioning:

- **MAJOR version:** Breaking changes (e.g., 1.0 → 2.0)
- **MINOR version:** New features backward compatible (e.g., 1.0 → 1.1)
- **PATCH version:** Bug fixes (e.g., 1.0.0 → 1.0.1)

Pre-release versions use: `1.0.0-alpha.1`, `1.0.0-beta.1`, `1.0.0-rc.1`

---

**Last Updated:** March 22, 2026
