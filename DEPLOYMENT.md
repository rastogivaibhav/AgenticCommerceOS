# ACOS Control Plane - Deployment Guide

## Overview

This guide covers deploying ACOS Control Plane v1.0.0 to production, staging, and development environments.

## Prerequisites

Before deploying, ensure you have:

- **Python** 3.9 or higher
- **Node.js** 18+ with npm
- **PostgreSQL** 12+ database
- **Docker** and **Docker Compose** (recommended)
- Appropriate system permissions and network access

## Quick Start with Docker

The easiest way to deploy is using Docker Compose.

### 1. Prepare Environment File

Create `.env` in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://acos_user:secure_password@postgres:5432/acos_db
POSTGRES_USER=acos_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=acos_db

# API Configuration
APP_VERSION=1.0.0
OPS_ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Security
JWT_SECRET=your-very-secure-secret-key-change-this
API_KEY_PREFIX=sk-

# Optional: Analytics and Monitoring
SENTRY_DSN=https://your-sentry-key@sentry.io/project
LOG_LEVEL=INFO
```

### 2. Build and Deploy with Docker Compose

```bash
# Build images
docker-compose build

# Start services (runs in background)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Remove all data (careful!)
docker-compose down -v
```

Services started:
- **PostgreSQL**: Database on port 5432
- **ACOS Backend API**: On port 8000
- **ACOS Frontend UI**: Served on port 8000 at `/ui`

Access the application: `http://localhost:8000/ui`

## Manual Deployment

For non-Docker deployments or custom setups.

### 1. Backend Setup

#### Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Database Setup
```bash
# Create database and schema
export DATABASE_URL="postgresql://user:pass@host:5432/acos_db"
python -c "from acosplatform.db.connection import ensure_schema; ensure_schema()"
```

#### Run Backend Server
```bash
export APP_VERSION="1.0.0"
export OPS_ENVIRONMENT="production"
export ALLOWED_ORIGINS="https://your-domain.com"
export JWT_SECRET="your-secret-key"

uvicorn apps.ops_api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools
```

**For Production**, use a process manager like systemd, supervisor, or Gunicorn:

```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 \
  --worker-class uvicorn.workers.UvicornWorker \
  apps.ops_api.main:app
```

### 2. Frontend Setup

#### Build Frontend
```bash
cd apps/ops_ui_v2
npm install
npm run build

# Output in: apps/ops_ui_v2/dist/
```

#### Serve Frontend
The backend automatically serves the frontend at `/ui` if the built files exist. To serve separately:

```bash
# Using a simple HTTP server
npx http-server dist -p 3000 --cors

# Or your preferred web server (nginx, Apache, etc.)
```

#### Deploy to CDN (Recommended for Production)
```bash
# Sync build output to S3, CloudFlare, or similar
aws s3 sync apps/ops_ui_v2/dist s3://your-bucket/acos/

# Or use your CDN provider's sync tool
```

## Environment Configuration

### Essential Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost/acos` |
| `APP_VERSION` | Application version | `1.0.0` |
| `OPS_ENVIRONMENT` | Environment type | `production`, `staging`, `dev` |
| `ALLOWED_ORIGINS` | CORS-allowed origins | `https://example.com,https://app.example.com` |
| `JWT_SECRET` | JWT signing key (dev mode only) | `your-secret-key` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Log verbosity | `INFO` |
| `API_KEY_PREFIX` | Prefix for generated API keys | `sk-` |
| `SENTRY_DSN` | Error tracking endpoint | None |
| `REDIS_URL` | Redis connection (for caching) | None |
| `MAX_WORKERS` | Max concurrent worker threads | `4` |

### Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` template instead
2. **Rotate secrets regularly** - Update JWT_SECRET and API keys quarterly
3. **Use strong passwords** - Database password minimum 20 characters
4. **Enable HTTPS** - Always use HTTPS in production (not HTTP)
5. **Restrict CORS origins** - Don't use `*` in ALLOWED_ORIGINS
6. **Implement authentication** - Use OAuth, API keys, or JWT
7. **Monitor logs** - Set up centralized logging and alerting

## Database Migration

### Initial Setup
```bash
# Automatically creates schema on startup
# Or manually:
python -c "from acosplatform.db.connection import ensure_schema; ensure_schema()"
```

### Backup Database
```bash
pg_dump -U acos_user -h localhost acos_db > backup.sql
```

### Restore Database
```bash
psql -U acos_user -h localhost acos_db < backup.sql
```

## Testing Before Deployment

### Run Backend Tests
```bash
pytest tests/ -v --cov=acosplatform --cov-report=html
```

### Run Frontend Tests
```bash
cd apps/ops_ui_v2
npm test -- run
```

### Run E2E Tests
```bash
cd apps/ops_ui_v2
npm run test:e2e
```

### Check Build
```bash
cd apps/ops_ui_v2
npm run build
# Verify dist/ folder has index.html and JavaScript files
```

### Lint Check
```bash
cd apps/ops_ui_v2
npm run lint
```

## Health Checks

After deployment, verify:

```bash
# Check backend health
curl http://localhost:8000/health

# Check database connection
curl -H "Authorization: Bearer dev-token" http://localhost:8000/runs

# Check frontend is served
curl http://localhost:8000/ui/ | grep -q "ACOS"

# Check API endpoints
curl -H "Authorization: Bearer dev-token" http://localhost:8000/analytics/metrics
```

## Scaling Considerations

### Horizontal Scaling
- Run multiple backend instances behind a load balancer
- Use external PostgreSQL managed service (RDS, Cloud SQL)
- Use Redis for distributed caching
- Deploy frontend to CDN for global distribution

### Performance Tuning
```python
# In deployment, increase database connection pool
DATABASE_MAX_POOL_SIZE = 20
# Increase worker threads
MAX_WORKERS = 8
# Enable caching
CACHE_TTL = 300
```

### Monitoring
- Set up metrics collection (Prometheus, DataDog)
- Configure alerting for error rates, latency
- Monitor database query performance
- Track API response times

## Troubleshooting

### Database Connection Fails
```bash
# Test PostgreSQL connection
psql $DATABASE_URL

# Check environment variable
echo $DATABASE_URL

# Verify PostgreSQL is running and accessible
```

### Frontend Not Loading
```bash
# Check files exist
ls -la apps/ops_ui_v2/dist/

# Check backend logs
docker-compose logs app

# Verify CORS headers
curl -i http://localhost:8000/ui/
```

### API Returns 403 Forbidden
- Check Authorization header is present
- Verify JWT_SECRET matches (if using JWT)
- Check API key format and prefix
- Ensure token isn't expired

### High Memory Usage
- Reduce worker count
- Enable log rotation
- Monitor database connection leaks
- Check for memory leaks in long-running processes

## Rollback Procedure

If issues occur in production:

```bash
# Stop current deployment
docker-compose down

# Restore from previous tag
git checkout v0.9.0

# Rebuild and restart
docker-compose up -d

# Or rollback database
psql -U acos_user acos_db < backup.sql
```

## Monitoring and Logging

### Docker Logs
```bash
# View logs
docker-compose logs -f app

# View specific service
docker-compose logs -f postgres
```

### Application Logs
Logs are written to stdout and can be captured by your container orchestration platform.

Set `LOG_LEVEL`:
- `DEBUG` - Verbose, includes all function calls
- `INFO` - Standard, operational events
- `WARNING` - Potential issues
- `ERROR` - Failures requiring attention

### Metrics Endpoint
```bash
# Get Prometheus-format metrics
curl http://localhost:8000/metrics
```

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx
```nginx
server {
    listen 443 ssl http2;
    server_name api.acos.example.com;

    ssl_certificate /etc/letsencrypt/live/api.acos.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.acos.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Disaster Recovery

### Backup Strategy
```bash
# Daily database backups
0 2 * * * pg_dump -U acos_user acos_db > /backups/acos-$(date +\%Y\%m\%d).sql

# Store in multiple locations
aws s3 sync /backups s3://backup-bucket/acos/
```

### Recovery Time Objective (RTO)
- Backend: < 5 minutes (restart container)
- Database: < 30 minutes (restore from backup)
- Frontend: < 1 minute (CDN cache)

## Support and Updates

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review documentation: `/docs/`
3. Check API documentation: `http://localhost:8000/docs` (if enabled)
4. Contact support team

For updates:
```bash
# Pull latest version
git pull origin main

# Rebuild and deploy
docker-compose build
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Status**: Production Ready
