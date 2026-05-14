# 🌐 Web Push Integration Guide

## Overview

The Intelligent Notification Manager now includes **real Web Push support** for browser notifications. This allows sending push notifications to users' browsers using the W3C Push API and RFC 8030 Web Push Protocol with VAPID authentication.

---

## 🏗️ Architecture

### Components

1. **WebPushProvider** (`src/providers/webpush_provider.py`)
   - Real implementation using `pywebpush` library
   - VAPID (Voluntary Application Server Identification) authentication
   - Subscription management
   - RFC 8030 compliant

2. **API Endpoints** (`src/api/main.py`)
   - `/api/v1/webpush/vapid-public-key` - Get public key for browser
   - `/api/v1/webpush/subscribe` - Register browser subscription
   - `/api/v1/webpush/unsubscribe` - Remove subscription
   - `/api/v1/webpush/subscriptions` - List all subscriptions
   - `/api/v1/webpush/test` - Send test notification

3. **Service Worker** (`static/sw.js`)
   - Handles push events
   - Displays notifications
   - Manages notification clicks

4. **Test Page** (`static/webpush-test.html`)
   - Interactive browser test interface
   - Subscribe/unsubscribe functionality
   - Send test notifications

---

## 🚀 Quick Start

### Step 1: Generate VAPID Keys

VAPID keys are already generated and configured. If you need new keys:

```bash
python scripts/generate_vapid_keys.py
```

This creates `config/vapid_keys.json` with:
- **Public Key**: Share with browsers (safe to expose)
- **Private Key**: Server-side only (keep secret)

### Step 2: Start the API Server

```bash
python src/api/main.py
```

The API will start on `http://localhost:8080`

### Step 3: Open the Test Page

Navigate to: **http://localhost:8080/static/webpush-test.html**

Or open `static/webpush-test.html` directly in your browser.

### Step 4: Subscribe to Notifications

1. Enter a User ID (e.g., `user_demo_1`)
2. Click "Subscribe to Push Notifications"
3. Grant permission when your browser prompts
4. Your subscription is now registered!

### Step 5: Send a Test Notification

1. Fill in the notification title and body
2. Click "Send Test Notification"
3. You should see a browser notification appear!

---

## 📡 API Reference

### Get VAPID Public Key

```http
GET /api/v1/webpush/vapid-public-key
```

**Response:**
```json
{
  "publicKey": "BDmOn0WsFwd1jG8k8xhti8HPbNPVEHJ28B7ERD7LKavyfXhrPDoCsfXSn8fWb2iQEH84zIKRBzc4s_Y2aJVxPaw"
}
```

### Subscribe to Web Push

```http
POST /api/v1/webpush/subscribe
Content-Type: application/json

{
  "user_id": "user_123",
  "subscription": {
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
      "p256dh": "...",
      "auth": "..."
    }
  }
}
```

**Response:**
```json
{
  "status": "subscribed",
  "message": "Web Push subscription registered for user user_123",
  "user_id": "user_123"
}
```

### Send Test Notification

```http
POST /api/v1/webpush/test
Content-Type: application/json

{
  "user_id": "user_123",
  "title": "Test Notification",
  "body": "This is a test message",
  "icon": "/icon.png",
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "status": "sent",
  "message": "Test notification sent successfully",
  "delivery_result": {
    "message_id": "abc-123",
    "latency_ms": 150.5,
    "timestamp": 1715356800.0
  }
}
```

### List All Subscriptions

```http
GET /api/v1/webpush/subscriptions
```

**Response:**
```json
{
  "total_subscriptions": 3,
  "subscriptions": [
    {
      "user_id": "user_123",
      "endpoint": "https://fcm.googleapis.com/fcm/send/...",
      "created_at": 1715356800.0
    }
  ]
}
```

---

## 🔄 Integration with ML Decision Service

Web Push is automatically available as a channel for the ML algorithms to select.

### Send Notification via ML Decision Flow

```http
POST /api/v1/notification/send
Content-Type: application/json

{
  "user_id": "user_demo_1",
  "message_type": "security",
  "data": {
    "title": "Security Alert",
    "body": "Unusual login detected",
    "url": "https://www.bbva.com/security"
  }
}
```

The system will:
1. **Sleeping Bandit** selects the best template
2. **Tug of War** selects the best channel (could be webpush!)
3. Notification is queued by priority
4. Queue Publisher sends to ESB
5. ESB routes to WebPush provider
6. Browser receives the notification

---

## 🎨 Notification Payload Structure

### Standard Notification Fields

```javascript
{
  "title": "Notification Title",           // Required
  "body": "Notification body text",        // Required
  "icon": "/icon.png",                     // Icon URL
  "badge": "/badge.png",                   // Badge URL
  "image": "/hero-image.png",              // Large image
  "tag": "unique-tag",                     // Group similar notifications
  "requireInteraction": false,             // Keep visible until clicked
  "silent": false,                         // No sound/vibration
  "data": {                                // Custom data
    "url": "https://example.com",
    "message_id": "abc-123",
    "extra": "data"
  },
  "actions": [                             // Action buttons
    {
      "action": "view",
      "title": "View",
      "icon": "/view-icon.png"
    },
    {
      "action": "dismiss",
      "title": "Dismiss"
    }
  ]
}
```

---

## 🔧 Configuration

### Environment Variables

Add to `.env` file:

```env
# Web Push Configuration
WEBPUSH_VAPID_PUBLIC_KEY="BDmOn0WsFwd1jG8k8xhti8HPbNPVEHJ28B7ERD7LKavyfXhrPDoCsfXSn8fWb2iQEH84zIKRBzc4s_Y2aJVxPaw"
WEBPUSH_VAPID_PRIVATE_KEY="<see config/vapid_keys.json>"
WEBPUSH_VAPID_ADMIN_EMAIL="admin@bbva-notifications.com"
```

### Settings in `config/settings.py`

```python
WEBPUSH_VAPID_PRIVATE_KEY = os.getenv("WEBPUSH_VAPID_PRIVATE_KEY", "...")
WEBPUSH_VAPID_PUBLIC_KEY = os.getenv("WEBPUSH_VAPID_PUBLIC_KEY", "...")
WEBPUSH_VAPID_ADMIN_EMAIL = os.getenv("WEBPUSH_VAPID_ADMIN_EMAIL", "admin@example.com")
```

---

## 🧪 Testing

### Manual Browser Test

1. Start API: `python src/api/main.py`
2. Open: http://localhost:8080/static/webpush-test.html
3. Subscribe with user ID
4. Send test notifications

### Programmatic Test

```python
from src.providers.webpush_provider import webpush_provider
from src.services.esb import ESBMessage
import uuid

# Register a subscription (from browser)
subscription_data = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "keys": {
        "p256dh": "...",
        "auth": "..."
    }
}
webpush_provider.register_subscription("user_123", subscription_data)

# Send notification
message = ESBMessage(
    message_id=str(uuid.uuid4()),
    message_type="notification",
    channel="webpush",
    destination="user_123",
    payload={
        "title": "Test",
        "body": "Hello from Python!",
        "icon": "/icon.png"
    }
)

result = webpush_provider.send(message)
print(f"Success: {result.success}, Latency: {result.latency_ms}ms")
```

---

## 🌍 Browser Compatibility

Web Push is supported in:

- ✅ **Chrome** 42+ (Desktop & Android)
- ✅ **Firefox** 44+ (Desktop & Android)
- ✅ **Edge** 17+
- ✅ **Opera** 37+
- ✅ **Safari** 16+ (macOS 13+, iOS 16.4+)
- ✅ **Samsung Internet** 4+

**Note**: iOS Safari requires iOS 16.4+ and user must add site to Home Screen.

---

## 🔒 Security Best Practices

### 1. VAPID Keys
- **Private key**: Never commit to version control
- Store in environment variables or secrets manager
- Rotate keys periodically

### 2. HTTPS Required
- Web Push only works over HTTPS (except localhost)
- Use valid SSL certificates in production

### 3. User Consent
- Always request permission explicitly
- Provide clear opt-out mechanism
- Respect user preferences

### 4. Subscription Management
- Clean up expired subscriptions (410 Gone responses)
- Handle subscription changes gracefully
- Store subscriptions securely

---

## 📊 Monitoring & Analytics

### Track Delivery Metrics

```python
# Get WebPush provider statistics
stats = webpush_provider.get_stats()
print(f"Success Rate: {stats['success_rate'] * 100:.2f}%")
print(f"Avg Latency: {stats['avg_latency_ms']:.2f}ms")
print(f"Total Sent: {stats['total_success']}")
print(f"Total Failed: {stats['total_failed']}")
```

### View via API

```bash
curl http://localhost:8080/api/v1/providers/stats
```

---

## 🐛 Troubleshooting

### Issue: "No subscription found"
**Solution**: User must subscribe first via browser

### Issue: "VAPID keys not configured"
**Solution**: Run `python scripts/generate_vapid_keys.py`

### Issue: Service Worker not registering
**Solution**: 
- Check browser console for errors
- Ensure serving over HTTPS (or localhost)
- Clear cache and retry

### Issue: 410 Gone error
**Solution**: Subscription expired, user must re-subscribe

### Issue: Notifications not showing
**Solution**:
- Check browser notification permissions
- Verify service worker is active
- Check browser console for errors

---

## 🚀 Production Deployment

### Checklist

- [ ] Generate production VAPID keys
- [ ] Store private key in secrets manager
- [ ] Configure HTTPS with valid SSL certificate
- [ ] Set up Redis for subscription persistence
- [ ] Implement subscription cleanup (410 Gone)
- [ ] Add analytics/monitoring
- [ ] Test across multiple browsers
- [ ] Configure rate limiting
- [ ] Set up backup/recovery
- [ ] Document user opt-out process

### Redis Persistence (Optional)

Store subscriptions in Redis for persistence across restarts:

```python
# In webpush_provider.py
def add_subscription(self, user_id, subscription_data):
    subscription = WebPushSubscription(...)
    
    # Store in Redis
    redis_client.set(
        f"webpush:subscription:{user_id}",
        subscription,
        ttl=None  # No expiration
    )
    
    self.subscriptions[user_id] = subscription
```

---

## 📚 Additional Resources

- [Web Push Protocol RFC 8030](https://tools.ietf.org/html/rfc8030)
- [VAPID RFC 8292](https://tools.ietf.org/html/rfc8292)
- [MDN Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [pywebpush Library](https://github.com/web-push-libs/pywebpush)

---

## 🎯 Next Steps

1. ✅ **Test Web Push** - Use the test page to verify functionality
2. ⬜ **Add to ML Training** - Train algorithms with webpush channel data
3. ⬜ **Implement Persistence** - Store subscriptions in database/Redis
4. ⬜ **Analytics** - Track engagement rates (clicks, dismissals)
5. ⬜ **A/B Testing** - Test notification styles and timing
6. ⬜ **Production Deploy** - Follow deployment checklist above

---

**✨ Web Push is now fully integrated with your ML-powered notification system!**

The system can intelligently select Web Push as the optimal channel based on user preferences and behavior patterns learned by the Sleeping Bandit and Tug of War algorithms.
