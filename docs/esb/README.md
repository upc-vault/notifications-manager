# Enterprise Service Bus (ESB) Documentation

## Overview

The ESB (Enterprise Service Bus) is the integration and delivery layer that:
- Consumes notifications from the priority queue
- Routes to external providers (Twilio, WhatsApp, SendGrid, Firebase)
- Implements retry logic and circuit breaker patterns
- Sends delivery feedback to ML models
- Provides monitoring and metrics

## Architecture

```
┌─────────────────┐
│   Flask API     │
│  (ML Decisions) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Priority Queue  │
│   (Redis)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  ESB Consumer   │◄─────┤ Message      │
│  (Polling)      │      │ Broker       │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│   ESB Service   │
│   (Routing)     │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
┌───────┐ ┌──────┐ ┌─────┐ ┌──────┐
│  SMS  │ │WhatsApp│Email│ │Push  │
│(Twilio)│(WA API)│(S.Grid)│(FCM)│
└───────┘ └──────┘ └─────┘ └──────┘
    │         │        │        │
    └─────────┴────────┴────────┘
              │
              ▼
    ┌─────────────────┐
    │  Feedback Loop  │
    │  (ML Updates)   │
    └─────────────────┘
```

## Components

### 1. ESB Service (`esb_service.py`)
Core routing and delivery logic:
- Provider management
- Retry logic with exponential backoff
- Circuit breaker implementation
- Metrics collection
- Feedback submission

### 2. ESB Consumer (`consumer.py`)
Continuous polling and processing:
- Polls priority queue at configurable intervals
- Processes notifications in batches
- Handles graceful shutdown
- Error recovery

### 3. Message Broker (`message_broker.py`)
Redis pub/sub messaging:
- `notifications.pending` - New notifications
- `notifications.delivered` - Successful deliveries
- `notifications.failed` - Failed attempts
- `notifications.feedback` - ML feedback

### 4. Providers (`providers/`)
Channel-specific adapters:
- **SMSProvider**: Twilio integration
- **WhatsAppProvider**: WhatsApp Business API
- **EmailProvider**: SendGrid integration
- **PushProvider**: Firebase Cloud Messaging

## Configuration

### Environment Variables

```bash
# API Configuration
API_BASE_URL=http://localhost:5000

# ESB Configuration
ESB_POLL_INTERVAL=2.0
ESB_BATCH_SIZE=10

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# WhatsApp Business
WHATSAPP_API_KEY=your_api_key
WHATSAPP_PHONE_ID=your_phone_number_id
WHATSAPP_BA_ID=your_business_account_id

# SendGrid (Email)
SENDGRID_API_KEY=your_api_key
EMAIL_FROM=notifications@yourbank.com
EMAIL_FROM_NAME=Bank Notifications

# Firebase (Push)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_CREDS=path/to/firebase-credentials.json
```

## Running the ESB

### Start ESB Consumer

```bash
python scripts/start_esb.py
```

The consumer will:
1. Connect to the API and Redis
2. Poll the priority queue every 2 seconds (configurable)
3. Process notifications in batches of 10 (configurable)
4. Route to appropriate providers
5. Send feedback to ML models

### Full System Startup

**Terminal 1 - Flask API:**
```bash
python scripts/start_api.py
```

**Terminal 2 - ESB Consumer:**
```bash
python scripts/start_esb.py
```

**Terminal 3 - Test notifications:**
```bash
irm http://localhost:5000/api/v1/notifications -Method POST -ContentType "application/json" -Body '{"user_id":"user123","notification_type":"transaction_alert","message":"Transaction of $500 detected","user_segment":"premium"}'
```

## Features

### Retry Logic
- Automatic retry on failure (default: 3 attempts)
- Exponential backoff: 5s, 10s, 20s
- Configurable per provider

### Circuit Breaker
- Prevents cascading failures
- Opens circuit after threshold failures
- Half-open state for recovery testing

### Dead Letter Queue
- Stores permanently failed notifications
- Enables manual review and reprocessing
- Alerts for critical failures

### Feedback Loop
- Real-time delivery status → ML models
- Continuous model improvement
- Success rate tracking per channel/template

### Monitoring
- Delivery metrics by channel
- Success/failure rates
- Average delivery time
- Provider health status

## Metrics Endpoint

```bash
GET http://localhost:5000/api/v1/esb/metrics
```

Response:
```json
{
  "total_processed": 1250,
  "successful": 1180,
  "failed": 70,
  "retried": 45,
  "success_rate": 0.944,
  "by_channel": {
    "whatsapp": {"total": 650, "successful": 625, "failed": 25},
    "sms": {"total": 350, "successful": 340, "failed": 10},
    "email": {"total": 200, "successful": 180, "failed": 20},
    "push": {"total": 50, "successful": 35, "failed": 15}
  }
}
```

## Provider Integration

### SMS (Twilio)
```python
# Production setup
from twilio.rest import Client
client = Client(account_sid, auth_token)
message = client.messages.create(
    body=message,
    from_=from_number,
    to=recipient
)
```

### WhatsApp Business API
```python
# Production setup
import requests
response = requests.post(
    f"https://graph.facebook.com/v18.0/{phone_id}/messages",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
)
```

### Email (SendGrid)
```python
# Production setup
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

client = SendGridAPIClient(api_key)
message = Mail(
    from_email='notifications@bank.com',
    to_emails=recipient,
    subject='Notification',
    plain_text_content=message
)
response = client.send(message)
```

### Push (Firebase)
```python
# Production setup
import firebase_admin
from firebase_admin import messaging

message = messaging.Message(
    notification=messaging.Notification(
        title='Bank Notification',
        body=message
    ),
    token=recipient
)
response = messaging.send(message)
```

## Demo Mode

Currently, all providers run in **demo mode**:
- No real API calls to external services
- Simulated delivery with realistic delays
- 100% success rate for testing
- Enable production mode by setting API keys

## Troubleshooting

**ESB not processing notifications:**
- Check API is running: `curl http://localhost:5000/health`
- Check Redis is running: `redis-cli ping`
- Check ESB logs: `logs/esb.log`

**All deliveries failing:**
- Check provider configuration
- Verify API keys (if production mode)
- Check network connectivity

**Slow processing:**
- Increase batch size: `ESB_BATCH_SIZE=20`
- Decrease poll interval: `ESB_POLL_INTERVAL=1.0`
- Scale horizontally: run multiple ESB consumers

## Next Steps

1. Configure real provider API keys
2. Set up monitoring and alerting
3. Implement dashboard for metrics
4. Add more channels (Slack, Telegram, etc.)
5. Implement advanced circuit breaker
6. Add A/B testing capabilities
