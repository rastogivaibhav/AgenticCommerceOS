# Installation Guide - ACOS Control Plane v1.0.0

Complete step-by-step installation instructions for development and production environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Setup](#production-setup)
4. [Docker Setup](#docker-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

#### Development Machine
- **OS:** macOS 11+, Windows 10+, Linux (Ubuntu 20.04+)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 10GB free space

#### Server (Production)
- **OS:** Ubuntu 20.04 LTS or later
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 50GB SSD
- **CPU:** 2 cores minimum, 4 cores recommended

### Software Requirements

#### Frontend Development
```bash
# Check versions
node --version        # Should be 18.0.0 or higher
npm --version         # Should be 8.0.0 or higher
```

**Installation:**
- **macOS:** `brew install node@18`
- **Windows:** Download from [nodejs.org](https://nodejs.org)
- **Linux:** `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs`

#### Backend Development
```bash
# Check versions
python --version      # Should be 3.9 or higher
pip --version         # Should be 21.0 or higher
```

**Installation:**
- **macOS:** `brew install python@3.9`
- **Windows:** Download from [python.org](https://www.python.org)
- **Linux:** `sudo apt-get install python3.9 python3.9-venv python3-pip`

#### Database
```bash
# Check if installed
psql --version        # Should be 12.0 or higher
```

**Installation:**
- **macOS:** `brew install postgresql@14`
- **Windows:** Download PostgreSQL installer from [postgresql.org](https://www.postgresql.org/download)
- **Linux:** `sudo apt-get install postgresql-14 postgresql-contrib-14`

#### Version Control
```bash
git --version         # Should be 2.30 or higher
```

**Installation:** Download from [git-scm.com](https://git-scm.com)

---

## Development Setup

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourorg/acos.git
cd acos

# Verify structure
ls -la                # Should see apps/, db/, docs/, tests/
```

### Step 2: Backend Setup

```bash
# Navigate to project root
cd acos

# Create Python virtual environment
python3.9 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# Upgrade pip and setuptools
pip install --upgrade pip setuptools

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python --version
pip list | grep fastapi
```

### Step 3: Database Setup

```bash
# Start PostgreSQL service
# macOS: brew services start postgresql@14
# Linux: sudo systemctl start postgresql

# Create database and user
createdb acos_dev
createuser -s acos_dev --password    # Enter password when prompted

# Run migrations
psql -U acos_dev -d acos_dev < db/schema.sql

# Verify tables created
psql -U acos_dev -d acos_dev -c "\dt"
```

Expected output shows tables: runs, workflows, experiments, agents, skills

### Step 4: Backend Configuration

```bash
# Create .env file in project root
cat > .env << EOF
DATABASE_URL=postgresql://acos_dev:password@localhost:5432/acos_dev
APP_VERSION=1.0.0
OPS_ENVIRONMENT=dev
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
SECRET_KEY=$(openssl rand -hex 32)
EOF

# Load environment variables
source .env
```

### Step 5: Start Backend Server

```bash
# From project root with venv activated
uvicorn apps.ops_api.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

**API Endpoints Available:**
- Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

### Step 6: Frontend Setup (New Terminal)

```bash
# From project root (in a new terminal)
cd apps/ops_ui_v2

# Install Node dependencies
npm install

# Check installation
npm list react           # Should show React 19.x
npm list vite            # Should show Vite 8.x
```

### Step 7: Start Frontend Dev Server

```bash
# From apps/ops_ui_v2
npm run dev

# You should see:
# VITE v8.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
```

### Step 8: Verify Installation

Open your browser and navigate to:
- **Frontend:** `http://localhost:5173`
- **API Docs:** `http://localhost:8000/docs`

You should see:
- ✅ ACOS Control Plane header
- ✅ Navigation menu with three items: Workflow Builder, Experiments, Analytics
- ✅ Dark/light mode toggle in header
- ✅ Responsive layout

---

## Production Setup

### System Preparation

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y \
  curl \
  git \
  wget \
  python3.9 \
  python3.9-venv \
  python3-pip \
  postgresql-14 \
  postgresql-contrib-14 \
  nodejs \
  npm

# Create application user
sudo useradd -m -s /bin/bash acos
sudo su - acos
```

### PostgreSQL Production Setup

```bash
# As acos user
sudo -u postgres psql << EOF
CREATE USER acos_prod WITH PASSWORD 'YOUR_SECURE_PASSWORD';
CREATE DATABASE acos_prod OWNER acos_prod;
GRANT ALL PRIVILEGES ON DATABASE acos_prod TO acos_prod;
EOF

# Run migrations
psql -U acos_prod -d acos_prod -h localhost < db/schema.sql

# Create indices for performance
psql -U acos_prod -d acos_prod -h localhost << EOF
CREATE INDEX idx_runs_created_at ON runs(created_at DESC);
CREATE INDEX idx_experiments_status ON experiments(status);
VACUUM ANALYZE;
EOF
```

### Backend Deployment

```bash
# Clone repository
git clone https://github.com/yourorg/acos.git /app/acos
cd /app/acos

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create production .env
cat > .env.production << EOF
DATABASE_URL=postgresql://acos_prod:YOUR_SECURE_PASSWORD@localhost:5432/acos_prod
APP_VERSION=1.0.0
OPS_ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

### Frontend Deployment

```bash
# Build frontend
cd apps/ops_ui_v2
npm install
npm run build

# Output in dist/ directory
ls -la dist/

# Deploy to web server
# Option 1: Copy to nginx
sudo cp -r dist/* /var/www/acos/

# Option 2: Upload to CDN
aws s3 sync dist/ s3://your-bucket-name/
```

### Nginx Configuration

```bash
# Create nginx config
sudo tee /etc/nginx/sites-available/acos << EOF
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/acos;

    # Frontend assets
    location / {
        try_files \$uri \$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/acos /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Systemd Service

```bash
# Create backend service
sudo tee /etc/systemd/system/acos-api.service << EOF
[Unit]
Description=ACOS Control Plane API
After=network.target

[Service]
Type=notify
User=acos
WorkingDirectory=/app/acos
Environment="PATH=/app/acos/venv/bin"
EnvironmentFile=/app/acos/.env.production
ExecStart=/app/acos/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    apps.ops_api.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable acos-api.service
sudo systemctl start acos-api.service
```

---

## Docker Setup

### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### Docker Compose Setup

```bash
# From project root
docker-compose up -d

# Monitor startup
docker-compose logs -f

# Wait for all services to be healthy (2-3 minutes)
```

The docker-compose.yml includes:
- **PostgreSQL 14** on port 5432
- **FastAPI backend** on port 8000
- **React frontend** on port 5173 (dev)

### Verify Docker Installation

```bash
# Check running containers
docker-compose ps

# Should show all services RUNNING

# Check logs
docker-compose logs acos-api
docker-compose logs acos-ui

# Access services
# Frontend: http://localhost:5173
# API: http://localhost:8000
# Database: localhost:5432
```

### Docker Commands

```bash
# Stop services
docker-compose down

# Restart specific service
docker-compose restart acos-api

# View logs with filtering
docker-compose logs -f --tail=100 acos-api

# Execute command in container
docker-compose exec acos-api python manage.py migrate

# Build custom image
docker-compose build --no-cache
```

---

## Verification

### Development Verification

```bash
# 1. Test frontend loads
curl -s http://localhost:5173 | grep -q "ACOS Control Plane" && echo "✅ Frontend OK" || echo "❌ Frontend Failed"

# 2. Test API responds
curl -s http://localhost:8000/health | grep -q "ok" && echo "✅ API OK" || echo "❌ API Failed"

# 3. Test database connection
psql -U acos_dev -d acos_dev -c "SELECT COUNT(*) FROM workflows;" && echo "✅ Database OK" || echo "❌ Database Failed"

# 4. Run tests
cd apps/ops_ui_v2 && npm run test:e2e
pytest tests/ -v

# Expected: All tests passing (34/34 E2E, 119 unit tests)
```

### Production Verification

```bash
# 1. Check services running
systemctl status acos-api
systemctl status nginx

# 2. Test API endpoint
curl -H "Authorization: Bearer YOUR_API_KEY" https://yourdomain.com/api/workflows

# 3. Check database
psql -U acos_prod -d acos_prod -h localhost -c "SELECT NOW();"

# 4. Check SSL certificate
ssl-cert-check -c /etc/letsencrypt/live/yourdomain.com/cert.pem

# 5. Monitor logs
journalctl -u acos-api -f
tail -f /var/log/nginx/access.log
```

---

## Troubleshooting

### Frontend Issues

**Issue:** npm install fails
```bash
# Solution: Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Issue:** Port 5173 already in use
```bash
# Solution: Use different port
npm run dev -- --port 3000
```

**Issue:** Module not found errors
```bash
# Solution: Reinstall dependencies
rm -rf node_modules
npm install
npm run dev
```

### Backend Issues

**Issue:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Reinstall Python dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

**Issue:** `Database does not exist`
```bash
# Solution: Create database
createdb acos_dev
psql -U acos_dev -d acos_dev < db/schema.sql
```

**Issue:** Port 8000 already in use
```bash
# Solution: Kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn apps.ops_api.main:app --port 8001
```

### Database Issues

**Issue:** `psql: error: could not connect to server`
```bash
# Solution: Start PostgreSQL service
# macOS: brew services start postgresql@14
# Linux: sudo systemctl start postgresql

# Or check if it's running
ps aux | grep postgres
```

**Issue:** Authentication failed
```bash
# Solution: Reset password
sudo -u postgres psql
\password acos_dev
\q
```

### Docker Issues

**Issue:** `docker: command not found`
```bash
# Solution: Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**Issue:** `Cannot connect to Docker daemon`
```bash
# Solution: Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Or add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Issue:** Port already in use
```bash
# Solution: Map to different port
# Edit docker-compose.yml
ports:
  - "5174:5173"  # Use 5174 instead of 5173
```

---

## Environment Variables Reference

### Development (.env)
```bash
DATABASE_URL=postgresql://acos_dev:password@localhost:5432/acos_dev
APP_VERSION=1.0.0
OPS_ENVIRONMENT=dev
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
SECRET_KEY=dev-secret-key-not-secure
DEBUG=True
```

### Production (.env.production)
```bash
DATABASE_URL=postgresql://acos_prod:secure_password@db.internal:5432/acos_prod
APP_VERSION=1.0.0
OPS_ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECRET_KEY=long-random-secure-key-from-openssl
DEBUG=False
LOG_LEVEL=info
```

### Docker (.env.docker)
```bash
DATABASE_URL=postgresql://postgres:postgres@db:5432/acos
POSTGRES_PASSWORD=postgres
POSTGRES_USER=postgres
POSTGRES_DB=acos
APP_VERSION=1.0.0
OPS_ENVIRONMENT=docker
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Next Steps

1. ✅ Complete installation
2. ✅ Run verification tests
3. 📖 Read [USER_GUIDE.md](./USER_GUIDE.md) for feature walkthrough
4. 🧪 Follow [TESTING.md](./TESTING.md) for testing procedures
5. 🚀 Deploy using [DEPLOYMENT.md](./DEPLOYMENT.md)

**Questions?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or open an issue on GitHub.

---

**Last Updated:** March 22, 2026
**Version:** 1.0.0
