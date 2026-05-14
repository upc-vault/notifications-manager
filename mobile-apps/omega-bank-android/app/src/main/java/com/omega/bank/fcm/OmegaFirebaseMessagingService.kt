package com.omega.bank.fcm

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.RingtoneManager
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.omega.bank.R
import com.omega.bank.ui.MainActivity
import com.omega.bank.network.ApiService
import com.omega.bank.network.ApiClient
import com.omega.bank.utils.PrefsManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class OmegaFirebaseMessagingService : FirebaseMessagingService() {
    
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d(TAG, "New FCM token: ${token.take(20)}...")
        
        // Save token
        PrefsManager.saveFCMToken(token)
        
        // Register with backend if user is logged in
        if (PrefsManager.isLoggedIn()) {
            registerTokenWithBackend(token)
        }
    }
    
    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        
        Log.d(TAG, "Message received from: ${message.from}")
        
        // Handle notification
        message.notification?.let {
            showNotification(it.title ?: "Omega Bank", it.body ?: "")
        }
        
        // Handle data payload
        message.data.isNotEmpty().let {
            Log.d(TAG, "Message data: ${message.data}")
            handleDataPayload(message.data)
        }
    }
    
    private fun handleDataPayload(data: Map<String, String>) {
        val title = data["title"] ?: "Omega Bank"
        val body = data["body"] ?: "You have a new notification"
        
        showNotification(title, body, data)
    }
    
    private fun showNotification(title: String, body: String, data: Map<String, String>? = null) {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            data?.forEach { (key, value) ->
                putExtra(key, value)
            }
        }
        
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            } else {
                PendingIntent.FLAG_UPDATE_CURRENT
            }
        )
        
        val channelId = getString(R.string.default_notification_channel_id)
        val defaultSoundUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
        
        val notificationBuilder = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .setSound(defaultSoundUri)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
        
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(System.currentTimeMillis().toInt(), notificationBuilder.build())
        
        Log.d(TAG, "Notification shown: $title")
    }
    
    private fun registerTokenWithBackend(token: String) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val deviceInfo = "${Build.MODEL}, Android ${Build.VERSION.RELEASE}"
                val appVersion = applicationContext.packageManager
                    .getPackageInfo(applicationContext.packageName, 0).versionName
                
                val apiService = ApiService()
                val response = apiService.registerDeviceToken(token, "android", deviceInfo, appVersion)
                
                Log.d(TAG, "FCM token registration response: $response")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to register FCM token", e)
            }
        }
    }
    
    companion object {
        private const val TAG = "OmegaFCMService"
    }
}
