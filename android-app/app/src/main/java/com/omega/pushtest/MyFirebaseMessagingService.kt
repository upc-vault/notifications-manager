package com.omega.pushtest

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class MyFirebaseMessagingService : FirebaseMessagingService() {

    companion object {
        private const val TAG = "FCMService"
        private const val CHANNEL_ID = "omega_notifications"
        private const val CHANNEL_NAME = "Omega Notifications"
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        
        Log.d(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        Log.d(TAG, "🔄 NEW FCM TOKEN:")
        Log.d(TAG, token)
        Log.d(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        // TODO: Send token to your server if needed
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        Log.d(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        Log.d(TAG, "📬 Message received from: ${message.from}")

        // Check if message contains notification payload
        message.notification?.let {
            Log.d(TAG, "📬 Notification Title: ${it.title}")
            Log.d(TAG, "📬 Notification Body: ${it.body}")
            
            showNotification(
                title = it.title ?: "Notification",
                body = it.body ?: "",
                data = message.data
            )
        }

        // Check if message contains data payload
        if (message.data.isNotEmpty()) {
            Log.d(TAG, "📦 Data Payload: ${message.data}")
            
            // If no notification payload, create one from data
            if (message.notification == null) {
                val title = message.data["title"] ?: "New Message"
                val body = message.data["body"] ?: "You have a new notification"
                showNotification(title, body, message.data)
            }
        }

        Log.d(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        // Update UI if app is in foreground
        updateMainActivity(
            message.notification?.title ?: "Notification",
            message.notification?.body ?: "Message received",
            message.data
        )
    }

    private fun showNotification(title: String, body: String, data: Map<String, String>) {
        createNotificationChannel()

        // Intent to open app when notification is tapped
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            putExtra("title", title)
            putExtra("body", body)
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        // Build notification
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .build()

        // Show notification
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(System.currentTimeMillis().toInt(), notification)

        Log.d(TAG, "✅ Notification displayed")
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Omega Push Notifications"
                enableLights(true)
                enableVibration(true)
            }

            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun updateMainActivity(title: String, body: String, data: Map<String, String>) {
        // Send broadcast to update MainActivity if it's running
        val intent = Intent("com.omega.pushtest.NOTIFICATION_RECEIVED").apply {
            putExtra("title", title)
            putExtra("body", body)
            putExtra("data", HashMap(data))
        }
        sendBroadcast(intent)
    }
}
