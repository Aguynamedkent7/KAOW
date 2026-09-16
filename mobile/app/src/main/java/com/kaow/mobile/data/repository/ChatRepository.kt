package com.kaow.mobile.data.repository

import com.kaow.mobile.data.model.CommandRow
import com.kaow.mobile.data.model.NewCommand
import com.kaow.mobile.data.model.OutputRow
import com.kaow.mobile.data.remote.KaowSupabase
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Order
import io.github.jan.supabase.realtime.PostgresAction
import io.github.jan.supabase.realtime.channel
import io.github.jan.supabase.realtime.decodeRecord
import io.github.jan.supabase.realtime.postgresChangeFlow
import io.github.jan.supabase.realtime.realtime
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.emitAll
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.mapNotNull

/** Command queue and transcript against the Supabase relay. */
class ChatRepository {
    suspend fun history(deviceId: String): List<CommandRow> =
        KaowSupabase.client.from("commands")
            .select {
                filter { eq("device_id", deviceId) }
                order(column = "created_at", order = Order.ASCENDING)
            }
            .decodeList<CommandRow>()

    suspend fun send(prompt: String, deviceId: String, userId: String): CommandRow {
        val command = NewCommand(deviceId = deviceId, userId = userId, prompt = prompt)
        return KaowSupabase.client.from("commands")
            .insert(command) { select() }
            .decodeSingle<CommandRow>()
    }

    /** Inserts + status updates of the user's commands. */
    fun observeCommands(deviceId: String): Flow<CommandRow> = flow {
        val channel = KaowSupabase.client.realtime.channel("kaow-commands")
        val source = channel.postgresChangeFlow<PostgresAction>("public") {
            table = "commands"
        }.mapNotNull { action ->
            when (action) {
                is PostgresAction.Insert,
                is PostgresAction.Update -> action.decodeRecord<CommandRow>()
                else -> null
            }
        }.filter { it.deviceId == deviceId }
        channel.subscribe()
        try {
            emitAll(source)
        } finally {
            channel.unsubscribe()
        }
    }

    /** Streaming output chunks for the user's commands. */
    fun observeOutputs(deviceId: String): Flow<OutputRow> = flow {
        val channel = KaowSupabase.client.realtime.channel("kaow-outputs")
        val source = channel.postgresChangeFlow<PostgresAction.Insert>("public") {
            table = "command_outputs"
        }.mapNotNull { action ->
            action.decodeRecord<OutputRow>()
        }
        channel.subscribe()
        try {
            emitAll(source)
        } finally {
            channel.unsubscribe()
        }
    }
}