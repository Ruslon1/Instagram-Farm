# 🚀 Instagram Bot - Professional Automation Platform

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A production-ready Instagram automation platform** with advanced proxy support, real-time progress tracking, and intuitive web interface for content creators and marketing teams.

![Instagram Bot Dashboard](https://via.placeholder.com/800x400/1f2937/ffffff?text=Instagram+Bot+Dashboard)

## ✨ Features

### 🎯 **Core Functionality**
- **Automated Video Upload** - Schedule and upload videos to multiple Instagram accounts
- **TikTok Content Fetching** - Automatically source content from TikTok creators
- **Multi-Account Management** - Handle dozens of Instagram accounts simultaneously
- **Advanced Proxy Support** - Residential/datacenter proxy integration with health monitoring
- **Real-time Progress Tracking** - Live task monitoring with detailed progress indicators

### 🛡️ **Security & Reliability**
- **Session Management** - Persistent login sessions with automatic refresh
- **2FA Authentication** - Full support for Instagram two-factor authentication
- **Proxy Health Monitoring** - Automatic proxy validation and failover
- **Account Verification** - Built-in credential verification before account activation
- **Rate Limiting** - Smart delays and cooldowns to avoid Instagram restrictions

### 📊 **Management & Monitoring**
- **Modern Web Interface** - Responsive React-based dashboard
- **Task Queue System** - Celery-powered background job processing
- **Real-time Notifications** - Telegram integration for instant alerts
- **Detailed Analytics** - Comprehensive statistics and performance metrics
- **Health Monitoring** - Built-in health checks and system diagnostics

### 🔧 **Technical Excellence**
- **Microservices Architecture** - Dockerized components for easy scaling
- **Database Persistence** - PostgreSQL with proper indexing and optimization
- **Redis Caching** - High-performance task queue and session storage
- **Structured Logging** - Comprehensive logging with JSON formatting
- **API Documentation** - Auto-generated OpenAPI/Swagger documentation

## 🏗️ Architecture

```mermaid
graph TB
    UI[React Frontend] --> API[FastAPI Backend]
    API --> DB[(PostgreSQL)]
    API --> REDIS[(Redis)]
    API --> CELERY[Celery Worker]
    CELERY --> INSTA[Instagram API]
    CELERY --> TIKTOK[TikTok Scraper]
    CELERY --> PROXY[Proxy Network]
    API --> TELEGRAM[Telegram Bot]
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM
- 10GB+ disk space

### 1. Clone Repository
```bash
git clone https://github.com/your-username/instagram-bot.git
cd instagram-bot
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Environment Variables:**
```env
# Telegram Notifications
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Database Security
POSTGRES_PASSWORD=secure_password_123

# TikTok Integration
MS_TOKENS=your_ms_tokens_comma_separated

# Security
SECRET_KEY=your-super-secret-key-32-chars-minimum
```

### 3. Launch Platform
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Access Dashboard
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📖 Usage Guide

### Adding Instagram Accounts

1. **Navigate to Accounts** in the web interface
2. **Click "Add Account"** and enter credentials
3. **Automatic Verification** - System validates login and creates session
4. **Configure Proxy** (optional) for enhanced security
5. **Account Ready** for automation tasks

### Setting Up Content Sources

1. **Go to TikTok Sources** section
2. **Add Creator Accounts** by username and theme
3. **Configure Fetch Settings** (videos per account, frequency)
4. **Activate Sources** to begin content discovery

### Running Upload Campaigns

1. **Fetch Videos** from configured TikTok sources
2. **Review Content** in the Videos section
3. **Select Target Account** and videos to upload
4. **Start Upload Task** with automatic scheduling
5. **Monitor Progress** in real-time through Tasks section

### Advanced Features

#### Proxy Configuration
```bash
# Proxy types supported:
- HTTP/HTTPS proxies
- SOCKS5 proxies
- Authentication support
- Automatic health monitoring
```

#### Task Management
- **Real-time Progress**: Live updates with cooldown timers
- **Cancellation Support**: Stop tasks mid-execution
- **Error Handling**: Automatic retry with exponential backoff
- **Detailed Logging**: Complete audit trail for all operations

## 🔧 Configuration

### Docker Compose Services

| Service | Description | Port | Health Check |
|---------|-------------|------|--------------|
| **app** | FastAPI Backend | 8000 | `/health` |
| **frontend** | React Dashboard | 3000 | HTTP 200 |
| **postgres** | Database | 5432 | `pg_isready` |
| **redis** | Cache & Queue | 6379 | `ping` |
| **celery** | Background Worker | - | Process Monitor |

### Environment Variables

#### Core Application
```env
APP_NAME="Instagram Bot API"
APP_VERSION="2.0.0"
ENVIRONMENT=production
DEBUG=false
```

#### Database Configuration
```env
# PostgreSQL (auto-configured in Docker)
DATABASE_URL=postgresql://user:pass@postgres:5432/db
REDIS_URL=redis://redis:6379/0
```

#### Security Settings
```env
SECRET_KEY=your-secret-key-minimum-32-characters
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### External Services
```env
# Telegram Bot Integration
TELEGRAM_TOKEN=bot_token_from_botfather
TELEGRAM_CHAT_ID=your_telegram_chat_id

# TikTok API Tokens
MS_TOKENS=token1,token2,token3
```

#### Browser Automation
```env
# Chrome/Selenium Settings
CHROME_OPTIONS=--headless,--no-sandbox,--disable-dev-shm-usage
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

## 📊 Monitoring & Maintenance

### Health Monitoring
```bash
# Check all service health
./monitor.sh status

# Detailed system information
./monitor.sh full

# View recent logs
./monitor.sh logs

# Check for errors
./monitor.sh errors
```

### Database Management
```bash
# Backup database
docker-compose exec postgres pg_dump -U instagram_bot instagram_bot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U instagram_bot instagram_bot < backup.sql
```

### Performance Optimization
```bash
# View resource usage
./monitor.sh resources

# Scale Celery workers
docker-compose up -d --scale celery=3

# Monitor task queue
docker-compose exec redis redis-cli LLEN celery
```

## 🛠️ Development

### Local Development Setup
```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend development
cd frontend
npm install
npm run dev
```

### API Development
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Database Schema
```sql
-- Core tables
accounts           -- Instagram account management
videos            -- Content library
tiktok_sources    -- Content source configuration
task_logs         -- Job execution tracking
publicationhistory -- Upload audit trail
```

## 🔒 Security Considerations

### Account Security
- ✅ **Session Encryption** - All login sessions encrypted at rest
- ✅ **2FA Support** - Full Instagram 2FA integration
- ✅ **Proxy Isolation** - Each account can use dedicated proxy
- ✅ **Rate Limiting** - Smart delays prevent account restrictions

### Infrastructure Security
- ✅ **Container Isolation** - Dockerized services with minimal privileges
- ✅ **Network Segmentation** - Internal Docker network isolation
- ✅ **Secrets Management** - Environment-based configuration
- ✅ **HTTPS Ready** - Production-ready with reverse proxy support

### Data Protection
- ✅ **Encrypted Storage** - Sensitive data encrypted in database
- ✅ **Audit Logging** - Complete audit trail for compliance
- ✅ **Backup Strategy** - Automated database backups
- ✅ **GDPR Compliance** - User data management tools

## 📈 Performance & Scaling

### Horizontal Scaling
```yaml
# Scale specific services
docker-compose up -d --scale celery=5
docker-compose up -d --scale app=3
```

### Resource Requirements

| Component | Minimum | Recommended | Heavy Load |
|-----------|---------|-------------|------------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **RAM** | 4GB | 8GB | 16GB+ |
| **Storage** | 20GB | 50GB | 100GB+ |
| **Network** | 10Mbps | 50Mbps | 100Mbps+ |

### Performance Tuning
- **Database Indexing** - Optimized queries with proper indexes
- **Redis Optimization** - Memory-efficient task queue configuration
- **Connection Pooling** - Database connection optimization
- **Caching Strategy** - Multi-level caching for API responses

### Development Workflow
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **TypeScript**: ESLint, Prettier formatting
- **Testing**: Unit tests for all new features
- **Documentation**: Update README for significant changes

## 🆘 Support

### Getting Help
- 📖 **Documentation**: Check this README and inline docs
- 🐛 **Bug Reports**: Open an issue with detailed reproduction steps
- 💡 **Feature Requests**: Submit enhancement proposals
- 💬 **Discussions**: Join our community discussions

### Troubleshooting

#### Common Issues

**Service Won't Start**
```bash
# Check logs
docker-compose logs app

# Restart services
docker-compose restart
```

**Database Connection Issues**
```bash
# Verify database health
docker-compose exec postgres pg_isready -U instagram_bot

# Reset database
docker-compose down -v
docker-compose up -d
```

**Frontend CSS Issues**
```bash
# Clear browser cache
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

**Instagram Login Problems**
- Verify credentials in account settings
- Check if 2FA is properly configured
- Review proxy settings if enabled
- Use account verification feature

## 🏆 Acknowledgments

- **FastAPI** - Modern Python web framework
- **React** - Frontend user interface library
- **Instagrapi** - Instagram API integration
- **Celery** - Distributed task queue
- **PostgreSQL** - Reliable database system
- **Docker** - Containerization platform

---

<div align="center">

**[⭐ Star this repo](https://github.com/your-username/instagram-bot)** if you find it useful!

Made with ❤️ by me
</div>