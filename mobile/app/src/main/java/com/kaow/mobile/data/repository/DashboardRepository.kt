package com.kaow.mobile.data.repository

import com.kaow.mobile.data.model.ScreenshotRow
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

/** Live screenshot feed from the daemon. */
class DashboardRepository {
    suspend fun latestScreenshot(deviceId: String): ScreenshotRow? =
        KaowSupabase.client.from("screenshots")
            .select {
                filter { eq("device_id", deviceId) }
                order(column = "created_at", order = Order.DESCENDING)
                limit(count = 1)
            }
            .decodeList<ScreenshotRow>()
            .firstOrNull()

    /** New screenshots pushed by the daemon over realtime. */
    fun observeScreenshots(deviceId: String): Flow<ScreenshotRow> = flow {
        val channel = KaowSupabase.client.realtime.channel("kaow-screenshots")
        val source = channel.postgresChangeFlow<PostgresAction.Insert>("public") {
            table = "screenshots"
        }.mapNotNull { action ->
            action.decodeRecord<ScreenshotRow>()
        }.filter { it.deviceId == deviceId }
        channel.subscribe()
        try {
            emitAll(source)
        } finally {
            channel.unsubscribe()
        }
    }
}