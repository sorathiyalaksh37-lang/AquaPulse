# AquaPulse Deployment Guide

## 📋 Prerequisites

### System Requirements
- **OS:** Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Python:** 3.8 or higher
- **Node.js:** 16.x or higher (for frontend)
- **PostgreSQL:** 12.x or higher
- **Redis:** 6.x or higher (for Celery tasks)
- **RAM:** Minimum 2GB, Recommended 4GB+
- **Storage:** 10GB+ free space

### Required Accounts
- SendGrid account (for email notifications)
- Twilio account (for SMS notifications)
- Firebase project (for realtime database)

---

## 🚀 Quick Start (Development)

### 1. Clone Repository
```bash
git clone https://github.com/sorathiyalaksh37-lang/AquaPulse.git
cd AquaPulse
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Environment Variables:**
```env
# Flask
SECRET_KEY=your-super-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/aquapulse

# Firebase
FIREBASE_CREDENTIALS_PATH=./config/firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com/

# SendGrid (Email)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@aquapulse.com

# Twilio (SMS)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Redis
REDIS_URL=redis://localhost:6379/0
```

#### Set up PostgreSQL Database
```bash
# Create database
createdb aquapulse

# Or using psql
psql -U postgres
CREATE DATABASE aquapulse;
\q
```

#### Initialize Database
```bash
# Run main application to create tables
python main_app.py
```

### 3. Run Development Server
```bash
python main_app.py
```

Server will start at: `http://localhost:5001`

---

## 🏭 Production Deployment

### Option 1: Docker Deployment (Recommended)

#### Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p reports temp uploads logs

# Expose port
EXPOSE 5001

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--worker-class", "eventlet", "main_app:app"]
```

#### Create docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: aquapulse
      POSTGRES_USER: aquapulse
      POSTGRES_PASSWORD: securepassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn --bind 0.0.0.0:5001 --workers 4 --worker-class eventlet main_app:app
    volumes:
      - .:/app
      - ./reports:/app/reports
      - ./uploads:/app/uploads
    ports:
      - "5001:5001"
    depends_on:
      - db
      - redis
    env_file:
      - .env

volumes:
  postgres_data:
```

#### Deploy with Docker
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Option 2: Traditional Server Deployment

#### 1. Install System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3-pip python3-venv postgresql redis-server nginx

# Start services
sudo systemctl start postgresql
sudo systemctl start redis
sudo systemctl enable postgresql
sudo systemctl enable redis
```

#### 2. Set up Application
```bash
# Create app directory
sudo mkdir -p /var/www/aquapulse
sudo chown $USER:$USER /var/www/aquapulse
cd /var/www/aquapulse

# Clone repository
git clone https://github.com/sorathiyalaksh37-lang/AquaPulse.git .

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

#### 3. Configure Gunicorn Service
Create `/etc/systemd/system/aquapulse.service`:
```ini
[Unit]
Description=AquaPulse Water Quality Monitoring
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aquapulse
Environment="PATH=/var/www/aquapulse/.venv/bin"
ExecStart=/var/www/aquapulse/.venv/bin/gunicorn \
    --bind 127.0.0.1:5001 \
    --workers 4 \
    --worker-class eventlet \
    --access-logfile /var/log/aquapulse/access.log \
    --error-logfile /var/log/aquapulse/error.log \
    main_app:app

[Install]
WantedBy=multi-user.target
```

#### 4. Configure Nginx
Create `/etc/nginx/sites-available/aquapulse`:
```nginx
server {
    listen 80;
    server_name aquapulse.com www.aquapulse.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aquapulse.com www.aquapulse.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/aquapulse.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aquapulse.com/privkey.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # File Upload Size
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /socket.io {
        proxy_pass http://127.0.0.1:5001/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files
    location /static {
        alias /var/www/aquapulse/static;
        expires 30d;
    }

    # Reports and uploads
    location /reports {
        alias /var/www/aquapulse/reports;
        internal;
    }
}
```

#### 5. Enable and Start Services
```bash
# Create log directory
sudo mkdir -p /var/log/aquapulse
sudo chown www-data:www-data /var/log/aquapulse

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/aquapulse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Start AquaPulse service
sudo systemctl daemon-reload
sudo systemctl start aquapulse
sudo systemctl enable aquapulse

# Check status
sudo systemctl status aquapulse
```

#### 6. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d aquapulse.com -d www.aquapulse.com
```

---

## 🔒 Security Hardening

### 1. Environment Variables
```bash
# Never commit .env file
echo ".env" >> .gitignore

# Use strong secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Database Security
```sql
-- Create dedicated database user
CREATE USER aquapulse_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE aquapulse TO aquapulse_user;
```

### 3. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
pip list --outdated
pip install --upgrade package_name
```

---

## 📊 Monitoring & Logging

### Application Logs
```bash
# View application logs
sudo journalctl -u aquapulse -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Performance Monitoring
- **CPU/Memory:** `htop` or `top`
- **Disk Usage:** `df -h`
- **Database:** `pg_stat_activity`

### Error Tracking
Consider integrating:
- **Sentry** for error tracking
- **New Relic** for APM
- **Datadog** for infrastructure monitoring

---

## 🔄 Backup Strategy

### Database Backup
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump aquapulse > /backups/aquapulse_$DATE.sql
find /backups -name "aquapulse_*.sql" -mtime +7 -delete
```

### Automated Backups
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup_script.sh
```

---

## 🧪 Testing Deployment

### Health Check
```bash
curl http://localhost:5001/health
```

### API Test
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aquapulse.com","password":"admin123"}'
```

### Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Run load test
ab -n 1000 -c 10 http://localhost:5001/health
```

---

## 🔧 Troubleshooting

### Application Won't Start
```bash
# Check logs
sudo journalctl -u aquapulse -n 50

# Check Python errors
source .venv/bin/activate
python main_app.py
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql -U aquapulse_user -d aquapulse -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :5001

# Kill process
kill -9 <PID>
```

---

## 📱 Frontend Deployment (Coming Soon)

The React frontend will be deployed separately:
```bash
# Build frontend
cd frontend
npm run build

# Deploy to Nginx
sudo cp -r build/* /var/www/aquapulse/frontend/
```

---

## 📞 Support

- **Issues:** https://github.com/sorathiyalaksh37-lang/AquaPulse/issues
- **Documentation:** See PROJECT_STATUS.md and API_DOCUMENTATION.md
- **Email:** support@aquapulse.com

---

**Last Updated:** 2026-08-17  
**Version:** 1.0.0
