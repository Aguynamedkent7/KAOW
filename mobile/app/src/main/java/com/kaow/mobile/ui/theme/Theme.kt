package com.kaow.mobile.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val KaowDark = darkColorScheme(
    primary = Color(0xFF7FD8D9),
    onPrimary = Color(0xFF003738),
    secondary = Color(0xFF4EBDC0),
    background = Color(0xFF0F1314),
    surface = Color(0xFF171C1D),
    onBackground = Color(0xFFE0E2E3),
    onSurface = Color(0xFFE0E2E3),
    error = Color(0xFFFFB4AB),
)

@Composable
fun KaowTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = KaowDark,
        content = content,
    )
}