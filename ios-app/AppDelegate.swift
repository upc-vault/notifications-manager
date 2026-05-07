//
//  AppDelegate.swift
//  Omega Push Notifications Test
//
//  Firebase Cloud Messaging integration for testing push notifications
//

import UIKit
import Firebase
import FirebaseMessaging
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate {

    var window: UIWindow?

    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Initialize Firebase
        FirebaseApp.configure()
        print("✅ Firebase initialized")
        
        // Set messaging delegate
        Messaging.messaging().delegate = self
        
        // Set notification delegate
        UNUserNotificationCenter.current().delegate = self
        
        // Request notification permissions
        let authOptions: UNAuthorizationOptions = [.alert, .badge, .sound]
        UNUserNotificationCenter.current().requestAuthorization(options: authOptions) { granted, error in
            if granted {
                print("✅ Notification permission granted")
            } else {
                print("❌ Notification permission denied")
            }
            
            if let error = error {
                print("❌ Permission error: \(error.localizedDescription)")
            }
        }
        
        // Register for remote notifications
        application.registerForRemoteNotifications()
        
        return true
    }
    
    // Called when APNs token is received
    func application(_ application: UIApplication, 
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        print("✅ APNs device token received")
        
        // Pass APNs token to Firebase
        Messaging.messaging().apnsToken = deviceToken
        
        // Convert token to string for logging
        let tokenParts = deviceToken.map { data in String(format: "%02.2hhx", data) }
        let token = tokenParts.joined()
        print("📱 APNs Token: \(token)")
    }
    
    func application(_ application: UIApplication, 
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("❌ Failed to register for remote notifications: \(error.localizedDescription)")
    }
    
    // Handle notification when app is in background and user taps it
    func application(_ application: UIApplication,
                     didReceiveRemoteNotification userInfo: [AnyHashable: Any],
                     fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        
        print("📬 Remote notification received")
        print("User info: \(userInfo)")
        
        // Handle custom data
        if let customData = userInfo["custom_data"] as? [String: Any] {
            print("Custom data: \(customData)")
        }
        
        completionHandler(.newData)
    }

    // MARK: UISceneSession Lifecycle (iOS 13+)
    
    func application(_ application: UIApplication, 
                     configurationForConnecting connectingSceneSession: UISceneSession, 
                     options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        return UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
    }
}

// MARK: - Firebase Messaging Delegate

extension AppDelegate: MessagingDelegate {
    
    // Called when FCM token is generated or refreshed
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let fcmToken = fcmToken else {
            print("❌ FCM token is nil")
            return
        }
        
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📱 FCM TOKEN (COPY THIS!):")
        print(fcmToken)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        // Save token to UserDefaults
        UserDefaults.standard.set(fcmToken, forKey: "fcmToken")
        
        // Notify the app that token is available
        NotificationCenter.default.post(
            name: .fcmTokenReceived,
            object: fcmToken
        )
    }
}

// MARK: - User Notification Center Delegate

extension AppDelegate: UNUserNotificationCenterDelegate {
    
    // Called when notification arrives while app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        
        let userInfo = notification.request.content.userInfo
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📬 Notification received (FOREGROUND)")
        print("Title: \(notification.request.content.title)")
        print("Body: \(notification.request.content.body)")
        print("User info: \(userInfo)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        // Show notification banner, sound, and badge even when app is active
        if #available(iOS 14.0, *) {
            completionHandler([[.banner, .sound, .badge]])
        } else {
            completionHandler([[.alert, .sound, .badge]])
        }
    }
    
    // Called when user taps on notification
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        
        let userInfo = response.notification.request.content.userInfo
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🔔 Notification TAPPED")
        print("Title: \(response.notification.request.content.title)")
        print("Body: \(response.notification.request.content.body)")
        print("User info: \(userInfo)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        // Handle deep linking or custom actions here
        if let action = userInfo["action"] as? String {
            print("Action: \(action)")
            // Handle different actions
        }
        
        completionHandler()
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let fcmTokenReceived = Notification.Name("fcmTokenReceived")
}
