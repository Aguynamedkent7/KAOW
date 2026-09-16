package com.kaow.mobile

import android.app.Application
import com.kaow.mobile.net.ConnectionStore
import com.kaow.mobile.net.DirectRelay
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

/** Simplest DI: shared connection state hung off the Application. */
class KaowApp : Application() {
    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    lateinit var connectionStore: ConnectionStore
    lateinit var relay: DirectRelay

    override fun onCreate() {
        super.onCreate()
        connectionStore = ConnectionStore(this)
        relay = DirectRelay(connectionStore, appScope)
        if (connectionStore.load() != null) {
            relay.connect()
        }
    }
}