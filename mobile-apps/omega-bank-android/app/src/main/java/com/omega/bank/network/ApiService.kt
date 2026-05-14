package com.omega.bank.network

import com.google.gson.Gson
import com.omega.bank.model.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

class ApiService {
    private val client = ApiClient.client
    private val baseUrl = ApiClient.getBaseUrl()
    private val gson = Gson()
    
    // Auth
    fun login(username: String, password: String): ApiResponse<LoginResponse> {
        val json = JSONObject().apply {
            put("username", username)
            put("password", password)
        }
        
        val request = Request.Builder()
            .url("$baseUrl/auth/login")
            .post(json.toString().toRequestBody("application/json".toMediaType()))
            .build()
        
        return executeRequest(request)
    }
    
    fun register(username: String, email: String, password: String, fullName: String): ApiResponse<LoginResponse> {
        val json = JSONObject().apply {
            put("username", username)
            put("email", email)
            put("password", password)
            put("full_name", fullName)
        }
        
        val request = Request.Builder()
            .url("$baseUrl/auth/register")
            .post(json.toString().toRequestBody("application/json".toMediaType()))
            .build()
        
        return executeRequest(request)
    }
    
    // Push Notifications
    fun registerDeviceToken(deviceToken: String, platform: String, deviceInfo: String, appVersion: String): ApiResponse<PushRegisterResponse> {
        val json = JSONObject().apply {
            put("device_token", deviceToken)
            put("platform", platform)
            put("device_info", deviceInfo)
            put("app_version", appVersion)
        }
        
        val request = Request.Builder()
            .url("$baseUrl/push/register")
            .post(json.toString().toRequestBody("application/json".toMediaType()))
            .build()
        
        return executeRequest(request)
    }
    
    // Transfers
    fun createTransfer(receiverUsername: String, amount: Double, description: String?): ApiResponse<TransferResponse> {
        val json = JSONObject().apply {
            put("receiver_username", receiverUsername)
            put("amount", amount)
            description?.let { put("description", it) }
        }
        
        val request = Request.Builder()
            .url("$baseUrl/transfers")
            .post(json.toString().toRequestBody("application/json".toMediaType()))
            .build()
        
        return executeRequest(request)
    }
    
    fun getTransfers(type: String = "all", limit: Int = 50, offset: Int = 0): ApiResponse<TransfersListResponse> {
        val url = "$baseUrl/transfers?type=$type&limit=$limit&offset=$offset"
        
        val request = Request.Builder()
            .url(url)
            .get()
            .build()
        
        return executeRequest(request)
    }
    
    // Preferences
    fun getPreferences(): ApiResponse<PreferencesResponse> {
        val request = Request.Builder()
            .url("$baseUrl/preferences")
            .get()
            .build()
        
        return executeRequest(request)
    }
    
    fun updatePreferences(preferences: Map<String, Any>): ApiResponse<PreferencesResponse> {
        val json = JSONObject(preferences)
        
        val request = Request.Builder()
            .url("$baseUrl/preferences")
            .put(json.toString().toRequestBody("application/json".toMediaType()))
            .build()
        
        return executeRequest(request)
    }
    
    private inline fun <reified T> executeRequest(request: Request): ApiResponse<T> {
        return try {
            client.newCall(request).execute().use { response ->
                val body = response.body?.string()
                
                if (response.isSuccessful && body != null) {
                    val data = gson.fromJson(body, T::class.java)
                    ApiResponse.Success(data)
                } else {
                    val errorMessage = body?.let {
                        try {
                            JSONObject(it).optString("error", "Unknown error")
                        } catch (e: Exception) {
                            "Request failed"
                        }
                    } ?: "Request failed"
                    ApiResponse.Error(errorMessage, response.code)
                }
            }
        } catch (e: IOException) {
            ApiResponse.Error("Network error: ${e.message}", -1)
        } catch (e: Exception) {
            ApiResponse.Error("Error: ${e.message}", -1)
        }
    }
}

sealed class ApiResponse<out T> {
    data class Success<T>(val data: T) : ApiResponse<T>()
    data class Error(val message: String, val code: Int) : ApiResponse<Nothing>()
}
