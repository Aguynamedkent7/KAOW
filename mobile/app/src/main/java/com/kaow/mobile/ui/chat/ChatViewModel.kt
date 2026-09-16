package com.kaow.mobile.ui.chat

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.kaow.mobile.KaowApp
import com.kaow.mobile.data.model.Author
import com.kaow.mobile.data.model.ChatMessage
import com.kaow.mobile.data.model.TaskStatus
import com.kaow.mobile.net.ConnectionStatus
import com.kaow.mobile.net.DaemonEvent
import com.kaow.mobile.net.HistoryEntryDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** View state for the chat screen. */
data class ChatUiState(
    val connection: ConnectionStatus = ConnectionStatus.DISCONNECTED,
    val messages: List<ChatMessage> = emptyList(),
    val sending: Boolean = false,
    val error: String? = null,
)

class ChatViewModel(app: Application) : AndroidViewModel(app) {
    private val relay = (app as KaowApp).relay

    private val _ui = MutableStateFlow(ChatUiState())
    val ui: StateFlow<ChatUiState> = _ui.asStateFlow()

    private val outputByTask = mutableMapOf<String, StringBuilder>()
    private val promptByTask = mutableMapOf<String, String>()
    private var orderCounter = 0L

    init {
        viewModelScope.launch {
            relay.status.collect { status -> _ui.update { it.copy(connection = status) } }
        }
        viewModelScope.launch {
            relay.events.collect { event ->
                when (event) {
                    is DaemonEvent.CommandOutput -> onOutput(event)
                    is DaemonEvent.TaskQueued -> Unit
                    is DaemonEvent.Screenshot -> Unit
                    is DaemonEvent.Error -> onError(event)
                    is DaemonEvent.History -> rebuildFromHistory(event.entries)
                }
            }
        }
        viewModelScope.launch {
            if (relay.savedConfig() != null) {
                relay.requestHistory()
            }
        }
    }

    fun send(prompt: String) {
        val text = prompt.trim()
        if (text.isEmpty()) return
        if (_ui.value.connection != ConnectionStatus.CONNECTED) {
            _ui.update { it.copy(error = "Not connected to your PC") }
            return
        }
        val taskId = relay.sendCommand(text)
        promptByTask[taskId] = text
        outputByTask[taskId] = StringBuilder()
        upsert(taskId, Author.USER, text, TaskStatus.QUEUED)
        upsert(taskId, Author.ASSISTANT, "", TaskStatus.RUNNING)
        _ui.update { it.copy(error = null, sending = true) }
    }

    fun dismissError() {
        _ui.update { it.copy(error = null) }
    }

    private fun onOutput(event: DaemonEvent.CommandOutput) {
        val buffer = outputByTask.getOrPut(event.taskId) { StringBuilder() }
        if (event.stream.isNotEmpty()) {
            buffer.append(event.stream)
        }
        val status = if (event.done) {
            TaskStatus.fromDb(event.status.orEmpty())
        } else {
            TaskStatus.RUNNING
        }
        upsert(event.taskId, Author.ASSISTANT, buffer.toString(), status)
        if (event.done) {
            upsert(event.taskId, Author.USER, promptByTask[event.taskId].orEmpty(), status)
            _ui.update { it.copy(sending = false) }
        }
    }

    private fun onError(event: DaemonEvent.Error) {
        _ui.update { it.copy(error = event.message) }
        event.taskId?.let { taskId ->
            val status = TaskStatus.FAILED
            upsert(taskId, Author.ASSISTANT, outputByTask[taskId].toString(), status)
            upsert(taskId, Author.USER, promptByTask[taskId].orEmpty(), status)
        }
    }

    private fun rebuildFromHistory(entries: List<HistoryEntryDto>) {
        if (entries.isEmpty()) return
        val built = entries.flatMap { entry ->
            val status = TaskStatus.fromDb(entry.status)
            listOf(
                ChatMessage(orderCounter++, entry.taskId, Author.USER, entry.prompt, status),
                ChatMessage(orderCounter++, entry.taskId, Author.ASSISTANT, entry.output, status),
            )
        }
        _ui.update { it.copy(messages = built) }
    }

    private fun upsert(taskId: String, author: Author, text: String, status: TaskStatus?) {
        _ui.update { state ->
            val index = state.messages.indexOfFirst { it.taskId == taskId && it.author == author }
            val messages = if (index >= 0) {
                val current = state.messages[index]
                state.messages.toMutableList().apply {
                    set(index, current.copy(text = text, status = status))
                }
            } else {
                state.messages + ChatMessage(
                    order = orderCounter++,
                    taskId = taskId,
                    author = author,
                    text = text,
                    status = status,
                )
            }
            state.copy(messages = messages)
        }
    }
}