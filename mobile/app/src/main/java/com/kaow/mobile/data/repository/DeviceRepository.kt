package com.kaow.mobile.data.repository

import com.kaow.mobile.data.model.DeviceRow
import com.kaow.mobile.data.remote.KaowSupabase
import io.github.jan.supabase.postgrest.from

/** Device registry queries for the current user's PCs. */
class DeviceRepository {
    suspend fun listDevices(): List<DeviceRow> =
        KaowSupabase.client.from("devices").select().decodeList<DeviceRow>()

    suspend fun firstOnlineDevice(): DeviceRow? =
        listDevices().firstOrNull { it.status == "online" }

    suspend fun refreshStatus(deviceId: String): DeviceRow? =
        KaowSupabase.client.from("devices")
            .select { filter { eq("id", deviceId) } }
            .decodeList<DeviceRow>()
            .firstOrNull()
}