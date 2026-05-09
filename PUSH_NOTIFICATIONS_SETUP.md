# Push Notifications Setup Guide

## Overview
The Omega Notifications Manager now supports **Firebase Cloud Messaging (FCM)** for sending push notifications to both iOS and Android devices.

## Demo Mode
Without Firebase configuration, the system runs in **demo mode** - all functionality works but notifications are simulated. Perfect for testing the UI and API flow!

---

## Firebase Setup (For Real Notifications)

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add project" or select existing project
3. Follow the setup wizard
4. Enable Google Analytics (optional)

### 2. Get Service Account Credentials

1. In Firebase Console, click the gear icon → **Project Settings**
2. Navigate to **Service Accounts** tab
3. Click **Generate New Private Key**
4. Download the JSON file
5. Save it as `config/firebase-credentials.json` in this project
6. Restart the API server

### 3. Add iOS App to Firebase

1. In Firebase Console → Project Overview → Add iOS app
2. Enter your iOS bundle ID (e.g., `com.yourcompany.omega`)
3. Download `GoogleService-Info.plist`
4. Add the file to your Xcode project root

### 4. Add Android App to Firebase (Optional)

1. In Firebase Console → Project Overview → Add Android app
2. Enter your Android package name
3. Download `google-services.json`
4. Place it in your Android app's `app/` directory

### 5. Upload APNs Certificate (iOS Only)

1. Generate an APNs Authentication Key in [Apple Developer Portal](https://developer.apple.com/account/)
   - Go to Certificates, Identifiers & Profiles
   - Keys → Create Key → Enable Apple Push Notifications service (APNs)
   - Download the `.p8` file (save it securely!)
   
2. Upload to Firebase:
   - Firebase Console → Project Settings → Cloud Messaging
   - Under Apple app configuration → APNs Authentication Key
   - Upload your `.p8` file
   - Enter Key ID and Team ID

---

## iOS Client Setup

### 1. Install Firebase SDK

Add to your `Podfile`:
```ruby
pod 'Firebase/Messaging'
```

Run:
```bash
pod install
```

### 2. Configure AppDelegate

```swift
import UIKit
import Firebase
import FirebaseMessaging
import UserNotifications

@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate {
    
    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Initialize Firebase
        FirebaseApp.configure()
        
        // Set messaging delegate
        Messaging.messaging().delegate = self
        
        // Set notification delegate
        UNUserNotificationCenter.current().delegate = self
        
        // Request permission
        let authOptions: UNAuthorizationOptions = [.alert, .badge, .sound]
        UNUserNotificationCenter.current().requestAuthorization(options: authOptions) { granted, _ in
            print("Permission granted: \(granted)")
        }
        
        application.registerForRemoteNotifications()
        
        return true
    }
    
    func application(_ application: UIApplication, 
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
    }
}

extension AppDelegate: MessagingDelegate {
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let fcmToken = fcmToken else { return }
        
        print("📱 FCM Token: \(fcmToken)")
        
        // TODO: Send this token to your server for testing
        // You'll paste this token in the web interface
        
        // Save to UserDefaults for easy access
        UserDefaults.standard.set(fcmToken, forKey: "fcmToken")
    }
}

extension AppDelegate: UNUserNotificationCenterDelegate {
    // Handle notification when app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([[.banner, .sound]])
    }
    
    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo
        print("Notification tapped: \(userInfo)")
        completionHandler()
    }
}
```

### 3. Enable Push Notifications in Xcode

1. Select your project target
2. Go to **Signing & Capabilities**
3. Click **+ Capability**
4. Add **Push Notifications**
5. Add **Background Modes** → Enable "Remote notifications"

### 4. Get Your FCM Token

Add a button in your app to copy the token:

```swift
import UIKit

class ViewController: UIViewController {
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Get FCM token
        if let token = UserDefaults.standard.string(forKey: "fcmToken") {
            print("Your FCM Token:")
            print(token)
            
            // Copy to clipboard
            UIPasteboard.general.string = token
            
            // Show alert
            let alert = UIAlertController(
                title: "FCM Token Copied!",
                message: "Paste this token in the web interface to test push notifications.\n\nToken: \(token)",
                preferredStyle: .alert
            )
            alert.addAction(UIAlertAction(title: "OK", style: .default))
            present(alert, animated: true)
        }
    }
}
```

---

## Android Client Setup (Optional)

### 1. Add Firebase SDK

In `build.gradle` (project level):
```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

In `build.gradle` (app level):
```gradle
plugins {
    id 'com.google.gms.google-services'
}

dependencies {
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    implementation 'com.google.firebase:firebase-messaging'
}
```

### 2. Create FirebaseMessagingService

```kotlin
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import android.util.Log

class MyFirebaseMessagingService : FirebaseMessagingService() {
    
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        Log.d(TAG, "From: ${remoteMessage.from}")
        
        remoteMessage.notification?.let {
            Log.d(TAG, "Notification Title: ${it.title}")
            Log.d(TAG, "Notification Body: ${it.body}")
            // Show notification
        }
        
        remoteMessage.data.isNotEmpty().let {
            Log.d(TAG, "Data payload: ${remoteMessage.data}")
        }
    }
    
    override fun onNewToken(token: String) {
        Log.d(TAG, "FCM Token: $token")
        // Send token to your server
    }
    
    companion object {
        private const val TAG = "FCM"
    }
}
```

### 3. Update AndroidManifest.xml

```xml
<service
    android:name=".MyFirebaseMessagingService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

### 4. Get FCM Token

In your MainActivity:
```kotlin
import com.google.firebase.messaging.FirebaseMessaging

FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        Log.d("FCM", "Token: $token")
        // Copy to clipboard or display
    }
}
```

---

## Testing Push Notifications

### 1. Start the API Server

```bash
.venv\Scripts\python.exe scripts\start_api.py
```

You'll see:
- ✅ Service ready (Firebase configured)
- ⚠️ Demo mode (Firebase not configured - simulated notifications)

### 2. Open Test Page

Navigate to: http://localhost:8080/test/push

### 3. Get Your Device Token

**iOS:** Run your app, check console or alert for FCM token
**Android:** Check Logcat for FCM token

### 4. Send Test Notification

1. Paste your FCM token in the web form
2. Customize title, body, badge, sound
3. Add custom data (optional JSON)
4. Click "Send Test Notification"

### 5. Check Your Device

- iOS: Notification appears in banner/lock screen
- Android: Notification appears in notification tray

---

## Troubleshooting

### iOS

**Problem:** Not receiving notifications
- ✅ Check Push Notifications capability enabled in Xcode
- ✅ Verify APNs certificate uploaded to Firebase
- ✅ Ensure device is registered for remote notifications
- ✅ Check bundle ID matches Firebase config
- ✅ Test on real device (not simulator for remote notifications)

**Problem:** Token not generated
- ✅ Call `application.registerForRemoteNotifications()`
- ✅ Ensure `FirebaseApp.configure()` is called
- ✅ Check console for errors

### Android

**Problem:** Not receiving notifications
- ✅ Verify `google-services.json` is in `app/` directory
- ✅ Check package name matches Firebase config
- ✅ Ensure FirebaseMessagingService is registered in manifest

### Server

**Problem:** Demo mode even with credentials file
- ✅ Check file is named exactly `firebase-credentials.json`
- ✅ Verify file is in `config/` directory
- ✅ Check JSON format is valid
- ✅ Restart API server

---

## API Endpoints

### Send Test Notification
```http
POST /api/v1/push/send-test
Content-Type: application/json

{
  "token": "device-fcm-token",
  "title": "Test Notification",
  "body": "This is a test",
  "badge": 1,
  "sound": "default",
  "data": {
    "key": "value"
  }
}
```

### Send to Multiple Devices
```http
POST /api/v1/push/send-multicast
Content-Type: application/json

{
  "tokens": ["token1", "token2", "token3"],
  "title": "Broadcast",
  "body": "Message to all devices",
  "data": {}
}
```

### Subscribe to Topic
```http
POST /api/v1/push/subscribe-topic
Content-Type: application/json

{
  "tokens": ["token1", "token2"],
  "topic": "news"
}
```

### Check Status
```http
GET /api/v1/push/status
```

---

## Production Deployment

### Security Best Practices

1. **Never commit credentials**
   - Add `config/firebase-credentials.json` to `.gitignore`
   - Use environment variables in production

2. **Use environment variables**
   ```python
   FIREBASE_CREDENTIALS_PATH=/secure/path/firebase-credentials.json
   ```

3. **Secure token storage**
   - Store FCM tokens encrypted in database
   - Associate tokens with user accounts
   - Remove invalid/expired tokens

4. **Rate limiting**
   - Implement rate limits on send endpoints
   - Use Firebase batch sending for efficiency

5. **Monitoring**
   - Log all notification sends
   - Track delivery rates
   - Monitor for errors

---

## Next Steps

✅ Set up Firebase project  
✅ Configure iOS app with FCM  
✅ Get device token  
✅ Test notifications via web interface  
⏳ Integrate with ML recommendation system  
⏳ Add notification templates for push  
⏳ Implement user segmentation  

---

## Support

- Firebase Documentation: https://firebase.google.com/docs/cloud-messaging
- iOS Setup Guide: https://firebase.google.com/docs/cloud-messaging/ios/client
- Android Setup Guide: https://firebase.google.com/docs/cloud-messaging/android/client

---

**Happy Pushing! 📱✨**
