package com.kaow.mobile.ui.pair

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import com.kaow.mobile.KaowApp
import com.kaow.mobile.net.ConnectionConfig

/** Parses the `ws://<host>:<port>/ws?token=...` string produced by `kaow pair`. */
object PairingCode {
    fun parse(text: String): ConnectionConfig? {
        val trimmed = text.trim()
        val uri = runCatching { Uri.parse(trimmed) }.getOrNull() ?: return null
        if (uri.scheme != "ws" && uri.scheme != "wss") return null
        val host = uri.host ?: return null
        val base = if (uri.port > 0) {
            "${uri.scheme}://$host:${uri.port}"
        } else {
            "${uri.scheme}://$host"
        }
        val token = uri.getQueryParameter("token") ?: return null
        if (token.isBlank()) return null
        return ConnectionConfig(base, token)
    }

    /** Build a pairing string from manual-entry values. */
    fun build(baseUrl: String, token: String): String =
        "${baseUrl.trim().trimEnd('/')}/ws?token=${token.trim()}"
}

/** First-run screen: scan the daemon QR code or enter the address manually. */
@Composable
fun PairScreen(app: KaowApp) {
    var manual by rememberSaveable { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    val scanLauncher = rememberLauncherForActivityResult(ScanContract()) { result ->
        val contents = result.contents
        if (contents == null) {
            error = "Scan cancelled"
        } else if (PairingCode.parse(contents) != null) {
            PairingCode.parse(contents)?.let { app.relay.connectWith(it) }
        } else {
            error = "That QR code is not a KAOW pairing code"
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text("KAOW", style = MaterialTheme.typography.displayMedium)
        Text(
            "Pair with your PC over Tailscale",
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(top = 4.dp, bottom = 24.dp),
            textAlign = TextAlign.Center,
        )
        Button(
            onClick = {
                val options = ScanOptions()
                options.setDesiredBarcodeFormats(ScanOptions.QR_CODE)
                options.setPrompt("Scan the QR shown by `kaow pair` on your PC")
                scanLauncher.launch(options)
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Scan QR code")
        }
        OutlinedButton(
            onClick = { manual = !manual },
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        ) {
            Text(if (manual) "Scan instead" else "Enter address manually")
        }
        if (manual) {
            ManualEntry(
                onPair = { app.relay.connectWith(it) },
                onInvalid = { error = it },
                modifier = Modifier.padding(top = 16.dp),
            )
        }
        error?.let {
            Text(
                text = it,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 12.dp),
            )
        }
        Surface(color = MaterialTheme.colorScheme.surfaceVariant) {
            Text(
                text = "Run `kaow pair` on your PC. Both devices must be on the same " +
                    "Tailscale network.",
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(12.dp),
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun ManualEntry(
    onPair: (ConnectionConfig) -> Unit,
    onInvalid: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var baseUrl by rememberSaveable { mutableStateOf("") }
    var token by rememberSaveable { mutableStateOf("") }
    val canSubmit = baseUrl.isNotBlank() && token.isNotBlank()

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Or type what the QR contains", style = MaterialTheme.typography.titleSmall)
        OutlinedTextField(
            value = baseUrl,
            onValueChange = { baseUrl = it },
            label = { Text("Base URL") },
            placeholder = { Text("ws://100.64.1.7:8765") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = token,
            onValueChange = { token = it },
            label = { Text("Auth token") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            onClick = {
                val config = PairingCode.parse(PairingCode.build(baseUrl, token))
                if (config == null) onInvalid("Enter a valid base URL and token") else onPair(config)
            },
            enabled = canSubmit,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Connect")
        }
    }
}