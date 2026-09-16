package com.kaow.mobile.net

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.decodeFromJsonElement
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put

/** JSON instance tolerant of daemon fields this app does not yet know about. */
private val ProtocolJson: Json = Json { ignoreUnknownKeys = true }

/** One transcript entry returned by the daemon's history result. */
@Serializable
data class HistoryEntryDto(
    @SerialName("task_id") val taskId: String,
    val prompt: String,
    val status: String,
    @SerialName("created_at") val createdAt: String,
    val output: String,
)

/** Events emitted by [DirectRelay], mirroring the daemon protocol (docs/API.md). */
sealed interface DaemonEvent {
    data class CommandOutput(
        val taskId: String,
        val stream: String,
        val done: Boolean,
        val status: String?,
    ) : DaemonEvent

    data class TaskQueued(val taskId: String) : DaemonEvent
    data class Screenshot(val imageBase64: String) : DaemonEvent
    data class Error(val message: String, val code: String, val taskId: String?) : DaemonEvent
    data class History(val entries: List<HistoryEntryDto>) : DaemonEvent
}

/** Encode/parse the daemon WebSocket message envelope. */
object DaemonProtocol {
    /** Parse one daemon frame into a [DaemonEvent], returning null for unknown frames. */
    fun parse(raw: String): DaemonEvent? {
        val root = runCatching { ProtocolJson.parseToJsonElement(raw).jsonObject }.getOrNull()
            ?: return null
        val type = root["type"]?.jsonPrimitive?.content ?: return null
        val payload = root["payload"]?.jsonObject ?: JsonObject(emptyMap())
        val t = payload["task_id"]?.jsonPrimitive?.content
        return when (type) {
            "task_queued" -> DaemonEvent.TaskQueued(t.orEmpty())
            "command_output" -> DaemonEvent.CommandOutput(
                taskId = t.orEmpty(),
                stream = payload["stream"]?.jsonPrimitive?.content.orEmpty(),
                done = payload["done"]?.jsonPrimitive?.content == "true",
                status = payload["status"]?.jsonPrimitive?.content,
            )
            "screenshot" -> DaemonEvent.Screenshot(
                imageBase64 = payload["image"]?.jsonPrimitive?.content.orEmpty()
            )
            "error" -> DaemonEvent.Error(
                message = payload["message"]?.jsonPrimitive?.content.orEmpty(),
                code = payload["code"]?.jsonPrimitive?.content.orEmpty(),
                taskId = t,
            )
            "history_result" -> DaemonEvent.History(
                runCatching {
                    ProtocolJson
                        .decodeFromJsonElement<HistoryResultDto>(payload)
                        .entries
                }.getOrDefault(emptyList())
            )
            else -> null
        }
    }

    /** Build a client-to-daemon envelope as a JSON string. */
    fun envelope(messageType: String, payload: Map<String, Any?> = emptyMap()): String {
        val payloadObject = buildJsonObject {
            payload.forEach { (key, value) ->
                when (value) {
                    is String -> put(key, value)
                    is Int -> put(key, value)
                    is Long -> put(key, value)
                    is Boolean -> put(key, value)
                    null -> Unit
                    else -> put(key, value.toString())
                }
            }
        }
        return ProtocolJson.encodeToString(
            Envelope.serializer(),
            Envelope(type = messageType, payload = payloadObject),
        )
    }
}

@Serializable
private data class Envelope(val type: String, val payload: JsonObject)

@Serializable
private data class HistoryResultDto(val entries: List<HistoryEntryDto> = emptyList())