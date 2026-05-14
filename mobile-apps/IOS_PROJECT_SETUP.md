# iOS Project Setup Guide - Omega Bank

## 🎯 Quick Start: Create iOS Project from Scratch

Since Xcode project files are binary and can't be version-controlled easily, follow these steps to create the iOS project:

### Step 1: Create New Xcode Project

1. Open **Xcode**
2. Click **"Create a new Xcode project"** or File → New → Project
3. Select **iOS** tab → **App** → Click **Next**
4. Configure your project:
   - **Product Name:** `OmegaBank`
   - **Team:** Select your Apple Developer team
   - **Organization Identifier:** `com.omega`
   - **Bundle Identifier:** Will be `com.omega.bank` (auto-generated)
   - **Interface:** `SwiftUI`
   - **Language:** `Swift`
   - **Storage:** None (uncheck Core Data)
   - Uncheck "Include Tests" for now
5. Click **Next** → Choose location: `mobile-apps/OmegaBank-iOS/`
6. Click **Create**

### Step 2: Install Firebase via Swift Package Manager (Recommended)

1. In Xcode, go to **File** → **Add Package Dependencies...**
2. Enter URL: `https://github.com/firebase/firebase-ios-sdk`
3. Click **Add Package**
4. Select packages:
   - ☑️ `FirebaseMessaging`
   - ☑️ `FirebaseAnalytics` (optional)
5. Click **Add Package**

**Alternative: CocoaPods**

If you prefer CocoaPods:

```bash
cd mobile-apps/OmegaBank-iOS
pod init
```

Edit `Podfile`:
```ruby
platform :ios, '15.0'

target 'OmegaBank' do
  use_frameworks!
  
  pod 'Firebase/Messaging'
  pod 'Firebase/Analytics'
end
```

Run:
```bash
pod install
open OmegaBank.xcworkspace
```

### Step 3: Add GoogleService-Info.plist

1. Download `GoogleService-Info.plist` from Firebase Console
2. Drag it into your Xcode project
3. ✅ Check "Copy items if needed"
4. ✅ Select your app target
5. Click **Finish**

### Step 4: Configure Capabilities

1. Select your **project** in Project Navigator
2. Select your **target** (OmegaBank)
3. Go to **Signing & Capabilities** tab
4. Click **+ Capability** → Add **Push Notifications**
5. Click **+ Capability** → Add **Background Modes**
6. Check ☑️ **Remote notifications**

### Step 5: Replace OmegaBankApp.swift

Replace the default `OmegaBankApp.swift` with:

```swift
import SwiftUI
import Firebase
import FirebaseMessaging
import UserNotifications

@main
struct OmegaBankApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var authManager = AuthManager()
    
    var body: some Scene {
        WindowGroup {
            if authManager.isAuthenticated {
                MainView()
                    .environmentObject(authManager)
            } else {
                LoginView()
                    .environmentObject(authManager)
            }
        }
    }
}

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate, MessagingDelegate {
    
    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        
        // Configure Firebase
        FirebaseApp.configure()
        
        // Set up notifications
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
    
    func application(_ application: UIApplication, 
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
        
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("📱 APNs Token: \(token)")
    }
    
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let token = fcmToken else { return }
        print("🔥 FCM Token: \(String(token.prefix(20)))...")
        
        UserDefaults.standard.set(token, forKey: "fcm_token")
        
        if let _ = UserDefaults.standard.string(forKey: "access_token") {
            registerDeviceToken(token: token)
        }
    }
    
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                                willPresent notification: UNNotification, 
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound, .badge])
    }
    
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                                didReceive response: UNNotificationResponse, 
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo
        print("📬 Notification tapped: \(userInfo)")
        completionHandler()
    }
    
    private func registerDeviceToken(token: String) {
        guard let accessToken = UserDefaults.standard.string(forKey: "access_token") else { return }
        
        let deviceInfo = "\(UIDevice.current.model), iOS \(UIDevice.current.systemVersion)"
        let appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
        
        let parameters: [String: Any] = [
            "device_token": token,
            "platform": "ios",
            "device_info": deviceInfo,
            "app_version": appVersion
        ]
        
        APIService.shared.registerPushToken(parameters: parameters) { result in
            switch result {
            case .success(let response):
                print("✓ Device registered: \(response)")
            case .failure(let error):
                print("✗ Registration failed: \(error)")
            }
        }
    }
}
```

### Step 6: Create Supporting Files

Create a new folder structure in Xcode:
- Right-click project → New Group → Name it `Services`
- Right-click project → New Group → Name it `Views`
- Right-click project → New Group → Name it `Managers`
- Right-click project → New Group → Name it `Models`

### Step 7: Add Source Files

Copy the Swift files from the repository structure into your Xcode project:

**Services/APIService.swift:**
```swift
// Copy content from: mobile-apps/OmegaBank-iOS/OmegaBank/Services/APIService.swift
```

**Managers/AuthManager.swift:**
```swift
// Copy content from: mobile-apps/OmegaBank-iOS/OmegaBank/Managers/AuthManager.swift
```

**Views/LoginView.swift:**
```swift
import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            ZStack {
                LinearGradient(
                    colors: [Color(hex: "667eea"), Color(hex: "764ba2")],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                VStack(spacing: 30) {
                    Spacer()
                    
                    VStack(spacing: 10) {
                        Image(systemName: "building.columns.fill")
                            .font(.system(size: 70))
                            .foregroundColor(.white)
                        
                        Text("Omega Bank")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                    }
                    
                    Spacer()
                    
                    VStack(spacing: 20) {
                        TextField("Username", text: $username)
                            .textFieldStyle(.roundedBorder)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                        
                        SecureField("Password", text: $password)
                            .textFieldStyle(.roundedBorder)
                        
                        if let error = errorMessage {
                            Text(error)
                                .foregroundColor(.red)
                                .font(.caption)
                        }
                        
                        Button(action: login) {
                            if isLoading {
                                ProgressView()
                                    .tint(.white)
                            } else {
                                Text("Login")
                                    .fontWeight(.semibold)
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.white)
                        .foregroundColor(Color(hex: "667eea"))
                        .cornerRadius(10)
                        .disabled(isLoading)
                    }
                    .padding(.horizontal, 40)
                    
                    Spacer()
                }
            }
            .navigationBarHidden(true)
        }
    }
    
    private func login() {
        guard !username.isEmpty, !password.isEmpty else {
            errorMessage = "Please fill all fields"
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        authManager.login(username: username, password: password) { result in
            isLoading = false
            
            switch result {
            case .success():
                print("✓ Login successful")
            case .failure(let error):
                errorMessage = error.localizedDescription
            }
        }
    }
}

// Color extension
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
```

**Views/MainView.swift:**
```swift
import SwiftUI

struct MainView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var balance: Double = 1250.50
    @State private var showingTransferSheet = false
    @State private var transfers: [Transfer] = []
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Balance Card
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Available Balance")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        Text("$\(balance, specifier: "%.2f")")
                            .font(.system(size: 40, weight: .bold))
                            .foregroundColor(.primary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(
                        LinearGradient(
                            colors: [Color(hex: "667eea"), Color(hex: "764ba2")],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .foregroundColor(.white)
                    .cornerRadius(15)
                    .shadow(radius: 5)
                    .padding(.horizontal)
                    
                    // Actions
                    Button(action: { showingTransferSheet = true }) {
                        HStack {
                            Image(systemName: "arrow.up.circle.fill")
                            Text("Send Money")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(hex: "667eea"))
                        .foregroundColor(.white)
                        .cornerRadius(10)
                    }
                    .padding(.horizontal)
                    
                    // Transactions
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Recent Transactions")
                            .font(.headline)
                            .padding(.horizontal)
                        
                        if isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                                .padding()
                        } else if transfers.isEmpty {
                            Text("No transactions yet")
                                .foregroundColor(.secondary)
                                .frame(maxWidth: .infinity)
                                .padding()
                        } else {
                            ForEach(transfers) { transfer in
                                TransferRow(transfer: transfer)
                            }
                        }
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Omega Bank")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { authManager.logout() }) {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                    }
                }
            }
            .sheet(isPresented: $showingTransferSheet) {
                TransferView()
            }
            .onAppear(perform: loadTransfers)
        }
    }
    
    private func loadTransfers() {
        isLoading = true
        
        APIService.shared.getTransfers { result in
            isLoading = false
            
            switch result {
            case .success(let response):
                transfers = response.transfers
            case .failure(let error):
                print("Failed to load transfers: \(error)")
            }
        }
    }
}

struct TransferRow: View {
    let transfer: Transfer
    
    var body: some View {
        HStack {
            Image(systemName: "arrow.up.circle.fill")
                .foregroundColor(Color(hex: "667eea"))
            
            VStack(alignment: .leading) {
                Text("Transfer")
                    .font(.headline)
                Text(transfer.createdAt)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            Text("$\(transfer.amount, specifier: "%.2f")")
                .font(.headline)
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(10)
        .shadow(radius: 2)
        .padding(.horizontal)
    }
}
```

**Views/TransferView.swift:**
```swift
import SwiftUI

struct TransferView: View {
    @Environment(\.dismiss) var dismiss
    @State private var recipientUsername = ""
    @State private var amount = ""
    @State private var description = ""
    @State private var isLoading = false
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Recipient")) {
                    TextField("Username", text: $recipientUsername)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }
                
                Section(header: Text("Amount")) {
                    TextField("0.00", text: $amount)
                        .keyboardType(.decimalPad)
                }
                
                Section(header: Text("Description (Optional)")) {
                    TextField("What's this for?", text: $description)
                }
                
                Section {
                    Button(action: sendTransfer) {
                        if isLoading {
                            HStack {
                                Spacer()
                                ProgressView()
                                Spacer()
                            }
                        } else {
                            Text("Send Money")
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .disabled(isLoading || recipientUsername.isEmpty || amount.isEmpty)
                }
            }
            .navigationTitle("Send Money")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .alert("Transfer", isPresented: $showingAlert) {
                Button("OK") {
                    if alertMessage.contains("successful") {
                        dismiss()
                    }
                }
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    private func sendTransfer() {
        guard let amountValue = Double(amount) else {
            alertMessage = "Invalid amount"
            showingAlert = true
            return
        }
        
        isLoading = true
        
        APIService.shared.createTransfer(
            receiverUsername: recipientUsername,
            amount: amountValue,
            description: description.isEmpty ? nil : description
        ) { result in
            isLoading = false
            
            switch result {
            case .success(_):
                alertMessage = "Transfer successful! The recipient will be notified."
                showingAlert = true
            case .failure(let error):
                alertMessage = error.localizedDescription
                showingAlert = true
            }
        }
    }
}
```

### Step 8: Update Info.plist

Add the following keys to your `Info.plist`:

Right-click `Info.plist` → Open As → Source Code, then add:

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

**Note:** For production, use proper SSL certificates and remove this.

### Step 9: Build and Run

1. Select a **physical iOS device** (simulator won't work for push notifications)
2. Click **Run** (▶️) or press ⌘R
3. Check Xcode console for "FCM Token: ..."
4. Test login and transfers

## 🐛 Common Xcode Errors

### "Module 'Firebase' not found"
- Solution: Clean build folder (⇧⌘K) then rebuild

### "Code signing error"
- Solution: Select your team in Signing & Capabilities

### "Failed to register bundle identifier"
- Solution: Change bundle ID to something unique like `com.yourdomain.omegabank`

### "GoogleService-Info.plist not found"
- Solution: Make sure the file is added to the target (check File Inspector)

## 📝 Notes

- iOS push notifications **require a physical device** - simulator won't work
- You need an **Apple Developer account** ($99/year) for device testing
- APNs key must be uploaded to Firebase Console (see FIREBASE_PUSH_SETUP.md)

## ✅ Verification

After setup, you should see in Xcode console:
```
✅ Notification permission granted
📱 APNs Token: [hex string]
🔥 FCM Token: [Firebase token]
```

Now your iOS app is ready to receive push notifications via the ML decision system! 🎉
