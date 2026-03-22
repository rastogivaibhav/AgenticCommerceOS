# Contributing to ACOS Control Plane

First, thank you for your interest in contributing to ACOS Control Plane. This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to conduct@acos.dev.

## Getting Started

### Prerequisites

- Node.js 18.0 or later
- Python 3.9 or later
- PostgreSQL 12 or later
- Git 2.30 or later

### Development Setup

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/acos.git
   cd acos
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/description
   # Use naming conventions:
   # - feature/: New feature
   # - bugfix/: Bug fix
   # - docs/: Documentation
   # - refactor/: Code refactoring
   # - test/: Test additions
   ```

3. **Set Up Development Environment**
   ```bash
   # Backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Frontend
   cd apps/ops_ui_v2
   npm ci
   ```

4. **Initialize Database**
   ```bash
   psql -U postgres -c "CREATE DATABASE acos_dev;"
   psql -U postgres -d acos_dev < db/schema.sql
   ```

## Development Standards

### Code Style

**Python (Backend)**
- Format: Black (line length: 88)
- Import sorting: isort
- Linting: pylint
- Type hints: Full coverage

```bash
black apps/
isort apps/
pylint apps/
mypy apps/
```

**JavaScript/TypeScript (Frontend)**
- Format: Prettier
- Linting: ESLint
- Type checking: TypeScript

```bash
prettier --write src/
eslint src/ --fix
tsc --noEmit
```

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `perf`: Performance improvements
- `ci`: CI/CD configuration
- `chore`: Build, dependencies, etc.

**Examples:**
```
feat(workflow): add step reordering capability

fix(api): correct rate limiting calculation

docs(readme): update installation instructions
```

### Pull Request Process

1. **Before Creating PR:**
   - Ensure all tests pass: `npm run test:e2e && pytest tests/`
   - Update documentation if needed
   - Add tests for new functionality
   - Follow code style guidelines

2. **Create Pull Request:**
   - Use descriptive title matching conventional commits
   - Reference related issues: `Closes #123`
   - Describe changes and rationale
   - Include any breaking changes in description

3. **PR Template:**
   ```markdown
   ## Description
   Brief description of changes

   ## Related Issues
   Closes #123

   ## Changes Made
   - Change 1
   - Change 2

   ## Testing
   - [ ] Unit tests added/updated
   - [ ] E2E tests added/updated
   - [ ] All tests passing

   ## Breaking Changes
   None / Describe breaking changes if any

   ## Screenshots (if applicable)
   Include screenshots for UI changes
   ```

4. **Review Process:**
   - Code review required before merge
   - Automated tests must pass
   - Documentation must be updated
   - No merge conflicts with main branch

## Testing Requirements

### Unit Tests

**Backend (pytest):**
```bash
pytest tests/ -v --cov=apps/
```

**Frontend (Vitest):**
```bash
cd apps/ops_ui_v2
npm run test
```

### E2E Tests

```bash
cd apps/ops_ui_v2
npm run test:e2e
```

### Coverage Requirements

- **Minimum line coverage:** 80%
- **New code coverage:** 100%
- **Critical paths:** 100%

### Test Organization

```
tests/
├── test_workflows.py        # Workflow API tests
├── test_experiments.py      # Experiment tests
├── test_analytics.py        # Analytics tests
└── conftest.py              # Fixtures and setup

apps/ops_ui_v2/
└── tests-e2e/
    └── features.spec.js     # Playwright E2E tests
```

## Documentation

### Code Documentation

**Python:**
```python
def create_workflow(name: str, steps: List[WorkflowStep]) -> Workflow:
    """
    Create a new workflow.

    Args:
        name: Workflow name (required)
        steps: List of workflow steps (minimum 1)

    Returns:
        Workflow: Created workflow object

    Raises:
        ValueError: If name is empty or steps are invalid
        DatabaseError: If database operation fails

    Example:
        >>> workflow = create_workflow("My Workflow", steps=[...])
    """
```

**TypeScript/JavaScript:**
```typescript
/**
 * Create a workflow step
 * @param {string} type - Step type (input, agent_call, etc.)
 * @param {StepConfig} config - Step configuration
 * @returns {WorkflowStep} The created step
 * @throws {ValidationError} If configuration is invalid
 */
export function createStep(type: string, config: StepConfig): WorkflowStep {
  // implementation
}
```

### Documentation Files

Update relevant documentation when making changes:
- `README.md` - Project overview changes
- `INSTALLATION.md` - Setup/configuration changes
- `API.md` - API endpoint changes
- `USER_GUIDE.md` - Feature changes
- `CONTRIBUTING.md` - Process changes

## Reporting Issues

### Bug Reports

Include:
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, browser, version)
- Screenshots or error logs
- Proposed solution (optional)

### Feature Requests

Include:
- Clear description of desired feature
- Use case and motivation
- Proposed implementation (optional)
- Alternative approaches considered
- Impact on existing features

## Release Process

### Version Numbering

ACOS uses semantic versioning: MAJOR.MINOR.PATCH

- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Update documentation
- [ ] Tag release in Git
- [ ] Build and test release artifacts
- [ ] Create GitHub release notes
- [ ] Update installation guide

## Getting Help

- **Documentation:** See [docs/](./docs/) directory
- **Issues:** Search [GitHub Issues](https://github.com/yourorg/acos/issues)
- **Discussions:** Use [GitHub Discussions](https://github.com/yourorg/acos/discussions)
- **Email:** dev@acos.dev

## License

By contributing to ACOS Control Plane, you agree that your contributions will be licensed under the Apache License 2.0.

---

**Thank you for contributing to ACOS Control Plane!**
