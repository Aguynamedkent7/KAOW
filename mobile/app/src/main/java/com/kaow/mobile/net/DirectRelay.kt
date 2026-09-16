package com.kaow.mobile.net

import android.util.Log
import io.ktor.client.HttpClient
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.websocket.WebSockets
import io.ktor.client.plugins.websocket.webSocket
import io.ktor.websocket.Frame
import io.ktor.websocket.WebSocketSession
import io.ktor.websocket.readText
import java.util.UUID
import kotlin.math.min
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/** Connection lifecycle state surfaced to the UI. */
enum class ConnectionStatus { DISCONNECTED, CONNECTING, CONNECTED, FAILED }

/**
 * Owns the WebSocket to the PC daemon over the tailnet, reconnecting on failure
 * and emitting parsed [DaemonEvent]s for the UI layer.
 */
class DirectRelay(
    private val store: ConnectionStore,
    private val scope: CoroutineScope,
) {
    private val client = HttpClient(OkHttp) {
        install(WebSockets)
    }

    private val _status = MutableStateFlow(ConnectionStatus.DISCONNECTED)
    val status: StateFlow<ConnectionStatus> = _status.asStateFlow()

    private val _events = MutableSharedFlow<DaemonEvent>(extraBufferCapacity = 256)
    val events: SharedFlow<DaemonEvent> = _events.asSharedFlow()

    private var session: WebSocketSession? = null
    private var loopJob: Job? = null

    fun savedConfig(): ConnectionConfig? = store.load()

    /** Persist a new QR pairing and connect immediately. */
    fun connectWith(config: ConnectionConfig) {
        store.save(config)
        connect()
    }

    /** Drop the pairing; returns to the scan/manual-entry screen. */
    fun forget() {
        store.clear()
        disconnect()
    }

    fun connect() {
        if (store.load() == null) return
        loopJob?.cancel()
        loopJob = scope.launch {
            var attempt = 0
            while (isActive) {
                _status.value = ConnectionStatus.CONNECTING
                try {
                    client.webSocket(urlString = store.load()!!.webSocketUrl) {
                        session = this
                        attempt = 0
                        _status.value = ConnectionStatus.CONNECTED
                        for (frame in incoming) {
                            if (frame is Frame.Text) {
                                DaemonProtocol.parse(frame.readText())?.let { _events.tryEmit(it) }
                            }
                        }
                    }
                    session = null
                    _status.value = ConnectionStatus.DISCONNECTED
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    Log.w("DirectRelay", "websocket failed", e)
                    session = null
                    attempt += 1
                    _status.value = ConnectionStatus.FAILED
                }
                if (!isActive) break
                delay(1000L * min(attempt.toLong(), 8L))
            }
        }
    }

    fun disconnect() {
        loopJob?.cancel()
        loopJob = null
        session = null
        _status.value = ConnectionStatus.DISCONNECTED
    }

    /** Queue a command; returns the client-generated task id used for correlation. */
    fun sendCommand(prompt: String): String {
        val taskId = UUID.randomUUID().toString()
        send(DaemonProtocol.envelope("command", mapOf("prompt" to prompt, "task_id" to taskId)))
        return taskId
    }

    fun sendScreenshotRequest() {
        send(DaemonProtocol.envelope("screenshot_request"))
    }

    fun requestHistory(limit: Int = 50) {
        send(DaemonProtocol.envelope("history", mapOf("limit" to limit)))
    }

    private fun send(text: String) {
        val session = session
        if (session == null) {
            Log.w("DirectRelay", "send ignored: not connected")
            return
        }
        scope.launch { runCatching { session.send(Frame.Text(text)) } }
    }
}