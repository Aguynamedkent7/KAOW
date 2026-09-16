package com.kaow.mobile.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.kaow.mobile.KaowApp
import com.kaow.mobile.data.model.Author
import com.kaow.mobile.data.model.ChatMessage
import com.kaow.mobile.data.model.CommandRow
import com.kaow.mobile.data.model.DeviceRow
import com.kaow.mobile.data.model.OutputRow
import com.kaow.mobile.data.model.TaskStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** View state for the chat screen. */
data class ChatUiState(
    val device: DeviceRow? = null,
    val messages: List<ChatMessage> = emptyList(),
    val sending: Boolean = false,
    val error: String? = null,
)

class ChatViewModel(app: Application) : AndroidViewModel(app) {
    private val graph = (app as KaowApp).repositories

    private val _ui = MutableStateFlow(ChatUiState())
    val ui: StateFlow<ChatUiState> = _ui.asStateFlow()

    private val commandById = mutableMapOf<String, CommandRow>()
    private val outputByCommand = mutableMapOf<String, StringBuilder>()
    private var orderCounter = 0L

    init {
        connect()
    }

    fun send(prompt: String) {
        val text = prompt.trim()
        if (text.isEmpty()) return
        val device = _ui.value.device
        val userId = graph.auth.currentUserId
        if (device == null) {
            _ui.update { it.copy(error = "No device connected - start the daemon relay") }
            return
        }
        if (userId == null) {
            _ui.update { it.copy(error = "Not signed in") }
            return
        }
        if (_ui.value.sending) return
        viewModelScope.launch {
            _ui.update { it.copy(sending = true, error = null) }
            try {
                val command = graph.chat.send(text, device.id, userId)
                onCommand(command)
            } catch (e: Exception) {
                _ui.update { it.copy(error = "Failed to send: ${e.message}") }
            } finally {
                _ui.update { it.copy(sending = false) }
            }
        }
    }

    fun dismissError() {
        _ui.update { it.copy(error = null) }
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
            loadHistory(device.id)
            observeLive(device.id)
        }
    }

    private suspend fun loadHistory(deviceId: String) {
        val commands = try {
            graph.chat.history(deviceId)
        } catch (e: Exception) {
            _ui.update { it.copy(error = "Failed to load chat history: ${e.message}") }
            return
        }
        commands.forEach { onCommand(it) }
    }

    private fun observeLive(deviceId: String) {
        viewModelScope.launch {
            graph.chat.observeCommands(deviceId).collect { onCommand(it) }
        }
        viewModelScope.launch {
            graph.chat.observeOutputs(deviceId).collect { onOutput(it) }
        }
    }

    private fun onCommand(command: CommandRow) {
        val wasKnown = commandById.containsKey(command.id)
        commandById[command.id] = command
        val status = TaskStatus.fromDb(command.status)
        upsert(command.id, Author.USER, command.prompt, status)
        if (wasKnown) {
            val hasAssistant =
                _ui.value.messages.any { it.commandId == command.id && it.author == Author.ASSISTANT }
            if (hasAssistant) {
                upsert(command.id, Author.ASSISTANT, outputByCommand[command.id]?.toString().orEmpty(), status)
            }
        }
    }

    private fun onOutput(output: OutputRow) {
        val buffer = outputByCommand.getOrPut(output.commandId) { StringBuilder() }
        buffer.append(output.chunk)
        val status = commandById[output.commandId]
            ?.let { TaskStatus.fromDb(it.status) }
            ?: TaskStatus.RUNNING
        upsert(output.commandId, Author.ASSISTANT, buffer.toString(), status)
    }

    private fun upsert(commandId: String?, author: Author, text: String, status: TaskStatus?) {
        _ui.update { state ->
            val index = state.messages.indexOfFirst { it.commandId == commandId && it.author == author }
            val messages = if (index >= 0) {
                val current = state.messages[index]
                state.messages.toMutableList().apply {
                    set(index, current.copy(text = text, status = status))
                }
            } else {
                state.messages + ChatMessage(
                    order = orderCounter++,
                    commandId = commandId,
                    author = author,
                    text = text,
                    status = status,
                )
            }
            state.copy(messages = messages)
        }
    }
}