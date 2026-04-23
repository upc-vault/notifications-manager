# Notifications Manager API - Testing Guide

## Prerequisites

1. **Install Redis** (optional, but recommended):
   ```bash
   # Windows: Download from https://github.com/microsoftarchive/redis/releases
   # Or use Docker:
   docker run -d -p 6379:6379 redis:alpine
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure models are trained**:
   ```bash
   python scripts/train_integrated.py
   ```

## Starting the API

### Option 1: Using the startup script
```bash
python scripts/start_api.py
```

### Option 2: Direct Flask run
```bash
cd src
python -m notifications_manager.api.app
```

API will be available at: `http://localhost:5000`

## API Endpoints

### 1. Health Check
```bash
GET http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "redis": "connected",
  "ml_models": "ready",
  "queue_size": 0
}
```

### 2. Create Notification (ML Decision + Queue)
```bash
POST http://localhost:5000/api/v1/notifications
Content-Type: application/json

{
  "user_id": "user123",
  "notification_type": "transaction_alert",
  "message": "Transaction of $500 detected",
  "user_segment": "premium",
  "priority_hint": "high",
  "time_of_day": "morning"
}
```

Response:
```json
{
  "notification_id": "uuid-here",
  "status": "queued",
  "decision": {
    "template": "urgent",
    "channel": "whatsapp",
    "priority": "HIGH",
    "priority_level": 2,
    "estimated_success_rate": 0.8913,
    "estimated_engagement": 0.6760
  },
  "queue_position": 1
}
```

### 3. View Queue Status
```bash
GET http://localhost:5000/api/v1/queue
```

Response:
```json
{
  "queue_stats": {
    "total_size": 5,
    "total_enqueued": 10,
    "by_priority": {
      "1": 2,
      "2": 3,
      "3": 0,
      "4": 0
    }
  },
  "next_notifications": [...]
}
```

### 4. Dequeue Notifications
```bash
POST http://localhost:5000/api/v1/queue/dequeue?count=5
```

Response:
```json
{
  "count": 5,
  "notifications": [
    {
      "id": "uuid",
      "user_id": "user123",
      "notification_type": "transaction_alert",
      "priority": 2,
      "template": "urgent",
      "channel": "whatsapp",
      "message": "Transaction of $500 detected",
      "context": {...},
      "estimated_success_rate": 0.8913,
      "estimated_engagement": 0.6760
    },
    ...
  ]
}
```

### 5. Submit Feedback (Update ML Models)
```bash
POST http://localhost:5000/api/v1/feedback
Content-Type: application/json

{
  "notification_id": "uuid",
  "template": "urgent",
  "channel": "whatsapp",
  "success": true,
  "engagement": 0.85
}
```

### 6. View ML Model Statistics
```bash
GET http://localhost:5000/api/v1/models/stats
```

## Testing Scenarios

### Scenario 1: Critical Security Alert
```bash
curl -X POST http://localhost:5000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user456",
    "notification_type": "security_alert",
    "message": "Suspicious login attempt detected",
    "user_segment": "premium",
    "time_of_day": "night"
  }'
```

Expected: Priority=CRITICAL, Template=URGENT, Channel=SMS or WhatsApp

### Scenario 2: Promotional Offer
```bash
curl -X POST http://localhost:5000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user789",
    "notification_type": "promotional",
    "message": "Special offer: 0% APR for 12 months",
    "user_segment": "young",
    "time_of_day": "afternoon"
  }'
```

Expected: Priority=LOW, Template=PROMOTIONAL/FRIENDLY, Channel=WhatsApp

### Scenario 3: Transaction Alert
```bash
curl -X POST http://localhost:5000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user101",
    "notification_type": "transaction_alert",
    "message": "Payment of $1,250.00 processed",
    "user_segment": "standard",
    "time_of_day": "evening",
    "priority_hint": "high"
  }'
```

Expected: Priority=HIGH, Template=CONCISE/URGENT, Channel=WhatsApp/Push

## Testing Flow

1. **Start API**: `python scripts/start_api.py`
2. **Check health**: `curl http://localhost:5000/health`
3. **Create notifications**: Use scenarios above
4. **Check queue**: `curl http://localhost:5000/api/v1/queue`
5. **Dequeue**: `curl -X POST http://localhost:5000/api/v1/queue/dequeue?count=3`
6. **Submit feedback**: Update models with results
7. **View stats**: `curl http://localhost:5000/api/v1/models/stats`

## Notes

- **Redis**: If Redis is not running, the system automatically falls back to in-memory queue
- **ML Models**: Decisions are based on trained models from `models/integrated_model.json`
- **Continuous Learning**: Submit feedback to improve model performance over time
- **Priority Queue**: Lower priority number = higher priority (1=CRITICAL, 4=LOW)

## Troubleshooting

**"ML models not initialized"**:
- Run training first: `python scripts/train_integrated.py`

**"Could not connect to Redis"**:
- Redis is optional, system will use in-memory fallback
- To use Redis: Start Redis server or Docker container

**Port already in use**:
- Change port in `.env` file or kill process using port 5000
