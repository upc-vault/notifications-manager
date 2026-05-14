package com.omega.bank.model

data class LoginResponse(
    val message: String,
    val access_token: String,
    val refresh_token: String,
    val user: User
)

data class User(
    val id: Int,
    val username: String,
    val email: String,
    val full_name: String?
)

data class PushRegisterResponse(
    val status: String,
    val message: String,
    val username: String,
    val platform: String
)

data class Transfer(
    val id: Int,
    val sender_id: Int,
    val receiver_id: Int,
    val amount: Double,
    val currency: String,
    val status: String,
    val description: String?,
    val reference_number: String,
    val notification_sent: Boolean,
    val created_at: String,
    val completed_at: String?
)

data class TransferResponse(
    val success: Boolean,
    val message: String,
    val transfer: Transfer
)

data class TransfersListResponse(
    val success: Boolean,
    val total: Int,
    val limit: Int,
    val offset: Int,
    val transfers: List<Transfer>
)

data class PreferencesResponse(
    val user_id: Int,
    val quiet_hours: Map<String, Any>?,
    val channels: Map<String, Boolean>?,
    val notification_types: Map<String, Boolean>?
)
