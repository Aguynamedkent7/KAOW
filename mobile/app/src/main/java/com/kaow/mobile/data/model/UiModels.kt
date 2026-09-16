package com.kaow.mobile.data.model

/** Mirror of the daemon task statuses (see docs/API.md). */
enum class TaskStatus(val dbValue: String) {
    QUEUED("queued"),
    RUNNING("running"),
    COMPLETED("completed"),
    FAILED("failed"),
    KILLED("killed"),
    UNKNOWN("unknown");

    companion object {
        fun fromDb(value: String): TaskStatus =
            entries.firstOrNull { it.dbValue == value } ?: UNKNOWN
    }
}

enum class Author { USER, ASSISTANT }

/** A single row in the chat transcript. */
data class ChatMessage(
    val order: Long,
    val taskId: String?,
    val author: Author,
    val text: String,
    val status: TaskStatus?,
)