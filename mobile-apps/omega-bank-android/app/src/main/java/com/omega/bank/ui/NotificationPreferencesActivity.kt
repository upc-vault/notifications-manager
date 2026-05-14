package com.omega.bank.ui

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.switchmaterial.SwitchMaterial
import com.omega.bank.R
import com.omega.bank.network.ApiService
import com.omega.bank.network.ApiResponse
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class NotificationPreferencesActivity : AppCompatActivity() {
    
    private lateinit var pushNotificationsSwitch: SwitchMaterial
    private lateinit var emailNotificationsSwitch: SwitchMaterial
    private lateinit var smsNotificationsSwitch: SwitchMaterial
    private val apiService = ApiService()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_notification_preferences)
        
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Notification Preferences"
        
        pushNotificationsSwitch = findViewById(R.id.switch_push)
        emailNotificationsSwitch = findViewById(R.id.switch_email)
        smsNotificationsSwitch = findViewById(R.id.switch_sms)
        
        loadPreferences()
        setupListeners()
    }
    
    private fun loadPreferences() {
        CoroutineScope(Dispatchers.IO).launch {
            when (val response = apiService.getPreferences()) {
                is ApiResponse.Success -> {
                    withContext(Dispatchers.Main) {
                        val prefs = response.data
                        pushNotificationsSwitch.isChecked = prefs.channels?.get("push") ?: true
                        emailNotificationsSwitch.isChecked = prefs.channels?.get("email") ?: true
                        smsNotificationsSwitch.isChecked = prefs.channels?.get("sms") ?: true
                    }
                }
                is ApiResponse.Error -> {
                    withContext(Dispatchers.Main) {
                        Toast.makeText(
                            this@NotificationPreferencesActivity,
                            "Failed to load preferences: ${response.message}",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }
            }
        }
    }
    
    private fun setupListeners() {
        pushNotificationsSwitch.setOnCheckedChangeListener { _, isChecked ->
            updatePreference("push_enabled", isChecked)
        }
        
        emailNotificationsSwitch.setOnCheckedChangeListener { _, isChecked ->
            updatePreference("email_enabled", isChecked)
        }
        
        smsNotificationsSwitch.setOnCheckedChangeListener { _, isChecked ->
            updatePreference("sms_enabled", isChecked)
        }
    }
    
    private fun updatePreference(key: String, value: Boolean) {
        CoroutineScope(Dispatchers.IO).launch {
            val params = mapOf(key to value)
            when (val response = apiService.updatePreferences(params)) {
                is ApiResponse.Success -> {
                    withContext(Dispatchers.Main) {
                        Toast.makeText(
                            this@NotificationPreferencesActivity,
                            "Preference updated",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }
                is ApiResponse.Error -> {
                    withContext(Dispatchers.Main) {
                        Toast.makeText(
                            this@NotificationPreferencesActivity,
                            "Failed to update: ${response.message}",
                            Toast.LENGTH_SHORT
                        ).show()
                        // Revert switch
                        loadPreferences()
                    }
                }
            }
        }
    }
    
    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
