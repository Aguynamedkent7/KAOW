package com.kaow.mobile.ui.dashboard

import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.kaow.mobile.KaowApp
import com.kaow.mobile.net.ConnectionStatus
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun DashboardScreen(app: KaowApp, viewModel: DashboardViewModel = viewModel()) {
    val ui by viewModel.ui.collectAsState()
    var bitmap by remember { mutableStateOf<ImageBitmap?>(null) }

    LaunchedEffect(ui.screenshotBytes) {
        val raw = ui.screenshotBytes
        if (raw != null) {
            val bmp = withContext(Dispatchers.IO) {
                BitmapFactory.decodeByteArray(raw, 0, raw.size)
            }
            bitmap = bmp?.asImageBitmap()
        } else {
            bitmap = null
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        ui.error?.let {
            Text(text = it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("Device", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(8.dp))
                Text(
                    when (ui.connection) {
                        ConnectionStatus.CONNECTED -> "Connected"
                        ConnectionStatus.CONNECTING -> "Connecting…"
                        ConnectionStatus.FAILED -> "Unreachable - check Tailscale"
                        ConnectionStatus.DISCONNECTED -> "Not paired"
                    },
                    style = MaterialTheme.typography.bodyLarge,
                )
                IconButton(
                    onClick = { viewModel.refresh() },
                    enabled = ui.connection == ConnectionStatus.CONNECTED && !ui.loading,
                    modifier = Modifier.align(Alignment.End),
                ) {
                    if (ui.loading) {
                        CircularProgressIndicator(modifier = Modifier.padding(8.dp))
                    } else {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh screenshot")
                    }
                }
            }
        }
        Card(Modifier.fillMaxWidth().weight(1f)) {
            if (bitmap != null) {
                Image(bitmap = bitmap!!, contentDescription = "Live screenshot", modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
            } else {
                Text("No screenshot yet", modifier = Modifier.padding(16.dp), style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}