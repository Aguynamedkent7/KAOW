package com.kaow.mobile.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.kaow.mobile.KaowApp
import com.kaow.mobile.data.remote.KaowSupabase
import com.kaow.mobile.ui.chat.ChatScreen
import com.kaow.mobile.ui.dashboard.DashboardScreen
import com.kaow.mobile.ui.login.LoginScreen
import com.kaow.mobile.ui.power.PowerScreen
import com.kaow.mobile.ui.theme.KaowTheme
import io.github.jan.supabase.auth.status.SessionStatus

/** Root composable: auth gate, then the three-tab shell. */
@Composable
fun KaowRoot() {
    KaowTheme {
        val app = LocalContext.current.applicationContext as KaowApp
        val auth = app.repositories.auth
        val status by auth.sessionStatus.collectAsStateWithLifecycle(initialValue = SessionStatus.Initializing)

        when {
            !KaowSupabase.isConfigured -> ConfigErrorScreen()
            status is SessionStatus.Authenticated -> HomeShell(app)
            status == SessionStatus.Initializing -> LoadingScreen()
            else -> LoginScreen(auth)
        }
    }
}

private data class Tab(val label: String, val icon: ImageVector)

private val tabs = listOf(
    Tab("Chat", Icons.Filled.Send),
    Tab("Dashboard", Icons.Filled.Home),
    Tab("Power", Icons.Filled.PlayArrow),
)

@Composable
private fun HomeShell(app: KaowApp) {
    var selected by rememberSaveable { mutableIntStateOf(0) }
    Scaffold(
        bottomBar = {
            NavigationBar {
                tabs.forEachIndexed { index, tab ->
                    NavigationBarItem(
                        selected = selected == index,
                        onClick = { selected = index },
                        icon = { Icon(tab.icon, contentDescription = tab.label) },
                        label = { Text(tab.label) },
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (selected) {
                0 -> ChatScreen(app)
                1 -> DashboardScreen(app)
                else -> PowerScreen()
            }
        }
    }
}