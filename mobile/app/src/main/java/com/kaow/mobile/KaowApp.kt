package com.kaow.mobile

import android.app.Application
import com.kaow.mobile.data.repository.AuthRepository
import com.kaow.mobile.data.repository.ChatRepository
import com.kaow.mobile.data.repository.DashboardRepository
import com.kaow.mobile.data.repository.DeviceRepository

/** Simplest DI: repositories are lazy singletons hung off the Application. */
class KaowApp : Application() {
    val repositories = Repositories()
}

class Repositories(
    val auth: AuthRepository = AuthRepository(),
    val devices: DeviceRepository = DeviceRepository(),
    val chat: ChatRepository = ChatRepository(),
    val dashboard: DashboardRepository = DashboardRepository(),
)