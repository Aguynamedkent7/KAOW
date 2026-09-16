package com.kaow.mobile.data.remote

import com.kaow.mobile.BuildConfig
import io.github.jan.supabase.auth.Auth
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.realtime.Realtime
import kotlinx.serialization.json.Json

/** Entry point for the shared Supabase client. */
object KaowSupabase {
    val isConfigured: Boolean
        get() = BuildConfig.SUPABASE_URL.isNotBlank() && BuildConfig.SUPABASE_ANON_KEY.isNotBlank()

    /** JSON used for decoding realtime records. */
    val json: Json = Json { ignoreUnknownKeys = true }

    val client by lazy {
        check(isConfigured) {
            "Supabase not configured - build with -PKAOW_MOBILE_SUPABASE_URL and -PKAOW_MOBILE_SUPABASE_ANON_KEY"
        }
        createSupabaseClient(BuildConfig.SUPABASE_URL, BuildConfig.SUPABASE_ANON_KEY) {
            install(Auth)
            install(Postgrest)
            install(Realtime)
        }
    }
}