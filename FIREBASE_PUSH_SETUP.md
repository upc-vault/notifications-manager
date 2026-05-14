# Firebase Push Notifications Setup Guide

## Overview
This system uses Firebase Cloud Messaging (FCM) to send push notifications to both **Android** and **iOS** devices.

## Prerequisites
- Firebase project (create at [Firebase Console](https://console.firebase.google.com/))
- Python `firebase-admin` package

## Step 1: Install Firebase Admin SDK

```powershell
pip install firebase-admin
```

## Step 2: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** or select existing project
3. Follow the setup wizard

## Step 3: Generate Service Account Key

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Navigate to **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Download the JSON file
5. Save it as `firebase-service-account.json` in the `config/` folder

```
notifications-manager/
└── config/
    ├── firebase-service-account.json  ← Place here
    ├── vapid_keys.json
    └── settings.py
```

## Step 4: Configure Environment Variables

Create/update `.env` file:

```env
# Firebase Push Notifications
FIREBASE_SERVICE_ACCOUNT_PATH=config/firebase-service-account.json
FIREBASE_MOCK_MODE=false
```

Set `FIREBASE_MOCK_MODE=true` to test without real FCM (uses mock provider).

## Step 5: Setup Mobile Apps

### Android Setup

1. In Firebase Console, add Android app
2. Download `google-services.json`
3. Add to your Android project (`app/` folder)
4. Add Firebase SDK to `build.gradle`:

```gradle
dependencies {
    implementation 'com.google.firebase:firebase-messaging:23.0.0'
}
```

5. Request notification permission and get device token:

```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        // Send this token to your backend
        registerDeviceToken(token)
    }
}
```

### iOS Setup

1. In Firebase Console, add iOS app
2. Download `GoogleService-Info.plist`
3. Add to your Xcode project
4. Enable Push Notifications capability
5. Get APNs key from Apple Developer Console
6. Upload APNs key to Firebase Console
7. Get device token:

```swift
UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
    if granted {
        DispatchQueue.main.async {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
}

func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceData: Data) {
    let token = deviceData.map { String(format: "%02.2hhx", $0) }.joined()
    // Send this token to your backend
    registerDeviceToken(token)
}
```

## Step 6: Test Push Notifications

### Option 1: Using the Dashboard

1. Start the server: `python src/api/main.py`
2. Go to `http://localhost:8080/dashboard`
3. Navigate to **Mobile Push** test section
4. Enter a valid FCM device token
5. Send test notification

### Option 2: Using API

```bash
curl -X POST http://localhost:8080/api/v1/notification/send \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "template_id": 1,
    "message_type": "security"
  }'
```

### Option 3: Direct API Endpoint

```bash
curl -X POST http://localhost:8080/api/v1/push/send \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "YOUR_FCM_DEVICE_TOKEN",
    "title": "Test Notification",
    "body": "This is a test push notification",
    "data": {
      "key1": "value1"
    }
  }'
```

## Notification Payload Structure

The push provider sends notifications with the following structure:

```json
{
  "notification": {
    "title": "Notification Title",
    "body": "Notification message body",
    "image": "https://example.com/image.png"
  },
  "data": {
    "notification_id": "unique_id",
    "click_action": "OPEN_APP",
    "log_id": "123",
    "custom_key": "custom_value"
  },
  "android": {
    "priority": "high",
    "notification": {
      "icon": "ic_notification",
      "color": "#0066CC",
      "sound": "default",
      "click_action": "OPEN_APP"
    }
  },
  "apns": {
    "payload": {
      "aps": {
        "alert": {
          "title": "Notification Title",
          "body": "Notification message body"
        },
        "badge": 1,
        "sound": "default"
      }
    }
  }
}
```

## Features

### ✅ Supported Features

- **Cross-platform**: Single API for Android & iOS
- **Rich notifications**: Images, custom icons, colors
- **Data payload**: Custom data with notification
- **Priority control**: High/normal priority
- **Sound & badges**: Custom sounds and badge counts
- **Click actions**: Deep linking support
- **Multicast**: Send to multiple devices at once
- **Mock mode**: Test without real devices

### 🎯 Platform-Specific

**Android:**
- Custom icon and color
- High priority delivery
- Click action handling

**iOS:**
- Badge counter
- Silent notifications
- APNs configuration
- Background updates

## Error Handling

The provider handles common errors:

- **UnregisteredError**: Device token invalid/unregistered
- **Network errors**: Automatic retry logic
- **Invalid tokens**: Fallback to mock mode
- **Missing credentials**: Automatic mock mode activation

## Monitoring & Stats

View push notification stats:

```python
from src.providers.push_provider import push_provider

stats = push_provider.get_stats()
# Returns: total_attempts, total_success, total_failed, success_rate, avg_latency_ms
```

## Troubleshooting

### Push provider using mock mode

**Symptom**: Logs show "🔧 Push provider running in mock mode"

**Solutions**:
1. Check `firebase-service-account.json` exists in `config/`
2. Verify `FIREBASE_SERVICE_ACCOUNT_PATH` in `.env`
3. Set `FIREBASE_MOCK_MODE=false` in `.env`
4. Ensure `firebase-admin` package is installed

### Device token not receiving notifications

**Solutions**:
1. Verify device token is valid (152 characters for FCM)
2. Check device has granted notification permissions
3. Ensure app is configured with Firebase
4. Verify `google-services.json` (Android) or `GoogleService-Info.plist` (iOS) is correct
5. Check Firebase Console for delivery status

### iOS notifications not working

**Solutions**:
1. Verify APNs certificate/key uploaded to Firebase
2. Check iOS app has Push Notifications capability enabled
3. Ensure proper entitlements in Xcode
4. Test with Apple Push Notification service directly

## Advanced: Multicast Messages

Send to multiple devices efficiently:

```python
from src.providers.push_provider import push_provider

result = push_provider.send_multicast(
    device_tokens=["token1", "token2", "token3"],
    title="Important Update",
    body="New feature available!",
    data={"feature": "chat", "version": "2.0"}
)

print(f"Success: {result['success_count']}, Failed: {result['failure_count']}")
```

## Security Best Practices

1. **Never commit** `firebase-service-account.json` to version control
2. Add to `.gitignore`:
   ```
   config/firebase-service-account.json
   ```
3. Use environment variables for sensitive paths
4. Rotate service account keys periodically
5. Limit service account permissions to Cloud Messaging only

## Resources

- [Firebase Console](https://console.firebase.google.com/)
- [FCM Documentation](https://firebase.google.com/docs/cloud-messaging)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Android Integration](https://firebase.google.com/docs/cloud-messaging/android/client)
- [iOS Integration](https://firebase.google.com/docs/cloud-messaging/ios/client)

## Support

For issues or questions:
1. Check Firebase Console logs
2. Review system logs: `notifications.log`
3. Enable debug mode: `LOG_LEVEL=DEBUG` in `.env`
