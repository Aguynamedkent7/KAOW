package com.kaow.mobile.ui.dashboard

import android.app.Application
import android.util.Base64
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.kaow.mobile.KaowApp
import com.kaow.mobile.data.model.DeviceRow
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** View state for the dashboard screen. */
data class DashboardUiState(
    val device: DeviceRow? = null,
    val screenshotBytes: ByteArray? = null,
    val error: String? = null,
) {
    override fun equals(other: Any?) = this === other
    override fun hashCode() = System.identityHashCode(this)
}

class DashboardViewModel(app: Application) : AndroidViewModel(app) {
    private val graph = (app as KaowApp).repositories
    private val _ui = MutableStateFlow(DashboardUiState())
    val ui: StateFlow<DashboardUiState> = _ui.asStateFlow()

    init {
        connect()
    }

    fun refresh() {
        val device = _ui.value.device ?: return
        viewModelScope.launch {
            _ui.update { it.copy(error = null) }
            loadScreenshot(device.id)
        }
    }

    private fun connect() {
        viewModelScope.launch {
            _ui.update { it.copy(error = null) }
            val device = try {
                graph.devices.firstOnlineDevice()
            } catch (e: Exception) {
                _ui.update { it.copy(error = "Failed to load device: ${e.message}") }
                return@launch
            }
            if (device == null) {
                _ui.update { it.copy(error = "No online device found - start the daemon relay") }
                return@launch
            }
            _ui.update { it.copy(device = device) }
            loadScreenshot(device.id)
            observeLive(device.id)
        }
    }

    private suspend fun loadScreenshot(deviceId: String) {
        val shot = try {
            graph.dashboard.latestScreenshot(deviceId)
        } catch (e: Exception) {
            _ui.update { it.copy(error = "Failed to load screenshot: ${e.message}") }
            null
        }
        if (shot != null) {
            val bytes = withContext(Dispatchers.IO) { decodeBytes(shot.imageBase64) }
            _ui.update { it.copy(screenshotBytes = bytes) }
        }
    }

    private fun observeLive(deviceId: String) {
        viewModelScope.launch {
            graph.dashboard.observeScreenshots(deviceId).collect { shot ->
                val bytes = withContext(Dispatchers.IO) { decodeBytes(shot.imageBase64) }
                _ui.update { it.copy(screenshotBytes = bytes) }
            }
        }
    }

    private fun decodeBytes(base64: String): ByteArray? = runCatching {
        Base64.decode(base64, Base64.DEFAULT)
    }.getOrNull()
}