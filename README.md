# Notifications Manager

Machine-learning powered notifications management system that optimizes notification delivery using multi-armed bandit algorithms.

## 🚀 Quick Start

**Start the full stack with Docker Compose:**
```bash
docker-compose up -d
```

This starts:
- **API** at http://localhost:5000
- **RabbitMQ** at http://localhost:15672 (admin/admin123)
- **Redis** at localhost:6379
- Notification workers
- Feedback workers

**Check service health:**
```bash
curl http://localhost:5000/health
```

## 📋 Features

- ✅ **ML-Powered Optimization**: Bandit algorithms learn which notifications work best for each user
- ✅ **Multiple Strategies**: Epsilon-greedy and UCB algorithms
- ✅ **Real-time Learning**: Continuously improves from user feedback
- ✅ **Async Processing**: RabbitMQ-based message queue
- ✅ **Scalable**: Docker-based deployment with horizontal scaling
- ✅ **Full API**: REST endpoints for sending, tracking, and analyzing notifications
- ✅ **Analytics**: Track performance metrics and CTR per template

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  Flask API   │────▶│  RabbitMQ   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Redis     │     │   Workers   │
                    │   (Cache)    │     │  (Senders)  │
                    └──────────────┘     └─────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Database   │◀────│  Feedback   │
                    │  (SQLite)    │     │   Worker    │
                    └──────────────┘     └─────────────┘
                           │                      │
                           └──────────┬───────────┘
                                      ▼
                              ┌──────────────┐
                              │ ML Algorithm │
                              │   (Bandit)   │
                              └──────────────┘
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/notifications/v1/send-notification` | POST | Queue notification |
| `/notifications/v1/optimize-template` | POST | Get best template for user |
| `/notifications/v1/feedback` | POST | Record user engagement |
| `/notifications/v1/stats` | GET | ML model statistics |
| `/notifications/v1/history/<user_id>` | GET | User notification history |

## 💡 Usage Example

**Send a notification:**
```bash
curl -X POST http://localhost:5000/notifications/v1/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "sender": {"id": "system"},
    "receiver": {"id": "user123"},
    "channelCode": "email",
    "notificationType": "promotional",
    "sendingTime": "2026-04-04T10:00:00",
    "data": [{"key": "name", "value": "John"}]
  }'
```

**Get optimal template:**
```bash
curl -X POST http://localhost:5000/notifications/v1/optimize-template \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "available_templates": ["template1", "template2", "template3"]
  }'
```

**Record feedback:**
```bash
curl -X POST http://localhost:5000/notifications/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"notification_id": "uuid", "was_tapped": true}'
```

## 🤖 Machine Learning

The system uses **Multi-Armed Bandit algorithms** to optimize notification delivery:

- **Epsilon-Greedy**: Balances exploration (10%) vs exploitation (90%)
- **UCB**: Uses confidence bounds for intelligent exploration

The algorithm learns from user engagement (taps/clicks) to select the best template for each user.

## 🛠️ Development

**Local setup:**
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Start services (Redis, RabbitMQ)
docker-compose up -d redis rabbitmq

# Run API
python -m notifications-manager.nm

# Run workers (separate terminals)
python -m notifications-manager.worker
python -m notifications-manager.feedback_worker
```

## 🚢 Production Deployment

**Scale workers:**
```bash
docker-compose up -d --scale worker=5 --scale feedback-worker=3
```

**Environment configuration:**
- Copy `.env.example` to `.env`
- Update with production credentials
- Configure database, Redis, RabbitMQ URLs

## 📊 Monitoring

- **RabbitMQ Dashboard**: http://localhost:15672
- **API Health**: http://localhost:5000/health
- **ML Stats**: http://localhost:5000/notifications/v1/stats
- **Logs**: `docker-compose logs -f`

## 📁 Project Structure

```
notifications-manager/
├── notifications-manager/    # Main application
│   ├── nm.py                 # Flask API
│   ├── config.py             # Configuration
│   ├── database.py           # Database models
│   ├── bandit_algorithm.py   # ML implementation
│   ├── message_queue.py      # RabbitMQ integration
│   ├── worker.py             # Notification worker
│   ├── feedback_worker.py    # Feedback worker
│   └── model/                # Pydantic models
├── tests/                    # Test files
├── scripts/                  # Utility scripts
├── docker-compose.yml        # Full stack orchestration
├── Dockerfile                # Container image
└── requirements.txt          # Python dependencies
```

## 📝 License

MIT License - See [LICENSE](LICENSE)

## 👥 Contributors

UPC PI2 Project - 2025-2026

---

**Status**: ✅ Fully Implemented  
**Version**: 1.0.0  
**Last Updated**: April 2026
Machine-learning powered notifications manager

Gobierno, conceptualizar mejor
Datos, no queda claro como centralizaremos los datos, no queda claro como ml usara esos datos
Plataformas, documentar sobre plataformas
Hacer una interfaz, se debe desarrollar todo
