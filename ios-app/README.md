# iOS App Setup Guide - Omega Push Notifications Test

This iOS app allows you to test push notifications from your Omega notifications manager system.

## Prerequisites

- **Mac** with Xcode 14+ installed
- **iPhone** (push notifications don't work on simulator)
- **Apple Developer Account** (free or paid)
- **Firebase project** set up (see main PUSH_NOTIFICATIONS_SETUP.md)

## Step 1: Create Xcode Project

### 1.1 Open Xcode
- Launch Xcode
- Click "Create New Project"

### 1.2 Project Settings
- Choose **App** template
- Click "Next"

### 1.3 Fill in Details
- **Product Name**: `OmegaPushTest`
- **Team**: Select your Apple Developer team
- **Organization Identifier**: `com.yourname` (use your own)
- **Bundle Identifier**: Will be `com.yourname.OmegaPushTest`
- **Interface**: Storyboard
- **Language**: Swift
- **Storage**: None
- Uncheck "Include Tests"
- Click "Next"

### 1.4 Save Location
- Choose `notifications-manager/ios-app/` folder
- Click "Create"

## Step 2: Add Firebase Configuration

### 2.1 Download GoogleService-Info.plist
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Click ⚙️ → Project Settings
4. Scroll to "Your apps"
5. Click "Add app" → iOS
6. Enter Bundle ID: `com.yourname.OmegaPushTest` (same as Xcode)
7. Click "Register app"
8. Download `GoogleService-Info.plist`

### 2.2 Add to Xcode
1. Drag `GoogleService-Info.plist` into Xcode project navigator
2. Check "Copy items if needed"
3. Make sure "OmegaPushTest" target is selected
4. Click "Finish"

## Step 3: Copy Source Files

### 3.1 Replace AppDelegate.swift
1. In Xcode, delete the existing `AppDelegate.swift`
2. Drag the new `AppDelegate.swift` from `ios-app/` folder into Xcode
3. Check "Copy items if needed"

### 3.2 Replace ViewController.swift
1. Delete existing `ViewController.swift`
2. Drag the new `ViewController.swift` from `ios-app/` folder
3. Check "Copy items if needed"

### 3.3 Add SceneDelegate.swift
1. Drag `SceneDelegate.swift` from `ios-app/` folder into Xcode
2. Check "Copy items if needed"

### 3.4 Replace Info.plist
1. Delete existing `Info.plist`
2. Drag the new `Info.plist` from `ios-app/` folder
3. Check "Copy items if needed"

## Step 4: Install CocoaPods Dependencies

### 4.1 Install CocoaPods (if not already installed)
```bash
sudo gem install cocoapods
```

### 4.2 Navigate to Project
```bash
cd "d:/programming/upc-pi2/notifications-manager/ios-app"
```

### 4.3 Install Dependencies
```bash
pod install
```

This will create `OmegaPushTest.xcworkspace`

### 4.4 Important!
**From now on, open `OmegaPushTest.xcworkspace` (NOT the .xcodeproj file)**

## Step 5: Enable Push Notifications Capability

### 5.1 In Xcode
1. Select your project in the navigator
2. Select "OmegaPushTest" target
3. Click "Signing & Capabilities" tab
4. Click "+ Capability"
5. Add **"Push Notifications"**
6. Add **"Background Modes"**
   - Check "Remote notifications"

### 5.2 Configure Signing
1. Under "Signing & Capabilities"
2. Select your Team
3. Xcode will automatically manage signing

## Step 6: Upload APNs Certificate to Firebase

### 6.1 Generate APNs Key
1. Go to [Apple Developer Portal](https://developer.apple.com/account/)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Click **Keys** → **+** (Create a key)
4. Name it "Omega Push Key"
5. Check **Apple Push Notifications service (APNs)**
6. Click "Continue" → "Register"
7. **Download the .p8 file** (save it securely!)
8. Note the **Key ID** (you'll need this)

### 6.2 Find Your Team ID
1. In Apple Developer Portal
2. Go to **Membership**
3. Copy your **Team ID**

### 6.3 Upload to Firebase
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Go to Project Settings
4. Click **Cloud Messaging** tab
5. Scroll to **Apple app configuration**
6. Under **APNs Authentication Key**, click **Upload**
7. Upload your `.p8` file
8. Enter **Key ID**
9. Enter **Team ID**
10. Click "Upload"

## Step 7: Build and Run

### 7.1 Connect Your iPhone
1. Plug in your iPhone via USB
2. Trust the computer if prompted on iPhone

### 7.2 Select Device
1. In Xcode, at the top, click the device selector
2. Select your iPhone from the list

### 7.3 Run the App
1. Click the Play button (▶️) or press Cmd+R
2. Wait for the app to build and install
3. If prompted, grant notification permissions on your iPhone

### 7.4 Check Console
In Xcode's console (bottom panel), you should see:
```
✅ Firebase initialized
✅ Notification permission granted
✅ APNs device token received
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 FCM TOKEN (COPY THIS!):
fL8Xj2kPQS6xY3mK9vH4bN7pT0wR1dC5aF6hG8iJ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 8: Test Notifications

### 8.1 Copy FCM Token
- In the app, tap the "📋 Copy Token" button
- Or copy it from Xcode console

### 8.2 Send Test Notification
1. Open browser: http://localhost:5000/test/push
2. Paste the FCM token
3. Enter title and message
4. Click "📤 Send Test Notification"

### 8.3 Check Your iPhone
You should receive the notification! 🎉

## Troubleshooting

### "Failed to register for remote notifications"
- ✅ Must use real device (not simulator)
- ✅ Check internet connection
- ✅ Ensure signing is configured

### APNs certificate error
- ✅ Verify you uploaded correct .p8 file to Firebase
- ✅ Check Key ID and Team ID are correct
- ✅ Wait a few minutes after uploading, then restart app

### No token in console
- ✅ Check GoogleService-Info.plist is added
- ✅ Verify bundle ID matches in Xcode and Firebase
- ✅ Look for errors in Xcode console

### Notification not received
- ✅ Grant notification permissions
- ✅ Check notification settings on iPhone (Settings → Notifications → OmegaPushTest)
- ✅ Ensure APNs key is uploaded to Firebase
- ✅ Verify Firebase credentials on server

### Build errors after pod install
- ✅ Open `.xcworkspace` file, NOT `.xcodeproj`
- ✅ Clean build folder (Cmd+Shift+K)
- ✅ Rebuild (Cmd+B)

## Project Structure

```
ios-app/
├── Podfile                          # CocoaPods dependencies
├── AppDelegate.swift                # App lifecycle & Firebase setup
├── ViewController.swift             # Main UI with token display
├── SceneDelegate.swift              # Scene lifecycle (iOS 13+)
├── Info.plist                       # App configuration
├── GoogleService-Info.plist         # Firebase config (you add this)
└── README.md                        # This file

After pod install:
├── OmegaPushTest.xcworkspace        # Open this in Xcode!
├── Pods/                            # CocoaPods dependencies
└── Podfile.lock                     # Dependency versions
```

## Features

### ✅ What the App Does
- Registers for push notifications with APNs
- Gets FCM token from Firebase
- Displays token in UI
- Copy token to clipboard
- Shows notification history
- Handles notifications when:
  - App is in foreground (banner appears)
  - App is in background (notification center)
  - App is closed (wakes app)
  - User taps notification

### 📱 UI Elements
- Omega logo (Ω)
- Status indicator
- FCM token display (monospace font)
- Copy button
- Instructions
- Notification history log

### 🔔 Notification Features
- Title and body
- Custom data payload
- Badge count
- Sound
- Tap handling
- Background notifications

## Next Steps

1. ✅ Follow Steps 1-7 to set up the app
2. ✅ Copy your FCM token
3. ✅ Test sending notifications via web interface
4. ✅ Test different notification types (badge, sound, data)
5. ✅ Test with app in different states (foreground/background/closed)

## Tips

- Keep Xcode console open to see debug logs
- Token refreshes occasionally - copy new token if needed
- Notifications work best on real device connected to cellular/WiFi
- Test both while app is active and when closed

## Support

If you encounter issues:
1. Check Xcode console for error messages
2. Verify all steps completed correctly
3. Check Firebase Console for APNs certificate status
4. Ensure server has valid Firebase credentials

---

**Ready to test push notifications on iOS! 📱✨**
