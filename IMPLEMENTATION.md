# Notifications Manager - Complete Implementation Guide

## Overview
Machine learning-powered notification management system that optimizes notification delivery using multi-armed bandit algorithms.

## Architecture Components

### 1. API Layer (nm.py)
- Flask REST API for notification management
- ML-powered template optimization
- Feedback tracking system
- Health monitoring

### 2. ML Layer (bandit_algorithm.py)
- Epsilon-greedy and UCB bandit algorithms
- Real-time learning from user feedback
- Template-user optimization
- Model persistence

### 3. Message Queue (message_queue.py)
- RabbitMQ producer/consumer
- Async notification processing
- Durable queues with acknowledgments

### 4. Workers
- **Notification Worker** (worker.py): Sends notifications
- **Feedback Worker** (feedback_worker.py): Updates ML model

### 5. Database Layer (database.py)
- SQLAlchemy models for notifications
- Template performance tracking
- Feedback integration

### 6. Configuration (config.py)
- Environment-based settings
- Connection URL builders
- Service configuration

## Quick Start

### Using Docker Compose (Recommended)

1. **Start all services:**
```bash
docker-compose up -d
```

2. **Check status:**
```bash
docker-compose ps
docker-compose logs -f api
```

3. **Access services:**
- API: http://localhost:5000
- RabbitMQ Management: http://localhost:15672 (admin/admin123)
- Redis: localhost:6379

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Initialize database:**
```bash
python scripts/init_db.py
```

4. **Start services:**
```bash
# Terminal 1: Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 2: Start RabbitMQ
docker run -d -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=admin \
  -e RABBITMQ_DEFAULT_PASS=admin123 \
  rabbitmq:3-management

# Terminal 3: Start API
python -m notifications_manager.nm

# Terminal 4: Start notification worker
python -m notifications_manager.worker

# Terminal 5: Start feedback worker
python -m notifications_manager.feedback_worker
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Send Notification
```bash
POST /notifications/v1/send-notification
Content-Type: application/json

{
  "sender": {"id": "system"},
  "receiver": {"id": "user123"},
  "channelCode": "email",
  "notificationType": "promotional",
  "sendingTime": "2026-04-04T10:00:00",
  "data": [{"key": "name", "value": "John"}]
}
```

### Optimize Template (ML)
```bash
POST /notifications/v1/optimize-template
Content-Type: application/json

{
  "user_id": "user123",
  "available_templates": ["template1", "template2", "template3"]
}
```

### Record Feedback
```bash
POST /notifications/v1/feedback
Content-Type: application/json

{
  "notification_id": "uuid-here",
  "was_tapped": true
}
```

### Get Statistics
```bash
GET /notifications/v1/stats
```

### Get User History
```bash
GET /notifications/v1/history/user123?limit=50
```

## Machine Learning

### Bandit Algorithms

**Epsilon-Greedy** (Default)
- Explores random templates with probability ε (0.1)
- Exploits best-performing templates otherwise
- Simple and effective for most use cases

**UCB (Upper Confidence Bound)**
- Balances exploration/exploitation using confidence intervals
- Automatically adjusts exploration based on uncertainty
- More sophisticated than epsilon-greedy

### Configuration

Set in environment variables or .env file:
```bash
BANDIT_STRATEGY=epsilon_greedy  # or 'ucb'
BANDIT_EPSILON=0.1              # for epsilon-greedy
BANDIT_MODEL_PATH=models/bandit_model.pkl
```

### How It Works

1. **Initial Phase**: Randomly selects templates to gather data
2. **Learning Phase**: Updates reward estimates based on user taps
3. **Optimization Phase**: Selects best templates per user
4. **Continuous Learning**: Adapts to changing user preferences

## Data Models

### Notification
```python
{
  "id": "uuid",
  "sender": {"id": "sender_id"},
  "receiver": {"id": "user_id"},
  "channelCode": "email|sms|push",
  "notificationType": "promotional|transactional",
  "sendingTime": "ISO 8601 datetime",
  "data": [{"key": "name", "value": "John"}],
  "attachments": [{"id": "uuid", "name": "file.pdf"}]
}
```

### Database Schema

- **notification_logs**: All notification records with engagement data
- **template_performance**: Aggregated metrics per template-user pair

## Configuration Options

### Environment Variables

```bash
# Flask Settings
DEBUG=False
HOST=0.0.0.0
PORT=5000

# Database
DATABASE_URL=sqlite:///notifications.db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# ML Algorithm
BANDIT_STRATEGY=epsilon_greedy
BANDIT_EPSILON=0.1
BANDIT_MODEL_PATH=models/bandit_model.pkl
```

## Monitoring & Debugging

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f feedback-worker
```

### RabbitMQ Dashboard
Access at http://localhost:15672 to monitor:
- Queue sizes and message rates
- Worker connections
- Message acknowledgments

### ML Model Stats
```bash
curl http://localhost:5000/notifications/v1/stats
```

## Production Deployment

### Scaling

**Horizontal Scaling:**
```bash
docker-compose up -d --scale worker=5 --scale feedback-worker=3
```

**Resource Limits:**
Update docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
```

### Security Checklist

- [ ] Use environment-specific configurations
- [ ] Enable authentication on RabbitMQ
- [ ] Use Redis password
- [ ] Set up SSL/TLS for API
- [ ] Implement rate limiting
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Configure proper logging
- [ ] Set up monitoring alerts

## Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### Database issues
```bash
# Reinitialize
python scripts/init_db.py

# Check tables
sqlite3 notifications.db ".tables"
```

### Queue backing up
- Scale up workers
- Check worker logs for errors
- Verify RabbitMQ connection
- Monitor queue depths

### ML model not learning
- Ensure feedback is being sent
- Check feedback worker logs
- Verify model file permissions
- Review bandit statistics

## Testing

### Manual Testing
```bash
# Health check
curl http://localhost:5000/health

# Send test notification
curl -X POST http://localhost:5000/notifications/v1/send-notification \
  -H "Content-Type: application/json" \
  -d @tests/sample_notification.json
```

### Load Testing
Use the included JMeter test file: `tests/Send Notifications.jmx`

## Development Tips

### Adding New Notification Channels

1. Update `worker.py` with new channel handler:
```python
def _send_new_channel(self, notification_data: dict):
    # Implement channel-specific logic
    pass
```

2. Add channel routing in `send_notification` method

### Extending ML Algorithm

1. Add new strategy in `bandit_algorithm.py`:
```python
def _new_strategy_select(self, user_id, templates):
    # Implement strategy
    pass
```

2. Update `select_template` method to use new strategy

## License

MIT License - See [LICENSE](LICENSE)

## Support

For issues and questions:
- Review documentation
- Check logs
- Open GitHub issue

---

**Version**: 1.0.0  
**Last Updated**: April 2026
