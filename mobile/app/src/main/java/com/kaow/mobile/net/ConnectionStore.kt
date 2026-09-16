package com.kaow.mobile.net

import android.content.Context

/** A paired-tailnet daemon endpoint plus its auth token. */
data class ConnectionConfig(val baseUrl: String, val authToken: String) {
    val webSocketUrl: String get() = "$baseUrl/ws?token=$authToken"
}

/** Persists the Tailscale pairing (base URL + token) in SharedPreferences. */
class ConnectionStore(context: Context) {
    private val prefs =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun load(): ConnectionConfig? {
        val base = prefs.getString(KEY_BASE, null) ?: return null
        val token = prefs.getString(KEY_TOKEN, null) ?: return null
        if (base.isBlank() || token.isBlank()) return null
        return ConnectionConfig(base, token)
    }

    fun save(config: ConnectionConfig) {
        prefs.edit()
            .putString(KEY_BASE, config.baseUrl)
            .putString(KEY_TOKEN, config.authToken)
            .apply()
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

    private companion object {
        const val PREFS_NAME = "kaow_pairing"
        const val KEY_BASE = "base_url"
        const val KEY_TOKEN = "auth_token"
    }
}