package com.kaow.mobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** A registered PC daemon row from `devices`. */
@Serializable
data class DeviceRow(
    val id: String,
    val name: String,
    val status: String,
    @SerialName("last_seen") val lastSeen: String? = null,
)

/** Payload for inserting a new command into `commands`. */
@Serializable
data class NewCommand(
    @SerialName("device_id") val deviceId: String,
    @SerialName("user_id") val userId: String,
    val prompt: String,
    val status: String = "queued",
)

/** A `commands` row including queue state. */
@Serializable
data class CommandRow(
    val id: String,
    @SerialName("device_id") val deviceId: String,
    @SerialName("user_id") val userId: String,
    val prompt: String,
    val status: String,
    @SerialName("error_message") val errorMessage: String? = null,
)

/** A `command_outputs` streaming chunk. */
@Serializable
data class OutputRow(
    @SerialName("command_id") val commandId: String,
    val chunk: String,
    val seq: Int,
)

/** A `screenshots` row with base64 PNG data. */
@Serializable
data class ScreenshotRow(
    val id: String,
    @SerialName("device_id") val deviceId: String,
    @SerialName("image_base64") val imageBase64: String,
    val width: Int = 1920,
    val height: Int = 1080,
)