# iOS Quick Start for Omega Push Notifications

## Minimal Working Example

Here's the simplest iOS app to receive push notifications from Omega:

### 1. Create New iOS Project in Xcode

1. Open Xcode → Create New Project → App
2. Product Name: `OmegaNotifications`
3. Bundle Identifier: `com.yourcompany.omega` (remember this!)
4. Language: Swift

### 2. Install Firebase

Create `Podfile` in project root:
```ruby
platform :ios, '14.0'
use_frameworks!

target 'OmegaNotifications' do
  pod 'Firebase/Messaging'
end
```

Install:
```bash
pod install
```

**From now on, open `OmegaNotifications.xcworkspace` (NOT .xcodeproj)**

### 3. Add Firebase Config

- Download `GoogleService-Info.plist` from Firebase Console
- Drag it into Xcode project navigator (next to Info.plist)
- ✅ Check "Copy items if needed"

### 4. Update AppDelegate.swift

Replace entire file with:

```swift
import UIKit
import Firebase
import FirebaseMessaging
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate {

    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Initialize Firebase
        FirebaseApp.configure()
        
        // Set delegates
        Messaging.messaging().delegate = self
        UNUserNotificationCenter.current().delegate = self
        
        // Request notification permissions
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            print("✅ Permission granted: \(granted)")
            if let error = error {
                print("❌ Error: \(error)")
            }
        }
        
        // Register for remote notifications
        application.registerForRemoteNotifications()
        
        return true
    }
    
    // Called when APNs token is received
    func application(_ application: UIApplication, 
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        print("✅ APNs Token received")
        Messaging.messaging().apnsToken = deviceToken
    }
    
    func application(_ application: UIApplication, 
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("❌ Failed to register: \(error)")
    }

    // MARK: UISceneSession Lifecycle

    func application(_ application: UIApplication, 
                     configurationForConnecting connectingSceneSession: UISceneSession, 
                     options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        return UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
    }
}

// MARK: - Firebase Messaging Delegate

extension AppDelegate: MessagingDelegate {
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let token = fcmToken else { return }
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📱 FCM TOKEN (copy this!):")
        print(token)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        // Save for easy access
        UserDefaults.standard.set(token, forKey: "fcmToken")
        
        // Post notification to update UI
        NotificationCenter.default.post(name: .fcmTokenReceived, object: token)
    }
}

// MARK: - User Notification Center Delegate

extension AppDelegate: UNUserNotificationCenterDelegate {
    
    // Called when notification arrives while app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        
        let userInfo = notification.request.content.userInfo
        print("📬 Notification received (foreground): \(userInfo)")
        
        // Show notification even when app is active
        completionHandler([[.banner, .sound, .badge]])
    }
    
    // Called when user taps notification
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        
        let userInfo = response.notification.request.content.userInfo
        print("🔔 Notification tapped: \(userInfo)")
        
        // Handle deep linking or custom actions here
        if let customData = userInfo["customKey"] as? String {
            print("Custom data: \(customData)")
        }
        
        completionHandler()
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let fcmTokenReceived = Notification.Name("fcmTokenReceived")
}
```

### 5. Update ViewController.swift

Replace with this user-friendly version:

```swift
import UIKit

class ViewController: UIViewController {
    
    private let tokenLabel: UILabel = {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = .center
        label.font = .systemFont(ofSize: 12, weight: .regular)
        label.textColor = .secondaryLabel
        label.text = "Waiting for FCM token..."
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let copyButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Copy Token", for: .normal)
        button.titleLabel?.font = .systemFont(ofSize: 18, weight: .semibold)
        button.translatesAutoresizingMaskIntoConstraints = false
        return button
    }()
    
    private let statusLabel: UILabel = {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = .center
        label.font = .systemFont(ofSize: 16, weight: .medium)
        label.textColor = .label
        label.text = "🔄 Initializing..."
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let instructionsLabel: UILabel = {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = .center
        label.font = .systemFont(ofSize: 14)
        label.textColor = .secondaryLabel
        label.text = """
        1. Copy your FCM token
        2. Go to http://localhost:5000/test/push
        3. Paste token and send test notification
        """
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private var currentToken: String?

    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupObservers()
        checkForToken()
    }
    
    private func setupUI() {
        view.backgroundColor = .systemBackground
        
        let stackView = UIStackView(arrangedSubviews: [
            statusLabel,
            tokenLabel,
            copyButton,
            instructionsLabel
        ])
        stackView.axis = .vertical
        stackView.spacing = 20
        stackView.alignment = .center
        stackView.translatesAutoresizingMaskIntoConstraints = false
        
        view.addSubview(stackView)
        
        NSLayoutConstraint.activate([
            stackView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            stackView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            stackView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20)
        ])
        
        copyButton.addTarget(self, action: #selector(copyTokenTapped), for: .touchUpInside)
        copyButton.isEnabled = false
    }
    
    private func setupObservers() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(tokenReceived(_:)),
            name: .fcmTokenReceived,
            object: nil
        )
    }
    
    private func checkForToken() {
        if let token = UserDefaults.standard.string(forKey: "fcmToken") {
            updateUI(with: token)
        }
    }
    
    @objc private func tokenReceived(_ notification: Notification) {
        if let token = notification.object as? String {
            DispatchQueue.main.async {
                self.updateUI(with: token)
            }
        }
    }
    
    private func updateUI(with token: String) {
        currentToken = token
        
        // Show truncated token
        let truncated = "\(token.prefix(20))...\(token.suffix(20))"
        tokenLabel.text = "Token: \(truncated)"
        
        statusLabel.text = "✅ Ready to receive notifications!"
        copyButton.isEnabled = true
        
        print("Token available: \(token)")
    }
    
    @objc private func copyTokenTapped() {
        guard let token = currentToken else { return }
        
        UIPasteboard.general.string = token
        
        let alert = UIAlertController(
            title: "✅ Token Copied!",
            message: "Your FCM token has been copied to clipboard.\n\nNow paste it in the web interface at:\nhttp://localhost:5000/test/push",
            preferredStyle: .alert
        )
        
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        
        present(alert, animated: true)
        
        // Visual feedback
        copyButton.setTitle("✓ Copied!", for: .normal)
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            self.copyButton.setTitle("Copy Token", for: .normal)
        }
    }
    
    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
```

### 6. Enable Push Notifications Capability

1. Select your project in Xcode navigator
2. Select your app target
3. Go to **Signing & Capabilities** tab
4. Click **+ Capability**
5. Add **Push Notifications**
6. Add **Background Modes**
   - ✅ Check "Remote notifications"

### 7. Build and Run

1. Connect your iPhone (push notifications don't work on simulator!)
2. Select your device as the target
3. Press Cmd+R to build and run
4. Grant notification permissions when prompted
5. Check Xcode console for your FCM token

### 8. Copy Your Token

When the app launches, you'll see:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 FCM TOKEN (copy this!):
fL8Xj2kPQS6xY3mK9vH4bN7pT0wR1dC5aF6hG8iJ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Or just tap the "Copy Token" button in the app!

### 9. Test Notification

1. Copy your FCM token from the app
2. Open http://localhost:5000/test/push
3. Paste the token
4. Click "Send Test Notification"
5. 🎉 You should receive a notification on your iPhone!

---

## Common Issues

### "Failed to register for remote notifications"

**Solution:** You must test on a real iOS device. Push notifications don't work on simulator.

### "APNs certificate not uploaded"

1. Go to [Apple Developer Portal](https://developer.apple.com/account/)
2. Certificates, Identifiers & Profiles → Keys
3. Create new key with APNs enabled
4. Download `.p8` file
5. Upload to Firebase Console → Project Settings → Cloud Messaging → APNs Authentication Key

### Token not appearing

Check console for errors:
```bash
# In Xcode, open View → Debug Area → Activate Console
# Look for errors related to Firebase or notifications
```

### Notifications not received

✅ Enable Push Notifications capability  
✅ Upload APNs key to Firebase  
✅ Test on real device  
✅ Check notification permissions granted  
✅ App bundle ID matches Firebase config  
✅ Restart app after uploading APNs key  

---

## Testing on Your Device Right Now

Since you have an iPhone:

1. **Open Xcode** on your Mac
2. **Create new project** with bundle ID matching your Firebase setup
3. **Follow steps 2-7** above (takes ~10 minutes)
4. **Run on your iPhone**
5. **Copy token** from console or tap "Copy Token" button
6. **Paste in web interface** at http://localhost:5000/test/push
7. **Send test notification**
8. **See it on your lock screen!** 🎉

---

## Next Steps

Once you have your FCM token:
- ✅ Test different notification titles/bodies
- ✅ Try custom data payloads
- ✅ Test badge numbers
- ✅ Try custom sounds
- ✅ Test while app is:
  - In foreground (notification banner appears)
  - In background (notification in notification center)
  - Closed (notification wakes app)

**You're all set to test push notifications! 📱✨**
