package com.kaow.mobile.data.repository

import com.kaow.mobile.data.remote.KaowSupabase
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.auth.providers.builtin.Email
import io.github.jan.supabase.auth.status.SessionStatus
import kotlinx.coroutines.flow.Flow

/** Auth against Supabase (anon key + RLS). */
class AuthRepository {
    val sessionStatus: Flow<SessionStatus> = KaowSupabase.client.auth.sessionStatus

    val currentUserId: String?
        get() = KaowSupabase.client.auth.currentUserOrNull()?.id

    suspend fun signIn(email: String, password: String) {
        KaowSupabase.client.auth.signInWith(Email) {
            this.email = email
            this.password = password
        }
    }

    suspend fun signOut() {
        KaowSupabase.client.auth.signOut()
    }
}