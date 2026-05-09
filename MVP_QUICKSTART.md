# WebPush MVP - Quick Start Guide

## 🚀 Start the MVP

### Step 1: Start the API Server
```powershell
python scripts/start_api.py
```

### Step 2: Open the Demo Page
Open your browser and navigate to:
```
http://localhost:8080/
```

### Step 3: Subscribe to Notifications
1. Click "📬 Subscribe to Notifications"
2. Allow notifications when your browser prompts
3. You should see "✅ Successfully subscribed to notifications!"

### Step 4: Send a Test Notification
Click "🧪 Send Test Notification" to receive a test browser notification

## 📝 What You'll See

- **Browser notification** will appear (even when tab is closed)
- **Notification list** on the page will update
- Notifications work on desktop and mobile browsers

## 🔧 Technical Details

- **VAPID Keys**: Generated in [.env](.env) and [config/vapid_keys.json](config/vapid_keys.json)
- **Service Worker**: [static/sw.js](static/sw.js) handles push events
- **Web Page**: [static/index.html](static/index.html) 
- **API Endpoints**:
  - `GET /api/v1/webpush/vapid-public-key` - Get public key
  - `POST /api/v1/webpush/subscribe` - Subscribe user
  - `POST /api/v1/webpush/send-test` - Send test notification
  - `GET /api/v1/webpush/stats` - View statistics

## 🌐 Browser Support

- ✅ Chrome/Edge (best support)
- ✅ Firefox
- ✅ Safari 16+ (requires user action)
- ✅ Opera

## 🔗 Integrate with ML System

To send notifications using ML-selected templates:

```powershell
irm http://localhost:8080/api/v1/notifications -Method POST -ContentType "application/json" -Body '{"user_id":"user_abc123","notification_type":"transaction_alert","message":"Transaction of $500 detected","user_segment":"premium","time_of_day":"morning"}'
```

Then start the ESB to deliver via WebPush:
```powershell
python scripts/start_esb.py
```

## 📊 View Statistics

```powershell
irm http://localhost:8080/api/v1/webpush/stats
```

## ⚡ Quick Test Commands

```powershell
# Health check
irm http://localhost:8080/health

# Subscribe (from JavaScript)
# See index.html for full implementation

# Send test notification
irm http://localhost:8080/api/v1/webpush/send-test -Method POST -ContentType "application/json" -Body '{"user_id":"user_abc123"}'

# View stats
irm http://localhost:8080/api/v1/webpush/stats
```

## 🎯 MVP Complete!

You now have a working WebPush notification system that can:
- Subscribe users from a web page
- Send browser notifications
- Work even when browser tab is closed
- Integrate with the ML notification system
