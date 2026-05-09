# Android App Setup Guide - Omega Push Notifications Test

Complete guide to set up Android push notifications with Firebase Cloud Messaging (FCM).

## ✅ Good News: 100% FREE!

Unlike iOS, Android push notifications are **completely free**:
- ❌ No developer subscription required
- ❌ No Play Store fee needed for testing
- ✅ Just need Firebase (free tier is generous)
- ✅ Can test on any Android device

## Prerequisites

- **Android Studio** installed (download from https://developer.android.com/studio)
- **Android phone** (API 24+, Android 7.0+)
- **Firebase project** (same one you created for iOS)

---

## Step 1: Add Android App to Firebase (5 minutes)

### 1.1 Go to Firebase Console
1. Open https://console.firebase.google.com
2. Select your project (e.g., `omega-notifications`)

### 1.2 Add Android App
1. Click "Add app" → Select **Android icon**
2. **Android package name**: `com.omega.pushtest`
   - ⚠️ MUST match exactly!
3. **App nickname** (optional): `Omega Push Test`
4. **Debug signing certificate** (optional): Leave blank for now
5. Click "Register app"

### 1.3 Download google-services.json
1. Click "Download google-services.json"
2. Save the file - you'll add it to Android Studio later
3. Click "Next" → "Next" → "Continue to console"

---

## Step 2: Create Android Studio Project (10 minutes)

### 2.1 Open Android Studio
- Launch Android Studio
- Click "New Project"

### 2.2 Project Settings
1. Select **"Empty Activity"** template
2. Click "Next"

### 2.3 Configure Project
- **Name**: `Omega Push Test`
- **Package name**: `com.omega.pushtest` (⚠️ MUST match Firebase!)
- **Save location**: `D:\programming\upc-pi2\notifications-manager\android-app`
- **Language**: Kotlin
- **Minimum SDK**: API 24 (Android 7.0)
- Click "Finish"

### 2.4 Wait for Gradle Build
- Android Studio will create project and sync
- Wait for "BUILD SUCCESSFUL" message

---

## Step 3: Add google-services.json

### 3.1 Copy File
1. In Android Studio, switch to **"Project"** view (top-left dropdown)
2. Find the `app/` folder
3. Drag your downloaded `google-services.json` into `app/` folder
4. Choose "Copy" when prompted

### 3.2 Verify Location
File should be at: `app/google-services.json`
- ✅ Correct: `app/google-services.json`
- ❌ Wrong: `app/src/google-services.json`

---

## Step 4: Copy Project Files

### 4.1 Replace build.gradle Files

**Top-level build.gradle** (`project/build.gradle`):
1. Open from `android-app/build.gradle`
2. Copy entire content
3. Paste into your project's top-level `build.gradle`

**App-level build.gradle** (`app/build.gradle`):
1. Open from `android-app/app/build.gradle`
2. Copy entire content
3. Paste into your project's `app/build.gradle`

### 4.2 Replace AndroidManifest.xml
1. Navigate to `app/src/main/AndroidManifest.xml`
2. Replace entire content with `android-app/app/src/main/AndroidManifest.xml`

### 4.3 Copy Kotlin Source Files

Copy these files to `app/src/main/java/com/omega/pushtest/`:
- `MainActivity.kt`
- `MyFirebaseMessagingService.kt`

In Android Studio:
1. Right-click on `java/com.omega.pushtest` folder
2. New → Kotlin Class/File
3. Paste the code for each file

### 4.4 Copy Resource Files

Copy these XML files:

**Layout:**
- `app/src/main/res/layout/activity_main.xml`

**Values:**
- `app/src/main/res/values/colors.xml`
- `app/src/main/res/values/strings.xml`
- `app/src/main/res/values/themes.xml`

**Drawable:**
- `app/src/main/res/drawable/ic_notification.xml`

### 4.5 Sync Gradle
1. Click "Sync Now" banner at top
2. Or: File → Sync Project with Gradle Files
3. Wait for sync to complete

---

## Step 5: Build and Run (5 minutes)

### 5.1 Connect Android Phone

**Enable Developer Options:**
1. Go to Settings → About Phone
2. Tap "Build Number" 7 times
3. Go back → Developer Options
4. Enable "USB Debugging"

**Connect via USB:**
1. Connect phone to computer via USB cable
2. On phone, tap "Allow USB debugging" when prompted

### 5.2 Select Device
1. In Android Studio, click device dropdown (top toolbar)
2. Select your Android phone

### 5.3 Run App
1. Click green Play button (▶️) or press Shift+F10
2. Wait for app to build and install
3. App should open automatically on your phone

### 5.4 Grant Permissions
- When app opens, grant notification permission
- On Android 13+, popup will ask for permission
- On older Android, permissions granted automatically

---

## Step 6: Get FCM Token

### 6.1 Check App Screen
- App displays "Omega Push Notifications"
- Status should show: "✅ Ready to receive notifications!"
- FCM token displayed in monospace font

### 6.2 Copy Token
- Tap "📋 Copy Token" button
- Toast message confirms copy

### 6.3 Check Logcat (Alternative)
In Android Studio:
1. Open Logcat (bottom panel)
2. Search for "FCM TOKEN"
3. Copy the full token from console

---

## Step 7: Test Push Notification

### 7.1 Send Test
1. Open browser: http://localhost:8080/test/push
2. Paste FCM token in the form
3. Enter title: "Test from Omega"
4. Enter body: "Hello from your notification system!"
5. Click "📤 Send Test Notification"

### 7.2 Receive Notification
You should see:
- Notification in system tray
- Sound/vibration
- Notification appears in app history

### 7.3 Test Different States
Try notification when:
- ✅ App is open (appears as banner + in history)
- ✅ App is in background (notification tray)
- ✅ App is closed (notification wakes app)
- ✅ Tap notification (opens app)

---

## Troubleshooting

### "google-services.json" error
- ✅ File must be in `app/` folder (not `app/src/`)
- ✅ File must be named exactly `google-services.json`
- ✅ Sync Gradle after adding file

### Package name mismatch
- ✅ Firebase package: `com.omega.pushtest`
- ✅ AndroidManifest package: `com.omega.pushtest`
- ✅ Must match exactly!

### Token not showing
- ✅ Check Logcat for errors
- ✅ Ensure google-services.json is correct
- ✅ Check internet connection
- ✅ Rebuild project (Build → Rebuild Project)

### Notification not received
- ✅ Grant notification permission
- ✅ Check Do Not Disturb is off
- ✅ Verify token is correct
- ✅ Check server has firebase-credentials.json
- ✅ Look for errors in Logcat

### Build errors
- ✅ Sync Gradle files
- ✅ Ensure compileSdk = 34
- ✅ Check internet connection for dependency download
- ✅ Invalidate caches (File → Invalidate Caches → Restart)

---

## Project Structure

```
android-app/
├── build.gradle                          # Top-level Gradle
├── app/
    ├── build.gradle                      # App-level Gradle
    ├── google-services.json              # Firebase config (you add this)
    ├── src/main/
        ├── AndroidManifest.xml           # App configuration
        ├── java/com/omega/pushtest/
        │   ├── MainActivity.kt           # Main UI
        │   └── MyFirebaseMessagingService.kt  # FCM handler
        └── res/
            ├── layout/
            │   └── activity_main.xml     # UI layout
            ├── values/
            │   ├── colors.xml
            │   ├── strings.xml
            │   └── themes.xml
            └── drawable/
                └── ic_notification.xml    # Notification icon
```

---

## Features

### ✅ What the App Does
- Registers with Firebase Cloud Messaging
- Gets FCM token automatically
- Displays token in UI with copy button
- Shows notification history
- Handles notifications in all states:
  - Foreground (in-app display)
  - Background (notification tray)
  - Closed (wakes app)
  - Tap handling (opens app)

### 📱 UI Features
- Omega logo (Ω)
- Real-time status indicator
- FCM token display
- One-tap copy to clipboard
- Instructions
- Notification history log

### 🔔 Notification Features
- Title and body
- Custom data payload
- Sound and vibration
- Notification channel (Android 8+)
- Badge support
- Tap to open app

---

## Backend Configuration

Your backend already supports FCM! Just ensure:

1. **Firebase credentials configured:**
   ```
   config/firebase-credentials.json
   ```

2. **Server running:**
   ```powershell
   .venv\Scripts\python.exe scripts\start_api.py
   ```

3. **Status check:**
   - Visit: http://localhost:8080/test/push
   - Should show "✅ Service Ready" (not demo mode)

---

## Cost Summary

### Android Push Notifications:
- FCM: **FREE** forever
- No developer subscription: **FREE**
- No Play Store fee for testing: **FREE**
- Google account: **FREE**

### Total Cost: **$0**

Compare to iOS:
- iOS: $99/year for Apple Developer Program
- Android: **$0** ✅

---

## Tips

- Keep Logcat open to see debug messages
- Token is generated on first app launch
- Token may refresh occasionally - copy new one if needed
- Test on real device (emulator works too but less reliable)
- No need to publish to Play Store for testing

---

## Next Steps

1. ✅ Follow Steps 1-7 to set up app
2. ✅ Copy FCM token
3. ✅ Test via http://localhost:8080/test/push
4. ✅ Test with different notification content
5. ✅ Test with custom data payload
6. ✅ Test notification in different app states

---

## Support

Common issues:
- **Token not generated**: Check Logcat for Firebase errors
- **Build fails**: Sync Gradle, check internet connection
- **Notification not received**: Verify google-services.json and package name match

---

**Ready to test Android push notifications! 🤖✨**

Completely FREE - no subscriptions needed!
