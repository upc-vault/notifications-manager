# Firebase Push Notifications Setup Guide

## 📱 Overview
This comprehensive guide walks you through setting up Firebase Cloud Messaging (FCM) for push notifications on both **Android** and **iOS** devices.

## 🎯 What You'll Need
- Google account (for Firebase Console)
- Apple Developer Account ($99/year - for iOS only)
- Python `firebase-admin` package
- Android Studio (for Android development)
- Xcode 15+ (for iOS development on macOS)

---

## 📦 Step 1: Install Firebase Admin SDK

In your backend project, install the Firebase Admin SDK:

```powershell
pip install firebase-admin
```

Or if using poetry:
```powershell
poetry add firebase-admin
```

---

## 🔥 Step 2: Create Firebase Project

### 2.1 Create New Project

1. Navigate to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"** (or select existing project)
3. Enter project name (e.g., "Omega Bank Notifications")
4. **Optional:** Enable Google Analytics (recommended for tracking)
5. Click **"Create project"** and wait for setup to complete
6. Click **"Continue"** when ready

### 2.2 Upgrade to Blaze Plan (Optional but Recommended)

For production use, upgrade to the **Blaze (Pay as you go)** plan:
- Navigate to Project Settings → Usage and billing
- Click "Modify plan"
- Select "Blaze" plan
- **Note:** Free tier includes 10GB FCM bandwidth/month (sufficient for most apps)

---

## 🔑 Step 3: Generate Service Account Key

This key allows your backend to authenticate with Firebase.

1. In Firebase Console, click the **gear icon** (⚙️) → **Project Settings**
2. Navigate to the **"Service accounts"** tab
3. Click **"Generate new private key"** button
4. In the popup, click **"Generate key"**
5. A JSON file will download automatically (e.g., `omega-bank-firebase-adminsdk-xxxxx.json`)
6. **IMPORTANT:** Keep this file secure - it grants full access to your Firebase project

### 3.1 Save the File

Rename and move the file to your project:

```
notifications-manager/
└── config/
    ├── firebase-service-account.json  ← Rename and place here
    ├── vapid_keys.json
    └── settings.py
```

### 3.2 Secure the File

Add to `.gitignore` to prevent committing sensitive credentials:

```gitignore
# Firebase credentials
config/firebase-service-account.json
config/*.json
!config/vapid_keys.json
```

---

## ⚙️ Step 4: Configure Environment Variables

Create or update your `.env` file in the project root:

```env
# Firebase Push Notifications
FIREBASE_SERVICE_ACCOUNT_PATH=config/firebase-service-account.json
FIREBASE_MOCK_MODE=false
```

**Environment Variables:**
- `FIREBASE_SERVICE_ACCOUNT_PATH`: Path to your Firebase service account JSON file
- `FIREBASE_MOCK_MODE`: Set to `true` for testing without real FCM (useful for development)

---

## 🤖 Step 5: Android Setup (Detailed)

### 5.1 Add Android App to Firebase

1. In Firebase Console, click **"Add app"** or the Android icon
2. **Android package name:** Enter your app's package name (e.g., `com.omega.bank`)
   - Find this in `app/build.gradle` → `applicationId`
3. **App nickname (optional):** "Omega Bank Android"
4. **Debug signing certificate SHA-1 (optional):** Can be added later
5. Click **"Register app"**

### 5.2 Download Configuration File

1. Download the `google-services.json` file
2. Place it in your Android project:
   ```
   omega-bank-android/
   └── app/
       ├── google-services.json  ← Place here
       ├── build.gradle
       └── src/
   ```

### 5.3 Add Firebase SDK to Project

**Project-level `build.gradle`:**
```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

**App-level `app/build.gradle`:**
```gradle
plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
    id 'com.google.gms.google-services'  // Add this line
}

dependencies {
    // Firebase BoM (Bill of Materials)
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    
    // Firebase Cloud Messaging
    implementation 'com.google.firebase:firebase-messaging-ktx'
    
    // Optional: Firebase Analytics
    implementation 'com.google.firebase:firebase-analytics-ktx'
}
```

### 5.4 Add Permissions to AndroidManifest.xml

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    
    <application>
        <!-- Your activities here -->
        
        <!-- Firebase Messaging Service -->
        <service
            android:name=".fcm.OmegaFirebaseMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>
    </application>
</manifest>
```

### 5.5 Request Notification Permission (Android 13+)

For Android 13 (API 33) and higher, you must request runtime permission:

```kotlin
// In your Activity
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
    if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) 
        != PackageManager.PERMISSION_GRANTED) {
        ActivityCompat.requestPermissions(
            this,
            arrayOf(Manifest.permission.POST_NOTIFICATIONS),
            REQUEST_CODE_NOTIFICATION_PERMISSION
        )
    }
}
```

### 5.6 Get FCM Token

```kotlin
import com.google.firebase.messaging.FirebaseMessaging

FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (!task.isSuccessful) {
        Log.w(TAG, "Fetching FCM registration token failed", task.exception)
        return@addOnCompleteListener
    }

    // Get FCM token
    val token = task.result
    Log.d(TAG, "FCM Token: $token")
    
    // Send token to your backend
    registerTokenWithBackend(token)
}
```

### 5.7 Test on Android Emulator

**Important:** Use an emulator with Google Play Services:
1. In Android Studio → AVD Manager
2. Create device with **"Play Store"** icon (not just "Google APIs")
3. Run the app and check Logcat for "FCM Token: ..."

---

## 🍎 Step 6: iOS Setup (Detailed)

### 6.1 Prerequisites for iOS

- **macOS** computer with Xcode 15+
- **Apple Developer Account** ($99/year enrollment)
- **App ID** registered in Apple Developer Portal

### 6.2 Create App ID in Apple Developer Portal

1. Go to [Apple Developer Portal](https://developer.apple.com/account)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Click **Identifiers** → **+ (Add button)**
4. Select **App IDs** → Click **Continue**
5. Select **App** → Click **Continue**
6. Enter **Description:** "Omega Bank"
7. Enter **Bundle ID:** `com.omega.bank` (must match Xcode project)
8. Scroll to **Capabilities** and check ☑️ **Push Notifications**
9. Click **Continue** → **Register**

### 6.3 Generate APNs Authentication Key (Recommended Method)

**Why APNs Key?** It's easier than certificates and works for both development and production.

#### Step-by-step APNs Key Generation:

1. In Apple Developer Portal, navigate to **Certificates, Identifiers & Profiles**
2. Click **Keys** (in the left sidebar)
3. Click the **+ (Add button)** at the top
4. Enter **Key Name:** "Omega Bank Push Notifications Key"
5. Check the checkbox ☑️ **Apple Push Notifications service (APNs)**
6. Click **Continue**
7. Review and click **Register**
8. **Download the `.p8` file** immediately
   - ⚠️ **You can only download this once!** Save it securely
   - Filename format: `AuthKey_XXXXXXXXXX.p8`
9. **Note the Key ID** (10 characters, e.g., `AB12CD34EF`)
10. **Note your Team ID** (found in top-right corner or Account page)

**File structure after download:**
```
Downloads/
└── AuthKey_AB12CD34EF.p8  ← Keep this file safe!
```

### 6.4 Upload APNs Key to Firebase

1. In Firebase Console, go to **Project Settings** (⚙️ gear icon)
2. Navigate to **Cloud Messaging** tab
3. Scroll to **Apple app configuration** section
4. Click **Upload** under "APNs Authentication Key"
5. Select your downloaded `.p8` file
6. Enter **Key ID** (the 10-character ID from step 9 above)
7. Enter **Team ID** (your Apple Developer Team ID)
8. Click **Upload**

**You should see:** ✅ "APNs Authentication Key uploaded successfully"

### 6.5 Add iOS App to Firebase

1. In Firebase Console, click **"Add app"** or the iOS icon (🍎)
2. **iOS bundle ID:** `com.omega.bank` (must match your App ID)
3. **App nickname (optional):** "Omega Bank iOS"
4. **App Store ID (optional):** Leave empty for now
5. Click **"Register app"**

### 6.6 Download Configuration File

1. Download the `GoogleService-Info.plist` file
2. In Xcode, drag this file into your project:
   - Select the project root in Project Navigator
   - Drag `GoogleService-Info.plist` into the project
   - ✅ Check "Copy items if needed"
   - ✅ Select your app target
   - Click **Finish**

### 6.7 Install Firebase SDK via CocoaPods

**Install CocoaPods** (if not already installed):
```bash
sudo gem install cocoapods
```

**Create `Podfile` in your iOS project root:**
```ruby
platform :ios, '15.0'

target 'OmegaBank' do
  use_frameworks!
  
  # Firebase
  pod 'Firebase/Messaging'
  pod 'Firebase/Analytics'
end
```

**Install pods:**
```bash
cd OmegaBank-iOS
pod install
```

**Important:** From now on, open `OmegaBank.xcworkspace` (not `.xcodeproj`)

### 6.8 Enable Push Notifications Capability in Xcode

1. Open your project in Xcode
2. Select your **project** in Project Navigator
3. Select your **app target**
4. Navigate to **Signing & Capabilities** tab
5. Click **+ Capability**
6. Search for and add **Push Notifications**
7. You should see: ✅ "Push Notifications" capability added

### 6.9 Enable Background Modes

1. In the same **Signing & Capabilities** tab
2. Click **+ Capability**
3. Add **Background Modes**
4. Check ☑️ **Remote notifications**

### 6.10 Initialize Firebase in Your App

**In `AppDelegate.swift` or your App struct:**

```swift
import UIKit
import Firebase
import FirebaseMessaging
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate, 
                   UNUserNotificationCenterDelegate, MessagingDelegate {
    
    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Initialize Firebase
        FirebaseApp.configure()
        
        // Set delegates
        UNUserNotificationCenter.current().delegate = self
        Messaging.messaging().delegate = self
        
        // Request notification permission
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            if granted {
                print("✅ Notification permission granted")
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            } else {
                print("❌ Notification permission denied")
            }
        }
        
        return true
    }
    
    // APNs token received
    func application(_ application: UIApplication, 
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        // Pass token to Firebase
        Messaging.messaging().apnsToken = deviceToken
        
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("📱 APNs Token: \(token)")
    }
    
    // FCM token received
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let token = fcmToken else { return }
        print("🔥 FCM Token: \(token)")
        
        // Save token
        UserDefaults.standard.set(token, forKey: "fcm_token")
        
        // Register with your backend
        registerTokenWithBackend(token: token)
    }
    
    // Handle foreground notifications
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                                willPresent notification: UNNotification, 
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound, .badge])
    }
    
    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                                didReceive response: UNNotificationResponse, 
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo
        print("📬 Notification tapped: \(userInfo)")
        completionHandler()
    }
}
```

### 6.11 Test on iOS Simulator (Limited)

**Note:** iOS Simulator **cannot receive real push notifications**. You must test on a **physical device**.

**To test on a physical device:**
1. Connect iPhone/iPad via USB
2. In Xcode, select your device from the device menu
3. Click **Run** (▶️)
4. Check Xcode console for "FCM Token: ..."

---

## Step 6: Register Device Token with Backend

After obtaining the FCM device token from your mobile app, register it with the notification manager backend.

### API Endpoint: Register Device Token

**POST** `/api/v1/push/register`

**Headers:**
```
Authorization: Bearer <jwt_access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "device_token": "fcm_device_token_from_firebase",
    "platform": "android",
    "device_info": "Samsung Galaxy S23, Android 13",
    "app_version": "1.0.5"
}
```

**Response:**
```json
{
    "status": "registered",
    "message": "FCM device token registered for user john_doe",
    "username": "john_doe",
    "platform": "android"
}
```

### Example: Android Integration

```kotlin
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import com.google.firebase.messaging.FirebaseMessaging

fun registerWithBackend(accessToken: String) {
    FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
        if (task.isSuccessful) {
            val deviceToken = task.result
            
            val json = JSONObject().apply {
                put("device_token", deviceToken)
                put("platform", "android")
                put("device_info", "${Build.MODEL}, Android ${Build.VERSION.RELEASE}")
                put("app_version", BuildConfig.VERSION_NAME)
            }
            
            val client = OkHttpClient()
            val request = Request.Builder()
                .url("http://localhost:8080/api/v1/push/register")
                .addHeader("Authorization", "Bearer $accessToken")
                .post(json.toString().toRequestBody("application/json".toMediaType()))
                .build()
            
            client.newCall(request).enqueue(object : Callback {
                override fun onResponse(call: Call, response: Response) {
                    if (response.isSuccessful) {
                        println("✓ Device registered for push notifications")
                    }
                }
                
                override fun onFailure(call: Call, e: IOException) {
                    println("✗ Registration failed: ${e.message}")
                }
            })
        }
    }
}
```

### Example: iOS Integration

```swift
import Foundation

func registerWithBackend(accessToken: String, deviceToken: String) {
    let url = URL(string: "http://localhost:8080/api/v1/push/register")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body: [String: Any] = [
        "device_token": deviceToken,
        "platform": "ios",
        "device_info": "\(UIDevice.current.model), iOS \(UIDevice.current.systemVersion)",
        "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
    ]
    
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            print("✗ Registration failed: \(error.localizedDescription)")
            return
        }
        
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            print("✓ Device registered for push notifications")
        }
    }.resume()
}
```

## Step 7: Additional API Endpoints

### Get User's Device Tokens

**GET** `/api/v1/push/tokens`

**Headers:**
```
Authorization: Bearer <jwt_access_token>
```

**Response:**
```json
{
    "total_tokens": 2,
    "tokens": [
        {
            "id": 1,
            "platform": "android",
            "device_info": "Samsung Galaxy S23, Android 13",
            "is_active": true,
            "created_at": "2026-05-14T10:30:00",
            "notifications_sent": 45,
            "notifications_failed": 2
        },
        {
            "id": 2,
            "platform": "ios",
            "device_info": "iPhone 14 Pro, iOS 17.0",
            "is_active": true,
            "created_at": "2026-05-13T15:20:00",
            "notifications_sent": 32,
            "notifications_failed": 0
        }
    ]
}
```

### Unregister Device Token

**POST** `/api/v1/push/unregister`

**Headers:**
```
Authorization: Bearer <jwt_access_token>
Content-Type: application/json
```

**Request Body (optional):**
```json
{
    "device_token": "fcm_token_to_remove"
}
```

If `device_token` is omitted, all user's tokens will be deactivated.

**Response:**
```json
{
    "status": "unregistered",
    "message": "FCM device token(s) removed for user john_doe",
    "username": "john_doe"
}
```

## 🧪 Step 8: Test Push Notifications

### 8.1 Test from Firebase Console (Quick Test)

1. In Firebase Console, go to **Cloud Messaging**
2. Click **"Send your first message"** or **"New notification"**
3. Enter **Notification title** and **text**
4. Click **"Send test message"**
5. Enter your **FCM token** (from device logs)
6. Click **"Test"**
7. Check your device for the notification

### 8.2 Test from Your Backend

Start your backend server:
```powershell
python src/api/main.py
```

**Create a test transfer** (triggers notification via ML system):
```bash
curl -X POST http://localhost:8080/api/v1/transfers \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_username": "test_user",
    "amount": 25.00,
    "description": "Test payment"
  }'
```

The receiver should get a push notification: **"💰 Money Received! You received $25.00 from..."**

### 8.3 Troubleshooting

#### Android Issues

**Problem:** "FirebaseApp initialization unsuccessful"
- ✅ **Solution:** Ensure `google-services.json` is in `app/` directory
- ✅ Check that `com.google.gms.google-services` plugin is applied

**Problem:** "No FCM token received"
- ✅ **Solution:** Use emulator with Google Play Services (has Play Store icon)
- ✅ Check internet connection
- ✅ Wait 30 seconds after app launch

**Problem:** "Notification permission denied"
- ✅ **Solution:** On Android 13+, request `POST_NOTIFICATIONS` permission
- ✅ Go to Settings → Apps → Your App → Notifications → Allow

#### iOS Issues

**Problem:** "APNs token not set"
- ✅ **Solution:** Ensure `Messaging.messaging().apnsToken = deviceToken` is called
- ✅ Enable Push Notifications capability in Xcode
- ✅ Check that APNs key is uploaded to Firebase

**Problem:** "No FCM token received"
- ✅ **Solution:** Must test on **physical device** (simulator doesn't support push)
- ✅ Ensure device has internet connection
- ✅ Check that `FirebaseApp.configure()` is called

**Problem:** "Error Domain=com.firebase.iid Code=1001"
- ✅ **Solution:** APNs key not properly configured
- ✅ Verify Key ID and Team ID in Firebase Console
- ✅ Re-upload `.p8` file if necessary

**Problem:** "Notifications not showing in foreground"
- ✅ **Solution:** Implement `userNotificationCenter(_:willPresent:)` delegate
- ✅ Return `[.banner, .sound, .badge]` to show notification

### 8.4 Verify Token Registration

Check if device token is registered in your backend:

```bash
# Get all registered tokens
curl http://localhost:8080/api/v1/push/tokens/all
```

You should see your device token listed with platform (android/ios).

---

## 🔐 Step 9: Production Considerations

### 9.1 Security

- ✅ Never commit `firebase-service-account.json` to version control
- ✅ Use environment variables for sensitive configuration
- ✅ Rotate service account keys periodically
- ✅ Use `.gitignore` to exclude credentials

### 9.2 APNs Environment

- **Development:** Used automatically when testing from Xcode
- **Production:** Used when app is downloaded from App Store
- **Firebase handles this automatically** when using APNs auth key

### 9.3 Rate Limiting

Firebase Cloud Messaging has rate limits:
- **FCM HTTP v1 API:** 600,000 requests/minute
- **Burst:** Up to 1,000 messages/second per device

For high-volume apps, implement:
- Message batching using `send_multicast()`
- Queue-based sending with throttling
- Retry logic with exponential backoff

---

## 📚 Additional Resources

### Official Documentation
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [FCM on Android](https://firebase.google.com/docs/cloud-messaging/android/client)
- [FCM on iOS](https://firebase.google.com/docs/cloud-messaging/ios/client)
- [Apple Push Notification Service](https://developer.apple.com/documentation/usernotifications)

### Useful Tools
- [FCM API Reference](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)
- [Firebase Console](https://console.firebase.google.com/)
- [Apple Developer Portal](https://developer.apple.com/account)

### Testing Tools
- **Postman:** Test FCM HTTP v1 API directly
- **Firebase Test Lab:** Automated testing on real devices
- **Pusher for iOS:** Test APNs connectivity (macOS app)

---

## 🎯 Quick Reference

### Android
```bash
# Package name
com.omega.bank

# File locations
app/google-services.json
app/src/main/java/.../OmegaFirebaseMessagingService.kt

# Test command
adb logcat | grep "FCM Token"
```

### iOS
```bash
# Bundle ID
com.omega.bank

# File locations
OmegaBank/GoogleService-Info.plist
OmegaBank/AppDelegate.swift

# Test on device (required)
# Check Xcode console for "FCM Token:"
```

### Backend
```bash
# Environment
FIREBASE_SERVICE_ACCOUNT_PATH=config/firebase-service-account.json

# Test endpoint
POST /api/v1/push/register
GET /api/v1/push/tokens
```

---

## ✅ Checklist

### Backend Setup
- [ ] Firebase project created
- [ ] Service account JSON downloaded and saved
- [ ] `firebase-admin` package installed
- [ ] Environment variables configured
- [ ] Backend server starts without errors

### Android Setup
- [ ] Android app added to Firebase
- [ ] `google-services.json` downloaded and placed in `app/`
- [ ] Firebase SDK added to Gradle files
- [ ] Permissions added to AndroidManifest.xml
- [ ] Notification permission requested (Android 13+)
- [ ] FCM service implemented
- [ ] Token registration with backend working
- [ ] Test notification received on device

### iOS Setup
- [ ] App ID created in Apple Developer Portal
- [ ] Push Notifications enabled for App ID
- [ ] APNs authentication key (.p8) generated and downloaded
- [ ] APNs key uploaded to Firebase Console
- [ ] iOS app added to Firebase
- [ ] `GoogleService-Info.plist` downloaded and added to Xcode
- [ ] Firebase SDK installed via CocoaPods
- [ ] Push Notifications capability enabled in Xcode
- [ ] Background Modes (Remote notifications) enabled
- [ ] Firebase initialized in AppDelegate
- [ ] Token registration with backend working
- [ ] Test notification received on physical device

---

## 🆘 Getting Help

If you encounter issues:

1. **Check Firebase Console** → Cloud Messaging → View logs
2. **Check device logs:**
   - Android: `adb logcat | grep Firebase`
   - iOS: Xcode Console (⌘⇧C)
3. **Verify configuration:**
   - Service account permissions
   - APNs key upload (iOS)
   - App bundle ID matches Firebase
4. **Test with Firebase Console notification composer first**
5. **Check backend logs** for registration errors

---

**Congratulations!** 🎉 Your push notification system is now fully configured and ready for production use.

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
