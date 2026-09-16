package com.kaow.mobile.ui.dashboard

import android.app.Application
import android.util.Base64
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.kaow.mobile.KaowApp
import com.kaow.mobile.net.ConnectionStatus
import com.kaow.mobile.net.DaemonEvent
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** View state for the dashboard screen. */
data class DashboardUiState(
    val connection: ConnectionStatus = ConnectionStatus.DISCONNECTED,
    val screenshotBytes: ByteArray? = null,
    val loading: Boolean = false,
    val error: String? = null,
) {
    override fun equals(other: Any?) = this === other
    override fun hashCode() = System.identityHashCode(this)
}

class DashboardViewModel(app: Application) : AndroidViewModel(app) {
    private val relay = (app as KaowApp).relay
    private val _ui = MutableStateFlow(DashboardUiState())
    val ui: StateFlow<DashboardUiState> = _ui.asStateFlow()

    init {
        viewModelScope.launch {
            relay.status.collect { status -> _ui.update { it.copy(connection = status) } }
        }
        viewModelScope.launch {
            relay.events.collect { event ->
                when (event) {
                    is DaemonEvent.Screenshot -> {
                        val bytes = withContext(Dispatchers.IO) { decodeBytes(event.imageBase64) }
                        if (bytes != null) _ui.update { it.copy(screenshotBytes = bytes) }
                    }
                    is DaemonEvent.Error -> _ui.update { it.copy(error = event.message) }
                    else -> Unit
                }
            }
        }
        refresh()
    }

    fun refresh() {
        if (_ui.value.connection != ConnectionStatus.CONNECTED) return
        viewModelScope.launch {
            _ui.update { it.copy(loading = true, error = null) }
            relay.sendScreenshotRequest()
            _ui.update { it.copy(loading = false) }
        }
    }

    private fun decodeBytes(base64: String): ByteArray? = runCatching {
        Base64.decode(base64, Base64.DEFAULT)
    }.getOrNull()
}