package com.omega.pushtest

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.android.gms.tasks.OnCompleteListener
import com.google.firebase.messaging.FirebaseMessaging
import com.omega.pushtest.databinding.ActivityMainBinding
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var fcmToken: String? = null
    private val notificationHistory = mutableListOf<String>()
    
    companion object {
        private const val TAG = "MainActivity"
        private const val NOTIFICATION_PERMISSION_CODE = 123
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        requestNotificationPermission()
        getFCMToken()
        loadNotificationHistory()
    }

    private fun setupUI() {
        binding.apply {
            // Copy button
            btnCopyToken.setOnClickListener {
                copyTokenToClipboard()
            }
            
            // Status
            tvStatus.text = "🔄 Initializing Firebase..."
        }
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this,
                    Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                ActivityCompat.requestPermissions(
                    this,
                    arrayOf(Manifest.permission.POST_NOTIFICATIONS),
                    NOTIFICATION_PERMISSION_CODE
                )
            } else {
                Log.d(TAG, "✅ Notification permission already granted")
            }
        } else {
            Log.d(TAG, "✅ Notification permission not required (Android < 13)")
        }
    }

    private fun getFCMToken() {
        FirebaseMessaging.getInstance().token.addOnCompleteListener(OnCompleteListener { task ->
            if (!task.isSuccessful) {
                Log.w(TAG, "❌ Fetching FCM token failed", task.exception)
                binding.tvStatus.text = "❌ Failed to get token"
                return@OnCompleteListener
            }

            // Get token
            val token = task.result
            fcmToken = token

            Log.d(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            Log.d(TAG, "📱 FCM TOKEN (COPY THIS!):")
            Log.d(TAG, token)
            Log.d(TAG, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            updateUIWithToken(token)
        })
    }

    private fun updateUIWithToken(token: String) {
        binding.apply {
            // Update token display
            tvToken.text = token
            
            // Update status
            tvStatus.text = "✅ Ready to receive notifications!"
            
            // Enable copy button
            btnCopyToken.isEnabled = true
            
            Toast.makeText(
                this@MainActivity,
                "FCM Token ready! Check Logcat for full token.",
                Toast.LENGTH_LONG
            ).show()
        }
    }

    private fun copyTokenToClipboard() {
        fcmToken?.let { token ->
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("FCM Token", token)
            clipboard.setPrimaryClip(clip)

            // Show confirmation
            Toast.makeText(
                this,
                "✅ Token copied to clipboard!\n\nPaste it at:\nhttp://localhost:8080/test/push",
                Toast.LENGTH_LONG
            ).show()

            // Visual feedback
            binding.btnCopyToken.text = "✓ Copied!"
            binding.btnCopyToken.postDelayed({
                binding.btnCopyToken.text = "📋 Copy Token"
            }, 2000)
        } ?: run {
            Toast.makeText(this, "Token not available yet", Toast.LENGTH_SHORT).show()
        }
    }

    private fun loadNotificationHistory() {
        val prefs = getSharedPreferences("notifications", Context.MODE_PRIVATE)
        val historyJson = prefs.getString("history", "")
        
        if (historyJson.isNullOrEmpty()) {
            binding.tvNotificationHistory.text = "No notifications received yet..."
        } else {
            binding.tvNotificationHistory.text = historyJson
        }
    }

    fun addNotificationToHistory(title: String, body: String, data: Map<String, String>?) {
        val timestamp = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
        val entry = buildString {
            append("[$timestamp] $title: $body")
            if (!data.isNullOrEmpty()) {
                append("\nData: $data")
            }
        }

        notificationHistory.add(0, entry)
        
        // Keep only last 10
        if (notificationHistory.size > 10) {
            notificationHistory.removeAt(notificationHistory.size - 1)
        }

        // Update UI
        val historyText = notificationHistory.joinToString("\n\n---\n\n")
        binding.tvNotificationHistory.text = historyText

        // Save to preferences
        val prefs = getSharedPreferences("notifications", Context.MODE_PRIVATE)
        prefs.edit().putString("history", historyText).apply()
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == NOTIFICATION_PERMISSION_CODE) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Log.d(TAG, "✅ Notification permission granted")
                Toast.makeText(this, "✅ Notifications enabled", Toast.LENGTH_SHORT).show()
            } else {
                Log.d(TAG, "❌ Notification permission denied")
                Toast.makeText(
                    this,
                    "⚠️ Notification permission denied. You won't receive notifications.",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }
}
