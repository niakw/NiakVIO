#!/usr/bin/env python3
"""Augment Android native-corpus tests with production Nuvio playback observation.

The generated lab never constructs a parallel Media3 player. TV launches NuvioTV's
real Player screen and reads LastPlaybackDiagnostics written by PlayerRuntimeController.
Mobile renders NuvioMobile's real PlatformPlayerSurface inside its real MainActivity,
therefore preserving production header sanitation, player settings and ExoPlayer→libmpv
fallback. Independent transport diagnostics run only after the player observation.
"""
from __future__ import annotations

from typing import Iterable

ANDROID_IMPORT_ANCHOR = "import android.util.Log\n"
TEST_ANCHOR = "    @Test\n"

COMMON_IMPORTS = """import android.content.Intent
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
"""

TV_IMPORTS = """import androidx.activity.compose.setContent
import androidx.navigation.compose.rememberNavController
import com.nuvio.tv.MainActivity
import com.nuvio.tv.core.player.LastPlaybackDiagnostics
import com.nuvio.tv.data.local.PlayerSettingsDataStore
import com.nuvio.tv.ui.navigation.NuvioNavHost
import com.nuvio.tv.ui.navigation.Screen
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
"""

MOBILE_IMPORTS = """import androidx.activity.compose.setContent
import com.nuvio.app.MainActivity
import com.nuvio.app.features.player.PlatformPlayerSurface
import com.nuvio.app.features.player.PlayerPlaybackSnapshot
import com.nuvio.app.features.player.PlayerResizeMode
"""

PROBE_MODEL = r'''
    data class NativePlayerProbe(
        val state: String,
        val engine: String,
        val errorClass: String,
        val errorCode: String,
        val httpStatus: Int,
        val failureStage: String,
        val host: String,
        val durationSeconds: Double?,
        val exceptionChain: String = "",
        val responseHeaderNames: String = "",
        val loadBytes: Long = 0L,
        val loadDurationMs: Long = 0L,
        val mediaDataType: Int = -1,
        val trackType: Int = -1,
    )

    private fun sanitizeDiag(raw: String?): String = raw.orEmpty()
        .replace(Regex("https?://\\S+", RegexOption.IGNORE_CASE), "<url>")
        .replace(Regex("(?i)(authorization|cookie|token|secret)\\s*[:=]\\s*\\S+"), "$1=<redacted>")
        .replace(Regex("\\s+"), " ")
        .take(420)
'''

TV_HELPERS = PROBE_MODEL + r'''
    @EntryPoint
    @InstallIn(SingletonComponent::class)
    interface NiakvioPlayerSettingsEntryPoint {
        fun playerSettingsDataStore(): PlayerSettingsDataStore
    }

    private fun probeNativePlayer(
        url: String,
        headers: Map<String, String>?,
        streamType: String?,
        expectedDurationMinutes: Int,
    ): NativePlayerProbe {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val host = hostOnly(url)
        var activity: MainActivity? = null
        return try {
            val store = EntryPointAccessors.fromApplication(
                context.applicationContext,
                NiakvioPlayerSettingsEntryPoint::class.java,
            ).playerSettingsDataStore()
            val baseline = runBlocking { store.lastPlaybackDiagnostics.first().timestampMs }
            val intent = context.packageManager.getLaunchIntentForPackage(context.packageName)
                ?: return NativePlayerProbe("error", "nuvio-tv", "MainActivity", "NO_LAUNCH_INTENT", 0, "player_setup", host, null)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
            activity = instrumentation.startActivitySync(intent) as? MainActivity
                ?: return NativePlayerProbe("error", "nuvio-tv", "MainActivity", "WRONG_ACTIVITY", 0, "player_setup", host, null)
            val route = Screen.Player.createRoute(
                streamUrl = url,
                title = "NiakVIO native reader",
                streamName = "NiakVIO native reader",
                headers = headers,
                contentType = streamType,
                autoPlayNav = true,
            )
            instrumentation.runOnMainSync {
                activity?.setContent {
                    val navController = rememberNavController()
                    NuvioNavHost(navController = navController, startDestination = route)
                }
            }
            val diagnostics = runBlocking {
                withTimeout(__PLAYER_TIMEOUT_MS__L) {
                    store.lastPlaybackDiagnostics.first { row ->
                        row.timestampMs > baseline && row.result != "Pending"
                    }
                }
            }
            val durationSeconds = diagnostics.durationMs.takeIf { it > 0L }?.div(1000.0)
            val expected = expectedDurationMinutes.takeIf { it > 0 }?.times(60.0)
            val shortMedia = durationSeconds != null && (
                durationSeconds < 60.0 || (expected != null && durationSeconds / expected < 0.55)
            )
            when {
                shortMedia -> NativePlayerProbe("short_media", "nuvio-tv-production", "", "", 0, "duration_identity", diagnostics.host.ifBlank { host }, durationSeconds)
                diagnostics.result.startsWith("Played", ignoreCase = true) || diagnostics.firstFrameMs >= 0L ->
                    NativePlayerProbe("ready", "nuvio-tv-production", "", "", 0, "none", diagnostics.host.ifBlank { host }, durationSeconds)
                diagnostics.result.startsWith("Error", ignoreCase = true) ->
                    NativePlayerProbe("error", "nuvio-tv-production", "PlayerRuntimeController", sanitizeDiag(diagnostics.result), 0, "player", diagnostics.host.ifBlank { host }, durationSeconds)
                else -> NativePlayerProbe("error", "nuvio-tv-production", "PlayerRuntimeController", sanitizeDiag(diagnostics.result), 0, "player", diagnostics.host.ifBlank { host }, durationSeconds)
            }
        } catch (error: kotlinx.coroutines.TimeoutCancellationException) {
            NativePlayerProbe("timeout", "nuvio-tv-production", error::class.qualifiedName.orEmpty(), "READER_TIMEOUT", 0, "timeout", host, null)
        } catch (error: Throwable) {
            NativePlayerProbe("error", "nuvio-tv-production", error::class.qualifiedName.orEmpty(), sanitizeDiag(error.message), 0, "player_setup", host, null)
        } finally {
            runCatching { instrumentation.runOnMainSync { activity?.finish() } }
        }
    }
'''

MOBILE_HELPERS = PROBE_MODEL + r'''
    private fun probeNativePlayer(
        url: String,
        headers: Map<String, String>?,
        streamType: String?,
        expectedDurationMinutes: Int,
    ): NativePlayerProbe {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val host = hostOnly(url)
        val terminal = CountDownLatch(1)
        val snapshotRef = AtomicReference<PlayerPlaybackSnapshot?>(null)
        val errorRef = AtomicReference<String?>(null)
        var activity: MainActivity? = null
        return try {
            val intent = context.packageManager.getLaunchIntentForPackage(context.packageName)
                ?: return NativePlayerProbe("error", "nuvio-mobile", "MainActivity", "NO_LAUNCH_INTENT", 0, "player_setup", host, null)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
            activity = instrumentation.startActivitySync(intent) as? MainActivity
                ?: return NativePlayerProbe("error", "nuvio-mobile", "MainActivity", "WRONG_ACTIVITY", 0, "player_setup", host, null)
            instrumentation.runOnMainSync {
                activity?.setContent {
                    // Real NuvioMobile production player entry. Its own code performs
                    // header sanitation, settings lookup and Auto engine fallback.
                    PlatformPlayerSurface(
                        sourceUrl = url,
                        sourceHeaders = headers.orEmpty(),
                        sourceResponseHeaders = emptyMap(),
                        externalSubtitles = emptyList(),
                        streamType = streamType,
                        useYoutubeChunkedPlayback = false,
                        playWhenReady = true,
                        initialPositionMs = 0L,
                        initialPositionRequestKey = "niakvio-native-reader",
                        resizeMode = PlayerResizeMode.Fit,
                        useNativeController = true,
                        onInitialPositionHandled = { _, _ -> },
                        onControllerReady = { _ -> },
                        onSnapshot = { snapshot ->
                            snapshotRef.set(snapshot)
                            if (snapshot.isEnded || (!snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L))) {
                                terminal.countDown()
                            }
                        },
                        onError = { message ->
                            // Auto mode intentionally emits null while switching from
                            // ExoPlayer to libmpv; do not terminate until Nuvio itself
                            // reports a final error or a playable snapshot.
                            if (!message.isNullOrBlank()) {
                                errorRef.compareAndSet(null, message)
                                terminal.countDown()
                            }
                        },
                    )
                }
            }
            terminal.await(__PLAYER_TIMEOUT_MS__L, TimeUnit.MILLISECONDS)
            val error = errorRef.get()
            val snapshot = snapshotRef.get()
            if (!error.isNullOrBlank()) {
                return NativePlayerProbe("error", "nuvio-mobile-production", "PlatformPlayerSurface", sanitizeDiag(error), 0, "player", host, null)
            }
            val durationSeconds = snapshot?.durationMs?.takeIf { it > 0L }?.div(1000.0)
            val expected = expectedDurationMinutes.takeIf { it > 0 }?.times(60.0)
            val shortMedia = durationSeconds != null && (
                durationSeconds < 60.0 || (expected != null && durationSeconds / expected < 0.55)
            )
            when {
                shortMedia -> NativePlayerProbe("short_media", "nuvio-mobile-production", "", "", 0, "duration_identity", host, durationSeconds)
                snapshot?.isEnded == true -> NativePlayerProbe("ended", "nuvio-mobile-production", "", "", 0, "none", host, durationSeconds)
                snapshot != null && !snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || snapshot.durationMs > 0L) ->
                    NativePlayerProbe("ready", "nuvio-mobile-production", "", "", 0, "none", host, durationSeconds)
                else -> NativePlayerProbe("timeout", "nuvio-mobile-production", "PlatformPlayerSurface", "READER_TIMEOUT", 0, "timeout", host, durationSeconds)
            }
        } catch (error: Throwable) {
            NativePlayerProbe("error", "nuvio-mobile-production", error::class.qualifiedName.orEmpty(), sanitizeDiag(error.message), 0, "player_setup", host, null)
        } finally {
            runCatching { instrumentation.runOnMainSync { activity?.finish() } }
        }
    }
'''

OLD_ANDROID_PROBE_BLOCK = '''                rows.firstOrNull()?.let { row ->
                    val probe = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} state=${probe.state} kind=${probe.kind} status=${probe.status} content_type64=${b64(probe.contentType)} extm3u=${probe.extm3u} duration_seconds=${probe.durationSeconds ?: 0.0} host64=${b64(probe.host)} media_hint64=${b64(probe.mediaHint)}")
                }
'''

NEW_ANDROID_PROBE_BLOCK = '''                rows.take(__MAX_PROBES__).forEachIndexed { index, row ->
                    // Human UX contract: Nuvio's production player is the first
                    // consumer. A diagnostic GET before playback can consume a
                    // signed/one-shot URL and manufacture a false failure.
                    emit("FIELD_NATIVE_PLAYER_BEGIN client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index entry=nuvio-production-player")
                    val reader = probeNativePlayer(row.url, row.headers, row.type, __EXPECTED_MINUTES__)
                    emit("FIELD_NATIVE_PLAYER client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index state=${reader.state} engine=${reader.engine} http_status=${reader.httpStatus} failure_stage=${reader.failureStage} duration_seconds=${reader.durationSeconds ?: 0.0} host64=${b64(reader.host)} error_class64=${b64(reader.errorClass)} error_code64=${b64(reader.errorCode)} exception_chain64=${b64(reader.exceptionChain)} response_header_names64=${b64(reader.responseHeaderNames)} load_bytes=${reader.loadBytes} load_duration_ms=${reader.loadDurationMs} media_data_type=${reader.mediaDataType} track_type=${reader.trackType}")
                    val transport = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index state=${transport.state} kind=${transport.kind} status=${transport.status} content_type64=${b64(transport.contentType)} extm3u=${transport.extm3u} duration_seconds=${transport.durationSeconds ?: 0.0} host64=${b64(transport.host)} media_hint64=${b64(transport.mediaHint)}")
                }
'''


def augment_android_test(
    source: str,
    *,
    client: str,
    expected_duration_minutes: int | float | None = None,
    max_player_probes: int = 1,
) -> str:
    if client not in {"mobile", "tv"}:
        raise ValueError(f"unsupported Android client: {client}")
    max_player_probes = max(1, min(int(max_player_probes or 1), 4))
    expected = max(0, int(expected_duration_minutes or 0))
    if "FIELD_NATIVE_PLAYER " in source:
        return source
    if source.count(ANDROID_IMPORT_ANCHOR) != 1:
        raise ValueError("android import anchor missing or ambiguous")
    imports = COMMON_IMPORTS + (TV_IMPORTS if client == "tv" else MOBILE_IMPORTS)
    source = source.replace(ANDROID_IMPORT_ANCHOR, ANDROID_IMPORT_ANCHOR + imports, 1)
    helpers = (TV_HELPERS if client == "tv" else MOBILE_HELPERS).replace("__PLAYER_TIMEOUT_MS__", "22000")
    if source.count(TEST_ANCHOR) != 1:
        raise ValueError("test anchor missing or ambiguous")
    source = source.replace(TEST_ANCHOR, helpers + "\n" + TEST_ANCHOR, 1)
    old = OLD_ANDROID_PROBE_BLOCK.replace("__CLIENT__", client)
    if source.count(old) != 1:
        raise ValueError(f"transport probe anchor missing for {client}: count={source.count(old)}")
    new = (
        NEW_ANDROID_PROBE_BLOCK.replace("__CLIENT__", client)
        .replace("__MAX_PROBES__", str(max_player_probes))
        .replace("__EXPECTED_MINUTES__", str(expected))
    )
    return source.replace(old, new, 1)


def filter_staged_providers(providers: Iterable[dict], provider: str | None) -> list[dict]:
    rows = list(providers)
    wanted = str(provider or "").strip().casefold()
    if not wanted:
        return rows
    filtered = [row for row in rows if str(row.get("id") or "").strip().casefold() == wanted]
    if not filtered:
        available = ", ".join(str(row.get("id") or "") for row in rows[:40])
        raise ValueError(f"unknown provider {provider!r}; available sample: {available}")
    return filtered
