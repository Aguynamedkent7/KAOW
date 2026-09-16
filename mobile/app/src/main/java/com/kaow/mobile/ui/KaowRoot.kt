package com.kaow.mobile.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.kaow.mobile.KaowApp
import com.kaow.mobile.net.ConnectionStatus
import com.kaow.mobile.ui.chat.ChatScreen
import com.kaow.mobile.ui.dashboard.DashboardScreen
import com.kaow.mobile.ui.pair.PairScreen
import com.kaow.mobile.ui.power.PowerScreen
import com.kaow.mobile.ui.theme.KaowTheme

/** Root composable: pairing gate, then the three-tab shell. */
@Composable
fun KaowRoot() {
    KaowTheme {
        val app = LocalContext.current.applicationContext as KaowApp
        val hasPairing = app.connectionStore.load() != null
        if (hasPairing) {
            HomeShell(app)
        } else {
            PairScreen(app)
        }
    }
}

private data class Tab(val label: String, val icon: ImageVector)

private val tabs = listOf(
    Tab("Chat", Icons.AutoMirrored.Filled.Send),
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
        Column(Modifier.fillMaxSize().padding(padding)) {
            ConnectionBar(app)
            Box(Modifier.weight(1f)) {
                when (selected) {
                    0 -> ChatScreen(app)
                    1 -> DashboardScreen(app)
                    else -> PowerScreen()
                }
            }
        }
    }
}

@Composable
private fun ConnectionBar(app: KaowApp) {
    val status by app.relay.status.collectAsStateWithLifecycle()
    if (status != ConnectionStatus.FAILED) return
    Surface(color = MaterialTheme.colorScheme.errorContainer) {
        Column(Modifier.fillMaxWidth().padding(10.dp)) {
            Text(
                text = if (app.connectionStore.load() != null) {
                    "Can't reach your PC. Is it on? Is Tailscale running?"
                } else {
                    "Not paired yet."
                },
                color = MaterialTheme.colorScheme.onErrorContainer,
                style = MaterialTheme.typography.bodyMedium,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(Modifier.padding(top = 6.dp)) {
                Button(
                    onClick = { app.relay.connect() },
                    modifier = Modifier.weight(1f).padding(end = 6.dp),
                ) {
                    Text("Retry")
                }
                OutlinedButton(
                    onClick = { app.relay.forget() },
                    modifier = Modifier.weight(1f),
                ) {
                    Text("Re-pair")
                }
            }
        }
    }
}