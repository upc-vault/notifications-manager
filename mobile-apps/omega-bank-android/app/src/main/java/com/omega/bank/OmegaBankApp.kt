package com.omega.bank

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import android.util.Log
import com.google.firebase.FirebaseApp
import com.google.firebase.messaging.FirebaseMessaging
import com.omega.bank.network.ApiClient
import com.omega.bank.utils.PrefsManager

class OmegaBankApp : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize PrefsManager
        PrefsManager.init(this)
        
        // Initialize Firebase
        FirebaseApp.initializeApp(this)
        
        // Create notification channels
        createNotificationChannels()
        
        // Set up API client with saved token
        val token = PrefsManager.getAccessToken()
        if (token != null) {
            ApiClient.setAccessToken(token)
            registerFCMToken()
        }
        
        Log.d(TAG, "OmegaBankApp initialized")
    }
    
    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channelId = getString(R.string.default_notification_channel_id)
            val channelName = "Money Transfers"
            val channelDescription = "Notifications for money transfers and payments"
            val importance = NotificationManager.IMPORTANCE_HIGH
            
            val channel = NotificationChannel(channelId, channelName, importance).apply {
                description = channelDescription
                enableLights(true)
                enableVibration(true)
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
            
            Log.d(TAG, "Notification channel created: $channelId")
        }
    }
    
    private fun registerFCMToken() {
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) {
                val token = task.result
                Log.d(TAG, "FCM Token obtained: ${token?.take(20)}...")
                // Token registration will be handled by MainActivity
            } else {
                Log.e(TAG, "Failed to get FCM token", task.exception)
            }
        }
    }
    
    companion object {
        private const val TAG = "OmegaBankApp"
    }
}
