# Notification Manager API - Quick Start Guide

## 🚀 Setup

### 1. Install Redis

**Windows (with Chocolatey):**
```bash
choco install redis-64
```

**Or download from:** https://github.com/tporadowski/redis/releases

### 2. Start Redis Server

```bash
redis-server
```

Leave this terminal running.

### 3. Install Python Dependencies

```bash
pip install Flask Flask-CORS redis python-dotenv
```

### 4. Start the API

Open a new terminal:

```bash
python src/api/main.py
```

The API will start on `http://localhost:8080`

## 📡 API Endpoints

### 1. Health Check
```bash
GET http://localhost:8080/
```

### 2. Send Notification (with ML Decision)
```bash
POST http://localhost:8080/api/v1/notification/send

{
  "user_id": "user_123",
  "message_type": "security",
  "data": {
    "title": "Security Alert",
    "body": "Unusual activity detected"
  }
}
```

**Response:**
```json
{
  "status": "queued",
  "notification_id": "uuid",
  "decision": {
    "template": "Security Alert",
    "channel": "push",
    "priority": "critical",
    "priority_score": 1,
    "user_affinity": 0.85,
    "confidence": 0.76,
    "reasoning": "Usuario PRIME | joven tech-savvy | Template 'Security Alert' (afinidad 0.80) | Canal 'push' (afinidad 0.90) | Prioridad CRITICAL"
  },
  "queue_position": 1
}
```

### 3. Get Queue Statistics
```bash
GET http://localhost:8080/api/v1/queue/stats
```

### 4. Peek Next Notification
```bash
GET http://localhost:8080/api/v1/queue/peek
```

### 5. Dequeue Notification
```bash
POST http://localhost:8080/api/v1/queue/dequeue
```

### 6. Send Feedback (Update ML Models)
```bash
POST http://localhost:8080/api/v1/notification/feedback

{
  "user_id": "user_123",
  "template_id": "template_security",
  "channel": "push",
  "success": true,
  "opened": true,
  "clicked": true
}
```

### 7. Cache Statistics
```bash
GET http://localhost:8080/api/v1/cache/stats
```

## 🧪 Test Script

Run the comprehensive test:

```bash
python scripts/test_api.py
```

This will:
- ✅ Test health check
- ✅ Send 3 notifications with different profiles
- ✅ Check queue statistics
- ✅ Peek next notification
- ✅ Dequeue notification
- ✅ Send feedback to ML models
- ✅ Check cache statistics

## 📊 How It Works

### Flow:

1. **API receives request** → `/api/v1/notification/send`
2. **Loads user profile** → From Redis cache or creates demo profile
3. **ML Decision Service** → Uses trained Sleeping Bandit + TOW models
   - Selects best **template** (Urgent, Security, Promo, Info)
   - Selects best **channel** (Push, Email, SMS, WhatsApp, WebPush)
   - Calculates **priority** (Critical, High, Medium, Low)
4. **Enqueues notification** → Priority queue in Redis
5. **Returns decision** → With reasoning and confidence

### ML Integration:

- **Sleeping Bandit**: Chooses notification template based on user engagement
- **Tug of War**: Selects delivery channel based on success rates
- **User Profiles**: Considers age, banking tier, digital adoption
- **Redis Cache**: Stores ML models per-user (1 hour TTL)

## 📈 Monitoring

### Check Queue:
```bash
curl http://localhost:8080/api/v1/queue/stats
```

### Check Cache:
```bash
curl http://localhost:8080/api/v1/cache/stats
```

## 🔧 Configuration

Edit `.env` file:

```env
# Server
PORT=8080
DEBUG=true

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_CACHE_TTL=3600

# ML Models
ML_BANDIT_EPSILON=0.1
ML_BANDIT_DECAY=0.995
```

## 🎯 Example Usage (Python)

```python
import requests

# Send notification
response = requests.post(
    "http://localhost:8080/api/v1/notification/send",
    json={
        "user_id": "user_young_tech",
        "message_type": "promo",
        "data": {
            "title": "Special Offer!",
            "body": "50% discount on loans"
        }
    }
)

decision = response.json()
print(f"Template: {decision['decision']['template']}")
print(f"Channel: {decision['decision']['channel']}")
print(f"Priority: {decision['decision']['priority']}")
print(f"Reasoning: {decision['decision']['reasoning']}")
```

## 🐛 Troubleshooting

**Redis not connected:**
- Make sure Redis server is running: `redis-server`
- Check port 6379 is available

**Import errors:**
- Install missing dependencies: `pip install -r requirements.txt`

**Module not found:**
- Make sure you're in the project root directory

## ✅ Success Indicators

When everything works, you should see:

```
✓ Redis connected: localhost:6379
✓ Notification Decision Service initialized
✓ Priority Queue Service initialized
🚀 Starting Intelligent Notification Manager API
📍 Server: http://localhost:8080
```
