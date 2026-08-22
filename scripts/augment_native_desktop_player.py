#!/usr/bin/env python3
"""Augment a generated NuvioDesktop corpus test with the production player surface.

Human-UX invariant: provider output is handed to NuvioDesktop's real
PlatformPlayerSurface. The lab does not construct NativePlayerController directly,
does not sanitize/rewrite the stream itself and does not choose decoder/network
settings. Whatever Nuvio's production player does with the source is the evidence.
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

IMPORT_ANCHOR = "import com.nuvio.app.features.plugins.runtime.PluginRuntime\n"
TEST_ANCHOR = "    @Test\n"
DEFAULT_PR_STREAM_LIMIT = 2

IMPORTS = """import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.awt.ComposePanel
import com.nuvio.app.core.ui.NuvioTheme
import com.nuvio.app.features.player.PlatformPlayerSurface
import com.nuvio.app.features.player.PlayerControlsState
import com.nuvio.app.features.player.PlayerPlaybackSnapshot
import com.nuvio.app.features.player.PlayerResizeMode
import java.awt.BorderLayout
import java.awt.Rectangle
import java.awt.Robot
import java.awt.Toolkit
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import javax.imageio.ImageIO
import javax.swing.JFrame
import javax.swing.SwingUtilities
"""

HELPERS = r'''
    data class DesktopNativePlayerProbe(
        val state: String,
        val errorClass: String,
        val errorCode: String,
        val httpStatus: Int,
        val failureStage: String,
        val durationSeconds: Double?,
        val positionSeconds: Double?,
        val exceptionChain: String = "",
    )

    private fun desktopThrowableChain(error: Throwable): Pair<Throwable, String> {
        var current = error
        val parts = mutableListOf<String>()
        repeat(8) {
            val name = current::class.qualifiedName.orEmpty().ifBlank { current.javaClass.name }
            val message = current.message.orEmpty()
                .replace(Regex("https?://\\S+", RegexOption.IGNORE_CASE), "<url>")
                .replace(Regex("(?i)(authorization|cookie|token|secret)\\s*[:=]\\s*\\S+"), "$1=<redacted>")
                .replace(Regex("\\s+"), " ")
                .take(180)
            parts += if (message.isBlank()) name else "$name:$message"
            val next = when (current) {
                is java.lang.reflect.InvocationTargetException -> current.targetException ?: current.cause
                else -> current.cause
            }
            if (next == null || next === current) {
                return current to parts.joinToString(" -> ").take(420)
            }
            current = next
        }
        return current to parts.joinToString(" -> ").take(420)
    }

    private fun captureDesktopPhase(phase: String, fixtureSlug: String) {
        val safe = phase.replace(Regex("[^A-Za-z0-9_.-]+"), "-").trim('-').ifBlank { "phase" }
        val dir = File(workspace, "native-evidence/desktop/${System.getProperty("os.name").lowercase().replace(Regex("[^a-z0-9]+"), "-")}/$fixtureSlug")
        dir.mkdirs()
        val target = File(dir, "$safe.png")
        try {
            val size = Toolkit.getDefaultToolkit().screenSize
            val image = Robot().createScreenCapture(Rectangle(size))
            ImageIO.write(image, "png", target)
            emit("FIELD_NATIVE_FRONTEND_CAPTURE client=desktop phase=$safe screenshot64=${b64(target.absolutePath)} bytes=${target.length()}")
        } catch (error: Throwable) {
            emit("FIELD_NATIVE_FRONTEND_ERROR client=desktop phase=$safe error_class64=${b64(error::class.qualifiedName.orEmpty())}")
        }
    }

    private fun probeDesktopProductionPlayer(
        url: String,
        headers: Map<String, String>?,
        streamType: String?,
        expectedDurationMinutes: Int,
    ): DesktopNativePlayerProbe {
        val frameRef = AtomicReference<JFrame?>(null)
        val latestSnapshot = AtomicReference<PlayerPlaybackSnapshot?>(null)
        val errorRef = AtomicReference<String?>(null)
        val terminal = CountDownLatch(1)
        try {
            SwingUtilities.invokeAndWait {
                val frame = JFrame("Nuvio Desktop native reader lab")
                val panel = ComposePanel()
                frame.layout = BorderLayout()
                frame.add(panel, BorderLayout.CENTER)
                frame.setSize(960, 540)
                frame.setLocationRelativeTo(null)
                frame.defaultCloseOperation = JFrame.DISPOSE_ON_CLOSE
                frameRef.set(frame)
                panel.setContent {
                    // PlatformPlayerSurface assumes the same production composition
                    // locals as a normal Nuvio app screen. In particular the current
                    // Desktop implementation reads LocalNuvioPlatformDensity, whose
                    // deliberate default throws outside NuvioTheme. Keep the real
                    // theme around the real surface instead of inventing test values.
                    NuvioTheme {
                        PlatformPlayerSurface(
                            sourceUrl = url,
                            sourceHeaders = headers.orEmpty(),
                            sourceResponseHeaders = emptyMap(),
                            externalSubtitles = emptyList(),
                            streamType = streamType,
                            useYoutubeChunkedPlayback = false,
                            modifier = Modifier.fillMaxSize(),
                            playWhenReady = true,
                            initialPositionMs = 0L,
                            initialPositionRequestKey = "niakvio-native-reader",
                            resizeMode = PlayerResizeMode.Fit,
                            useNativeController = true,
                            playerControlsState = PlayerControlsState(),
                            onControllerReady = { _ -> },
                            onSnapshot = { snapshot ->
                                latestSnapshot.set(snapshot)
                                if (snapshot.isEnded || (!snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L))) {
                                    terminal.countDown()
                                }
                            },
                            onError = { message ->
                                if (!message.isNullOrBlank()) {
                                    errorRef.compareAndSet(null, message)
                                    terminal.countDown()
                                }
                            },
                        )
                    }
                }
                frame.isVisible = true
            }

            terminal.await(__READER_TIMEOUT_MS__L, TimeUnit.MILLISECONDS)
            val error = errorRef.get()
            val snapshot = latestSnapshot.get()
            if (!error.isNullOrBlank()) {
                return DesktopNativePlayerProbe(
                    "error", "NuvioDesktopProductionPlayer",
                    error.replace(Regex("\\s+"), "_").take(160),
                    0, "player", null, null,
                )
            }
            val durationSeconds = snapshot?.durationMs?.takeIf { it > 0L }?.div(1000.0)
            val positionSeconds = snapshot?.positionMs?.takeIf { it >= 0L }?.div(1000.0)
            val expected = expectedDurationMinutes.takeIf { it > 0 }?.times(60.0)
            val shortMedia = durationSeconds != null && (
                durationSeconds < 60.0 || (expected != null && durationSeconds / expected < 0.55)
            )
            if (shortMedia) {
                return DesktopNativePlayerProbe("short_media", "", "", 0, "duration_identity", durationSeconds, positionSeconds)
            }
            if (snapshot?.isEnded == true) {
                return DesktopNativePlayerProbe("ended", "", "", 0, "none", durationSeconds, positionSeconds)
            }
            if (snapshot != null && !snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L)) {
                return DesktopNativePlayerProbe("ready", "", "", 0, "none", durationSeconds, positionSeconds)
            }
            return DesktopNativePlayerProbe("timeout", "NuvioDesktopProductionPlayer", "READER_TIMEOUT", 0, "timeout", durationSeconds, positionSeconds)
        } catch (error: Throwable) {
            val (root, chain) = desktopThrowableChain(error)
            val rootMessage = root.message.orEmpty().ifBlank { "PLAYER_SETUP" }
            return DesktopNativePlayerProbe(
                "error", root::class.qualifiedName.orEmpty().ifBlank { root.javaClass.name },
                rootMessage.replace(Regex("\\s+"), "_").take(160),
                0, "player_setup", null, null, chain,
            )
        } finally {
            runCatching { SwingUtilities.invokeAndWait { frameRef.getAndSet(null)?.dispose() } }
        }
    }
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"desktop reader anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def augment(path: Path, expected_minutes: int, stream_scope: str) -> None:
    text = path.read_text(encoding="utf-8")
    if "probeDesktopProductionPlayer" in text:
        return
    pr_bounded = os.environ.get("GITHUB_EVENT_NAME", "").strip().lower() == "pull_request"
    if pr_bounded and stream_scope == "all":
        configured = os.environ.get("NIAKVIO_PR_STREAM_LIMIT", str(DEFAULT_PR_STREAM_LIMIT)).strip()
        try:
            stream_scope = str(max(1, min(int(configured), 4)))
        except ValueError:
            stream_scope = str(DEFAULT_PR_STREAM_LIMIT)
    reader_timeout_ms = 12_000 if pr_bounded else 25_000

    text = replace_once(text, IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORTS, "imports")
    helpers = HELPERS.replace("__READER_TIMEOUT_MS__", str(reader_timeout_ms))
    text = replace_once(text, TEST_ANCHOR, helpers + "\n" + TEST_ANCHOR, "test")

    if stream_scope == "all":
        text = re.sub(r"rows\.take\(\d+\)\.forEachIndexed", "rows.forEachIndexed", text)
        reader_iter = "rows.forEachIndexed"
    else:
        count = max(1, min(int(stream_scope), 4))
        reader_iter = f"rows.take({count}).forEachIndexed"

    transport_pattern = re.compile(
        r'''                rows\.firstOrNull\(\)\?\.let \{ row ->\n'''
        r'''                    val probe = probeTransport\(row\.url, row\.headers\)\n'''
        r'''                    emit\("FIELD_NATIVE_TRANSPORT client=desktop fixture=\$fixtureSlug provider64=\$\{b64\(provider\.id\)\} request_type=\$requestMediaType route_mode=\$routeMode state=\$\{probe\.state\} kind=\$\{probe\.kind\} status=\$\{probe\.status\} content_type64=\$\{b64\(probe\.contentType\)\} extm3u=\$\{probe\.extm3u\} duration_seconds=\$\{probe\.durationSeconds \?: 0\.0\} host64=\$\{b64\(probe\.host\)\} media_hint64=\$\{b64\(probe\.mediaHint\)\}"\)\n'''
        r'''                \}\n'''
    )
    replacement = f'''                {reader_iter} {{ index, row ->
                    emit("FIELD_NATIVE_PLAYER_BEGIN client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=$index entry=PlatformPlayerSurface")
                    captureDesktopPhase("player-start", fixtureSlug)
                    val reader = probeDesktopProductionPlayer(row.url, row.headers, row.type, {expected_minutes})
                    emit("FIELD_NATIVE_PLAYER client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=$index state=${{reader.state}} engine=nuvio-desktop-production http_status=${{reader.httpStatus}} failure_stage=${{reader.failureStage}} duration_seconds=${{reader.durationSeconds ?: 0.0}} host64=${{b64(hostOnly(row.url))}} error_class64=${{b64(reader.errorClass)}} error_code64=${{b64(reader.errorCode)}} exception_chain64=${{b64(reader.exceptionChain)}} response_header_names64=${{b64("")}} load_bytes=0 load_duration_ms=0 media_data_type=-1 track_type=-1")
                    captureDesktopPhase("player-result", fixtureSlug)
                    // Independent transport diagnostics run only after the production
                    // player has reached a terminal observation for this source.
                    val transport = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=$index state=${{transport.state}} kind=${{transport.kind}} status=${{transport.status}} content_type64=${{b64(transport.contentType)}} extm3u=${{transport.extm3u}} duration_seconds=${{transport.durationSeconds ?: 0.0}} host64=${{b64(transport.host)}} media_hint64=${{b64(transport.mediaHint)}}")
                }}
'''
    text, changed = transport_pattern.subn(replacement, text, count=1)
    if changed != 1:
        raise SystemExit(f"desktop reader transport replacement count={changed}")

    begin = '        emit("FIELD_NATIVE_CORPUS_BEGIN client=desktop fixture=$fixtureSlug title64=${b64(title)} providers=${providers.size}")'
    text = replace_once(text, begin, begin + '\n        captureDesktopPhase("corpus-begin", fixtureSlug)', "corpus begin")
    provider_begin = '                emit("FIELD_NATIVE_PROVIDER_BEGIN client=desktop fixture=$fixtureSlug provider64=${b64(provider.id)} enabled=${provider.enabled} request_type=$requestMediaType route_mode=$routeMode declared_types64=${b64(declaredTypesByProvider[provider.id.lowercase()].orEmpty().sorted().joinToString(","))}")'
    text = replace_once(text, provider_begin, provider_begin + '\n                captureDesktopPhase("provider-loading", fixtureSlug)', "provider begin")
    result_marker = 'emit("FIELD_NATIVE_RESULT client=desktop fixture=$fixtureSlug provider64=${b64(provider.id)} request_type=$requestMediaType route_mode=$routeMode'
    text = text.replace(result_marker, 'captureDesktopPhase("provider-result", fixtureSlug)\n                ' + result_marker)
    end = '        emit("FIELD_NATIVE_CORPUS_END client=desktop fixture=$fixtureSlug errors=${errors.size}")'
    text = replace_once(text, end, '        captureDesktopPhase("corpus-end", fixtureSlug)\n' + end, "corpus end")
    path.write_text(text, encoding="utf-8")
    print(
        f"FIELD_NATIVE_DESKTOP_READER_AUGMENTED source={path} streams={stream_scope} "
        f"expected_minutes={expected_minutes} timeout_ms={reader_timeout_ms} entry=PlatformPlayerSurface "
        f"ci_mode={'pr-bounded' if pr_bounded else 'deep'} theme=NuvioTheme"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--expected-minutes", type=int, default=0)
    parser.add_argument("--streams", default="all")
    args = parser.parse_args()
    raw = str(args.streams).strip().lower()
    if raw != "all":
        try:
            value = int(raw)
        except ValueError as error:
            raise SystemExit("--streams must be all or 1-4") from error
        if value < 1 or value > 4:
            raise SystemExit("--streams must be all or 1-4")
    augment(Path(args.source).resolve(), max(0, args.expected_minutes), raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
