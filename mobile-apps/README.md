# Omega Bank - Mobile Apps

Complete mobile banking applications for Android and iOS with ML-powered push notifications.

## 🏗️ Project Structure

```
mobile-apps/
├── omega-bank-android/          # Android app (Kotlin)
│   ├── app/
│   │   ├── src/main/java/com/omega/bank/
│   │   │   ├── OmegaBankApp.kt
│   │   │   ├── network/
│   │   │   │   ├── ApiClient.kt
│   │   │   │   └── ApiService.kt
│   │   │   ├── model/
│   │   │   │   └── Models.kt
│   │   │   ├── ui/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── LoginActivity.kt
│   │   │   │   └── TransferActivity.kt
│   │   │   ├── fcm/
│   │   │   │   └── OmegaFirebaseMessagingService.kt
│   │   │   └── utils/
│   │   │       └── PrefsManager.kt
│   │   └── build.gradle
│   └── build.gradle
│
└── OmegaBank-iOS/               # iOS app (Swift/SwiftUI)
    ├── OmegaBank/
    │   ├── OmegaBankApp.swift
    │   ├── Services/
    │   │   └── APIService.swift
    │   ├── Managers/
    │   │   └── AuthManager.swift
    │   ├── Views/
    │   │   ├── LoginView.swift
    │   │   ├── MainView.swift
    │   │   └── TransferView.swift
    │   └── Models/
    │       └── Models.swift
    └── OmegaBank.xcodeproj/
```

## ✨ Features

### 1. **Authentication**
- User login/register
- JWT token management with encrypted storage
- Automatic token refresh
- Secure credential storage (EncryptedSharedPreferences on Android, Keychain on iOS)

### 2. **Money Transfers**
- P2P payments between users
- Real-time transfer history
- Transaction status tracking
- Reference number generation

### 3. **Push Notifications (ML-Powered)**
- Firebase Cloud Messaging integration
- Automatic device token registration
- **ML Decision System**: Uses Sleeping Bandit + Tug of War algorithms
- Personalized notification delivery based on user behavior
- Rich notifications with transaction details

### 4. **User Interface**
- Modern Material Design (Android) / iOS Human Interface Guidelines
- Identical design language across platforms
- Balance display
- Transaction history with sent/received filters
- Pull-to-refresh
- Loading states and error handling

## 🚀 Setup Instructions

### Prerequisites
- Backend API running on `http://localhost:8080`
- Firebase project configured (see `../FIREBASE_PUSH_SETUP.md`)
- Android Studio (for Android app)
- Xcode 15+ and Apple Developer Account (for iOS app - macOS required)

### Android Setup

1. **Open project in Android Studio:**
   ```bash
   cd mobile-apps/omega-bank-android
   # Open in Android Studio
   ```

2. **Add Firebase configuration:**
   - Download `google-services.json` from Firebase Console
   - Place in `app/` directory

3. **Update API URL** (if needed):
   - Open `app/build.gradle`
   - Modify `API_BASE_URL` (use `10.0.2.2` for emulator, or your local IP for physical device)

4. **Build and Run:**
   - Connect device or start emulator (with Google Play Services)
   - Click Run button in Android Studio

### iOS Setup

⚠️ **Important:** The iOS project needs to be created fresh in Xcode (project files are binary and can't be version-controlled).

**📖 Follow the detailed guide:** [`IOS_PROJECT_SETUP.md`](IOS_PROJECT_SETUP.md)

**Quick steps:**
1. Create new Xcode project: `OmegaBank` with Bundle ID `com.omega.bank`
2. Add Firebase via Swift Package Manager
3. Add `GoogleService-Info.plist` from Firebase Console
4. Enable Push Notifications + Background Modes capabilities
5. Copy Swift source files from this repository structure
6. Build and run on **physical device** (required for push notifications)

**Requirements:**
- Physical iOS device (simulator doesn't support push notifications)
- Apple Developer account ($99/year) for device testing
- APNs authentication key uploaded to Firebase (see FIREBASE_PUSH_SETUP.md)

---

## 📱 How It Works

### Transfer Flow with ML Notifications

1. **User initiates transfer:**
   ```kotlin
   // Android
   apiService.createTransfer(
       receiverUsername = "jane_doe",
       amount = 50.0,
       description = "Lunch payment"
   )
   ```

2. **Backend processes transfer:**
   - Creates transfer record
   - Updates status to "completed"
   - Triggers ML decision system

3. **ML Decision System:**
   ```python
   # Backend (automatic)
   decision_service.decide_and_notify({
       "user_id": "jane_doe",
       "event_type": "money_received",
       "priority": "high",
       "data": {
           "title": "💰 Money Received!",
           "body": "You received $50.00 from John Doe",
           "amount": 50.0,
           "sender": "john_doe"
       }
   })
   ```

4. **ML algorithms select best option:**
   - **Sleeping Bandit**: Chooses optimal template type (URGENT, FRIENDLY, etc.)
   - **Tug of War**: Selects best channel (Push, Email, SMS, WhatsApp)
   - Decision based on user's historical engagement

5. **Notification delivered:**
   - FCM sends push notification to receiver's device
   - User sees rich notification with transaction details
   - Tapping opens app directly to transaction

## 🎯 API Endpoints Used

### Authentication
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`

### Push Notifications
- `POST /api/v1/push/register` - Register FCM token
- `GET /api/v1/push/tokens` - Get user's registered devices

### Transfers
- `POST /api/v1/transfers` - Create new transfer
- `GET /api/v1/transfers` - Get transfer history
- `GET /api/v1/transfers/{id}` - Get transfer details

## 🧪 Testing

### Test Transfer Between Users

1. **Create two test accounts:**
   ```bash
   # User 1
   Username: alice
   Password: password123
   
   # User 2
   Username: bob
   Password: password123
   ```

2. **Login on different devices:**
   - Device A: Login as `alice`
   - Device B: Login as `bob`

3. **Send money from alice to bob:**
   - On Device A: Click "Send Money"
   - Enter `bob` as recipient
   - Enter amount: `25.00`
   - Click "Send"

4. **Observe ML notification:**
   - Device B receives push notification
   - ML system chose optimal template and channel
   - Notification includes amount, sender, reference number

5. **View transaction history:**
   - Device A: Shows transaction as "Sent"
   - Device B: Shows transaction as "Received"

## 🔐 Security Features

- Encrypted credential storage
- JWT authentication with automatic refresh
- HTTPS support (configure in production)
- Input validation and sanitization
- Secure FCM token handling

## 🎨 Design Philosophy

Both apps follow identical design principles:
- **Purple gradient theme** matching web dashboard
- **Card-based layouts** for clean organization
- **Material Design 3** (Android) / **iOS 17 Guidelines** (iOS)
- **Accessibility** support (font scaling, color contrast)
- **Dark mode ready** (can be enabled easily)

## 📊 ML Integration

The mobile apps seamlessly integrate with the backend's ML decision system:

- **User Profiling**: Every interaction updates user behavior models
- **Template Selection**: Sleeping Bandit learns which message styles work best
- **Channel Optimization**: Tug of War finds most effective delivery method
- **Feedback Loop**: Click tracking improves future predictions

## 🚀 Production Deployment

### Android
1. Generate signed APK
2. Update `API_BASE_URL` to production URL
3. Enable ProGuard/R8
4. Upload to Google Play Console

### iOS
1. Archive for distribution
2. Update API URL to production
3. Configure App Store Connect
4. Submit for review

## 📝 License

Part of the Omega Intelligent Notification Manager system.
