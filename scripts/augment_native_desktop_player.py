#!/usr/bin/env python3
"""Augment a generated NuvioDesktop corpus test with the official native player.

This runs only on macOS/Windows. Linux NuvioDesktop intentionally uses a stub player
and is therefore never accepted as native-reader proof.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


IMPORT_ANCHOR = "import com.nuvio.app.features.plugins.runtime.PluginRuntime\n"
TEST_ANCHOR = "    @Test\n"

IMPORTS = """import com.nuvio.app.features.player.desktop.DesktopHostOs
import com.nuvio.app.features.player.desktop.NativePlayerController
import com.nuvio.app.features.player.desktop.NativePlayerHost
import java.awt.BorderLayout
import java.awt.Rectangle
import java.awt.Robot
import java.awt.Toolkit
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
    )

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

    private fun probeDesktopNativePlayer(
        url: String,
        headers: Map<String, String>?,
        expectedDurationMinutes: Int,
    ): DesktopNativePlayerProbe {
        if (DesktopHostOs.current != DesktopHostOs.MACOS && DesktopHostOs.current != DesktopHostOs.WINDOWS) {
            return DesktopNativePlayerProbe("unsupported", "DesktopHostOs", "LINUX_STUB", 0, "player_setup", null, null)
        }
        val frameRef = AtomicReference<JFrame?>(null)
        val controllerRef = AtomicReference<NativePlayerController?>(null)
        val errorRef = AtomicReference<String?>(null)
        try {
            SwingUtilities.invokeAndWait {
                val frame = JFrame("Nuvio Desktop native reader lab")
                val host = NativePlayerHost()
                frame.layout = BorderLayout()
                frame.add(host, BorderLayout.CENTER)
                frame.setSize(960, 540)
                frame.setLocationRelativeTo(null)
                frame.isVisible = true
                val controller = NativePlayerController(host)
                frameRef.set(frame)
                controllerRef.set(controller)
            }
            val controller = controllerRef.get()
                ?: return DesktopNativePlayerProbe("error", "NativePlayerController", "NO_CONTROLLER", 0, "player_setup", null, null)
            controller.attach(
                sourceUrl = url,
                sourceHeaders = headers.orEmpty().filterKeys { !it.equals("Range", ignoreCase = true) },
                playWhenReady = true,
                initialPositionMs = 0L,
                decoderPriority = 1,
                nvidiaRtxSuperResolutionEnabled = false,
                onError = { message -> errorRef.compareAndSet(null, message ?: "native_player_error") },
            )
            val deadline = System.currentTimeMillis() + 25_000L
            var lastDuration: Long = 0L
            var lastPosition: Long = 0L
            while (System.currentTimeMillis() < deadline) {
                errorRef.get()?.let { message ->
                    return DesktopNativePlayerProbe(
                        "error", "NativePlayer", message.replace(Regex("\\s+"), "_").take(120),
                        0, "player", null, null,
                    )
                }
                val snapshot = controller.snapshot()
                lastDuration = snapshot.durationMs.coerceAtLeast(0L)
                lastPosition = snapshot.positionMs.coerceAtLeast(0L)
                val durationSeconds = lastDuration.takeIf { it > 0 }?.div(1000.0)
                val expected = expectedDurationMinutes.takeIf { it > 0 }?.times(60.0)
                val shortMedia = durationSeconds != null && (
                    durationSeconds < 60.0 || (expected != null && durationSeconds / expected < 0.55)
                )
                if (shortMedia) {
                    return DesktopNativePlayerProbe("short_media", "", "", 0, "duration_identity", durationSeconds, lastPosition / 1000.0)
                }
                if (snapshot.isEnded) {
                    return DesktopNativePlayerProbe("ended", "", "", 0, "none", durationSeconds, lastPosition / 1000.0)
                }
                if (!snapshot.isLoading && (snapshot.isPlaying || lastPosition > 0L || lastDuration > 0L)) {
                    return DesktopNativePlayerProbe("ready", "", "", 0, "none", durationSeconds, lastPosition / 1000.0)
                }
                Thread.sleep(500L)
            }
            return DesktopNativePlayerProbe(
                "timeout", "NativePlayer", "READER_TIMEOUT", 0, "timeout",
                lastDuration.takeIf { it > 0 }?.div(1000.0),
                lastPosition.takeIf { it > 0 }?.div(1000.0),
            )
        } catch (error: Throwable) {
            return DesktopNativePlayerProbe(
                "error", error::class.qualifiedName.orEmpty(), "PLAYER_SETUP", 0, "player_setup", null, null,
            )
        } finally {
            runCatching { controllerRef.getAndSet(null)?.dispose() }
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
    if "DesktopNativePlayerProbe" in text:
        return
    text = replace_once(text, IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORTS, "imports")
    text = replace_once(text, TEST_ANCHOR, HELPERS + "\n" + TEST_ANCHOR, "test")

    # Make row evidence match the actual reader scope.
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
                    emit("FIELD_NATIVE_PLAYER_BEGIN client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=$index")
                    captureDesktopPhase("player-start", fixtureSlug)
                    val reader = probeDesktopNativePlayer(row.url, row.headers, {expected_minutes})
                    emit("FIELD_NATIVE_PLAYER client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=$index state=${{reader.state}} engine=native-desktop http_status=${{reader.httpStatus}} failure_stage=${{reader.failureStage}} duration_seconds=${{reader.durationSeconds ?: 0.0}} host64=${{b64(hostOnly(row.url))}} error_class64=${{b64(reader.errorClass)}} error_code64=${{b64(reader.errorCode)}} exception_chain64=${{b64("")}} response_header_names64=${{b64("")}} load_bytes=0 load_duration_ms=0 media_data_type=-1 track_type=-1")
                    captureDesktopPhase("player-result", fixtureSlug)
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
    print(f"FIELD_NATIVE_DESKTOP_READER_AUGMENTED source={path} streams={stream_scope} expected_minutes={expected_minutes}")


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
