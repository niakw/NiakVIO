#!/usr/bin/env python3
"""Augment Android native-corpus tests with production Nuvio playback observation.

The generated lab never constructs a parallel Media3 player. TV launches NuvioTV's
real Player screen and reads LastPlaybackDiagnostics written by PlayerRuntimeController.
Mobile renders NuvioMobile's real PlatformPlayerSurface inside its real MainActivity,
therefore preserving production header sanitation, player settings and ExoPlayer→libmpv
fallback. Independent transport diagnostics run only after the player observation.
"""
from __future__ import annotations

import os
from typing import Iterable

ANDROID_IMPORT_ANCHOR = "import android.util.Log\n"
TEST_ANCHOR = "    @Test\n"

COMMON_IMPORTS = """import android.content.Intent
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
"""

# Shared TV Hilt/repository imports are owned by augment_native_provider_loading.py.
# Keeping them out of this player-only layer prevents two independent augmenters
# from emitting the same Kotlin imports into the final native corpus source.
TV_IMPORTS = """import androidx.activity.compose.setContent
import androidx.navigation.compose.rememberNavController
import androidx.test.uiautomator.By
import androidx.test.uiautomator.UiDevice
import androidx.test.uiautomator.Until
import com.nuvio.tv.MainActivity
import com.nuvio.tv.R
import com.nuvio.tv.core.player.LastPlaybackDiagnostics
import com.nuvio.tv.data.local.PlayerSettingsDataStore
import com.nuvio.tv.ui.navigation.NuvioNavHost
import com.nuvio.tv.ui.navigation.Screen
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
"""

MOBILE_IMPORTS = """import androidx.activity.compose.setContent
import com.nuvio.app.MainActivity
import com.nuvio.app.features.player.AndroidPlaybackEngine
import com.nuvio.app.features.player.PlatformPlayerSurface
import com.nuvio.app.features.player.PlayerEngineController
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
        val audioTrackCount: Int = -1,
        val audioTrackLanguages: String = "",
        val subtitleTrackCount: Int = -1,
        val subtitleTrackLanguages: String = "",
        val subtitleTrackLabels: String = "",
        val videoWidth: Int = 0,
        val videoHeight: Int = 0,
        // Official LastPlaybackDiagnostics may report synthetic first-frame on
        // tunneled READY. This marker is observational, never decode proof.
        val diagnosticFirstFrameMs: Long = -1L,
        val diagnosticPlayed: Boolean = false,
        val diagnosticLateFormat: Boolean = false,
    )

    private val niakvioPlayerProbeLock = Any()

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

    private data class TvAudioTrackProbe(
        val count: Int = -1,
        val languages: String = "",
    )

    private fun normalizeTvVisibleLanguage(label: String?): String? {
        val raw = label?.trim().orEmpty()
        if (raw.isBlank()) return null
        val locales = java.util.Locale.getAvailableLocales()
        val isoCodes = locales.asSequence().map { it.language.lowercase(java.util.Locale.US) }
            .filter { it.length == 2 }.distinct().toSet()
        // An unanchored match over every visible accessibility label used to
        // report "pm,at" from unrelated playback controls as audio tracks.
        // Accept tags only when the *entire* label is a recognized ISO tag.
        val direct = Regex("""(?i)^[a-z]{2,3}(?:[-_][a-z]{2})?$""")
            .matchEntire(raw)?.value?.replace('_', '-')?.lowercase(java.util.Locale.US)
        if (direct != null) {
            val code = direct.substringBefore('-')
            if (code.length == 2) return code.takeIf { it in isoCodes }
            return locales.firstOrNull { locale ->
                runCatching { locale.isO3Language.equals(code, ignoreCase = true) }
                    .getOrDefault(false)
            }?.language?.lowercase(java.util.Locale.US)?.takeIf { it in isoCodes }
        }

        // Exact, localized names may have a non-language codec qualifier:
        // "Français (stéréo)", "日本語 · AAC", "English - Stereo".
        // Reject words embedded elsewhere in a generic UI control.
        val surface = raw.substringBefore('(').substringBefore('—')
            .substringBefore(" - ").substringBefore(" · ")
            .trim().lowercase(java.util.Locale.ROOT)
        if (surface.length < 3) return null
        return isoCodes.asSequence().mapNotNull { code ->
            val locale = java.util.Locale.forLanguageTag(code)
            val names = sequenceOf(
                locale.getDisplayLanguage(java.util.Locale.getDefault()),
                locale.getDisplayLanguage(java.util.Locale.ENGLISH),
                locale.getDisplayLanguage(locale),
            ).map { it.trim().lowercase(java.util.Locale.ROOT) }
                .filter { it.length >= 3 }.distinct()
            if (names.any { it == surface }) code else null
        }.firstOrNull()
    }

    private fun findTvControlButton(
        device: UiDevice,
        label: String,
    ): androidx.test.uiautomator.UiObject2? {
        val visible = device.wait(Until.findObject(By.desc(label)), 500L)
        if (visible != null) return visible
        device.pressDPadCenter()
        return device.wait(Until.findObject(By.desc(label)), 2500L)
    }

    private fun visibleTvLanguageNodes(
        device: UiDevice,
    ): List<Pair<String, androidx.test.uiautomator.UiObject2>> {
        return device.findObjects(By.text(java.util.regex.Pattern.compile(".+")))
            .mapNotNull { node ->
                normalizeTvVisibleLanguage(node.text)?.let { language -> language to node }
            }
            .distinctBy { it.first }
    }

    private fun probeTvAudioTracks(
        instrumentation: android.app.Instrumentation,
        context: android.content.Context,
    ): TvAudioTrackProbe {
        return try {
            val device = UiDevice.getInstance(instrumentation)
            val label = context.getString(R.string.cd_audio_tracks)
            val button = findTvControlButton(device, label)
                ?: return TvAudioTrackProbe()
            button.click()
            device.waitForIdle()
            device.wait(Until.hasObject(By.clazz("android.widget.RadioButton")), 1200L)
            Thread.sleep(500L)
            val radioRows = device.findObjects(By.clazz("android.widget.RadioButton"))
            val semanticLanguages = radioRows.mapNotNull { track ->
                sequenceOf(track.text, track.contentDescription)
                    .mapNotNull(::normalizeTvVisibleLanguage)
                    .firstOrNull()
            }
            // Compose TV exposes Role.RadioButton inconsistently through UiAutomator.
            // The production overlay always renders the track language as Text, so
            // visible language rows are the authoritative fallback when the role
            // semantics are absent from the Android accessibility class tree.
            val visibleLanguages = visibleTvLanguageNodes(device).map { it.first }
            val languages = (semanticLanguages + visibleLanguages).distinct()
            val count = if (radioRows.isNotEmpty()) {
                maxOf(radioRows.size, languages.size)
            } else {
                languages.size
            }
            device.pressBack()
            TvAudioTrackProbe(count, languages.joinToString(","))
        } catch (_: Throwable) {
            TvAudioTrackProbe()
        }
    }

    private data class TvSubtitleTrackProbe(
        val count: Int = -1,
        val languages: String = "",
        val labels: String = "",
    )

    private fun probeTvIntegratedSubtitleTracks(
        instrumentation: android.app.Instrumentation,
        context: android.content.Context,
    ): TvSubtitleTrackProbe {
        return try {
            val device = UiDevice.getInstance(instrumentation)
            val controlLabel = context.getString(R.string.cd_subtitles)
            val button = findTvControlButton(device, controlLabel)
                ?: return TvSubtitleTrackProbe()
            button.click()
            device.waitForIdle()
            val builtIn = context.getString(R.string.subtitle_built_in)
            Thread.sleep(500L)

            // The subtitle overlay first presents a language rail. If "Off" is
            // selected, no Built-in option row exists yet. Select the first real
            // visible language so the production UI materializes its source rows.
            var internalNodes = device.findObjects(By.text(builtIn))
            var visibleLanguages = visibleTvLanguageNodes(device)
            if (internalNodes.isEmpty() && visibleLanguages.isNotEmpty()) {
                visibleLanguages.first().second.click()
                device.waitForIdle()
                device.wait(Until.hasObject(By.text(builtIn)), 2500L)
                Thread.sleep(350L)
                internalNodes = device.findObjects(By.text(builtIn))
                visibleLanguages = visibleTvLanguageNodes(device)
            }
            val languages = visibleLanguages.map { it.first }.distinct()
            device.pressBack()
            TvSubtitleTrackProbe(
                count = internalNodes.size,
                languages = languages.joinToString(","),
                labels = languages.joinToString(" | "),
            )
        } catch (_: Throwable) {
            TvSubtitleTrackProbe()
        }
    }

    private fun probeNativePlayer(
        url: String,
        headers: Map<String, String>?,
        streamType: String?,
        expectedDurationMinutes: Int,
    ): NativePlayerProbe = synchronized(niakvioPlayerProbeLock) {
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
            val initialDiagnostics = runBlocking {
                withTimeout(__PLAYER_TIMEOUT_MS__L) {
                    store.lastPlaybackDiagnostics.first { row ->
                        row.timestampMs > baseline && row.result != "Pending"
                    }
                }
            }
            // A first Played event can arrive before NuvioTV publishes its
            // video format. Candidate-only wait for a later *official*
            // LastPlaybackDiagnostics update, never fabricate dimensions or
            // treat the synthetic READY first-frame hint as decoded media.
            val diagnostics = if (
                __PLAYER_FORMAT_SETTLE_MS__L > 0L &&
                initialDiagnostics.result.startsWith("Played", ignoreCase = true) &&
                initialDiagnostics.videoResolution.isNullOrBlank()
            ) {
                runBlocking {
                    kotlinx.coroutines.withTimeoutOrNull(__PLAYER_FORMAT_SETTLE_MS__L) {
                        store.lastPlaybackDiagnostics.first { row ->
                            row.timestampMs > baseline &&
                                (Regex("""(\d{2,5})x(\d{2,5})""")
                                    .containsMatchIn(row.videoResolution.orEmpty()) ||
                                 row.result.startsWith("Error", ignoreCase = true))
                        }
                    }
                } ?: initialDiagnostics
            } else initialDiagnostics
            val durationSeconds = diagnostics.durationMs.takeIf { it > 0L }?.div(1000.0)
            val dimensions = Regex("""(\d{2,5})x(\d{2,5})""")
                .find(diagnostics.videoResolution.orEmpty())
            val videoWidth = dimensions?.groupValues?.getOrNull(1)?.toIntOrNull() ?: 0
            val videoHeight = dimensions?.groupValues?.getOrNull(2)?.toIntOrNull() ?: 0
            val expected = expectedDurationMinutes.takeIf { it > 0 }?.times(60.0)
            val shortMedia = durationSeconds != null && (
                durationSeconds < 60.0 || (expected != null && durationSeconds / expected < 0.55)
            )
            val result = when {
                shortMedia -> NativePlayerProbe("short_media", "nuvio-tv-production", "", "", 0, "duration_identity", diagnostics.host.ifBlank { host }, durationSeconds)
                diagnostics.result.startsWith("Played", ignoreCase = true) || diagnostics.firstFrameMs >= 0L ->
                    NativePlayerProbe("ready", "nuvio-tv-production", "", "", 0, "none", diagnostics.host.ifBlank { host }, durationSeconds)
                diagnostics.result.startsWith("Error", ignoreCase = true) ->
                    NativePlayerProbe("error", "nuvio-tv-production", "PlayerRuntimeController", sanitizeDiag(diagnostics.result), 0, "player", diagnostics.host.ifBlank { host }, durationSeconds)
                else -> NativePlayerProbe("error", "nuvio-tv-production", "PlayerRuntimeController", sanitizeDiag(diagnostics.result), 0, "player", diagnostics.host.ifBlank { host }, durationSeconds)
            }
            if (result.state == "ready" || result.state == "short_media") {
                val audioTracks = probeTvAudioTracks(instrumentation, context)
                val subtitleTracks = probeTvIntegratedSubtitleTracks(instrumentation, context)
                val probed = result.copy(
                    audioTrackCount = audioTracks.count,
                    audioTrackLanguages = audioTracks.languages,
                    subtitleTrackCount = subtitleTracks.count,
                    subtitleTrackLanguages = subtitleTracks.languages,
                    subtitleTrackLabels = subtitleTracks.labels,
                    videoWidth = videoWidth,
                    videoHeight = videoHeight,
                    diagnosticFirstFrameMs = diagnostics.firstFrameMs,
                    diagnosticPlayed = diagnostics.result.startsWith("Played", ignoreCase = true),
                    diagnosticLateFormat = diagnostics !== initialDiagnostics,
                )
                // The normal FIELD_NATIVE_PLAYER marker is emitted after
                // this function's finally block has closed MainActivity.
                // Signal a bounded live candidate frame before that cleanup,
                // while preserving the original result and playback semantics.
                if (__PLAYER_VISIBLE_HOLD_MS__L > 0L &&
                    probed.state == "ready" && probed.videoWidth > 0 &&
                    probed.videoHeight > 0 && probed.diagnosticPlayed) {
                    Log.i("NiakvioCorpus",
                        "FIELD_NATIVE_PLAYER_VISUAL_READY client=tv video_width=${probed.videoWidth} video_height=${probed.videoHeight} proof_authority=false")
                    runCatching { Thread.sleep(__PLAYER_VISIBLE_HOLD_MS__L) }
                }
                probed
            } else result
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
        forcedEngine: AndroidPlaybackEngine? = null,
    ): NativePlayerProbe = synchronized(niakvioPlayerProbeLock) {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val host = hostOnly(url)
        val terminal = CountDownLatch(1)
        val snapshotRef = AtomicReference<PlayerPlaybackSnapshot?>(null)
        val controllerRef = AtomicReference<PlayerEngineController?>(null)
        val errorRef = AtomicReference<String?>(null)
        val terminalStateRef = AtomicReference<String?>(null)
        var activity: MainActivity? = null
        return try {
            // Resolve the installed production launcher by activity class, not by the
            // Kotlin namespace/targetContext package. Official build variants may keep
            // com.nuvio.app.MainActivity while using a different applicationId.
            val launcherQuery = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
            val launchActivity = context.packageManager.queryIntentActivities(launcherQuery, 0)
                .firstOrNull { info -> info.activityInfo?.name == MainActivity::class.java.name }
                ?: context.packageManager.queryIntentActivities(launcherQuery, 0)
                    .firstOrNull { info ->
                        info.activityInfo?.name?.endsWith(".MainActivity") == true &&
                            info.activityInfo?.applicationInfo?.sourceDir == context.applicationInfo.sourceDir
                    }
                ?: return NativePlayerProbe("error", "nuvio-mobile", "MainActivity", "NO_LAUNCH_ACTIVITY", 0, "player_setup", host, null)
            val intent = Intent().setClassName(
                launchActivity.activityInfo.packageName,
                launchActivity.activityInfo.name,
            )
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
                        playbackEngine = forcedEngine,
                        useNativeController = true,
                        onInitialPositionHandled = { _, _ -> },
                        onControllerReady = { controller -> controllerRef.set(controller) },
                        onSnapshot = { snapshot ->
                            snapshotRef.set(snapshot)
                            if ((snapshot.isEnded || (!snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || (snapshot.videoWidth > 0 && snapshot.videoHeight > 0)))) &&
                                terminalStateRef.compareAndSet(null, "success")
                            ) {
                                terminal.countDown()
                            }
                        },
                        onError = { message ->
                            // Auto mode intentionally emits null while switching from
                            // ExoPlayer to libmpv; do not terminate until Nuvio itself
                            // reports a final error or a playable snapshot.
                            if (!message.isNullOrBlank() && terminalStateRef.compareAndSet(null, "error")) {
                                errorRef.set(message)
                                terminal.countDown()
                            }
                        },
                    )
                }
            }
            terminal.await(__PLAYER_TIMEOUT_MS__L, TimeUnit.MILLISECONDS)
            val terminalState = terminalStateRef.get()
            val error = errorRef.get()
            val snapshot = snapshotRef.get()
            var audioTracks = runCatching { controllerRef.get()?.getAudioTracks().orEmpty() }
                .getOrDefault(emptyList())
            var subtitleTracks = runCatching { controllerRef.get()?.getSubtitleTracks().orEmpty() }
                .getOrDefault(emptyList())
            if (terminalState == "success" && (audioTracks.isEmpty() || subtitleTracks.isEmpty())) {
                repeat(8) {
                    if (audioTracks.isNotEmpty() && subtitleTracks.isNotEmpty()) return@repeat
                    Thread.sleep(125L)
                    if (audioTracks.isEmpty()) {
                        audioTracks = runCatching { controllerRef.get()?.getAudioTracks().orEmpty() }
                            .getOrDefault(emptyList())
                    }
                    if (subtitleTracks.isEmpty()) {
                        subtitleTracks = runCatching { controllerRef.get()?.getSubtitleTracks().orEmpty() }
                            .getOrDefault(emptyList())
                    }
                }
            }
            val audioLanguages = audioTracks.mapNotNull { track ->
                track.language?.trim()?.takeIf { it.isNotBlank() && !it.equals("und", ignoreCase = true) }
            }.distinct().joinToString(",")
            val subtitleLanguages = subtitleTracks.mapNotNull { track ->
                track.language?.trim()?.takeIf { it.isNotBlank() && !it.equals("und", ignoreCase = true) }
            }.distinct().joinToString(",")
            val subtitleLabels = subtitleTracks.mapNotNull { track ->
                track.label.trim().takeIf { it.isNotBlank() }
            }.distinct().joinToString(" | ")
            if (terminalState == "error" && !error.isNullOrBlank()) {
                return NativePlayerProbe("error", "nuvio-mobile-production", "PlatformPlayerSurface", sanitizeDiag(error), 0, "player", host, null)
            }
            val durationSeconds = snapshot?.durationMs?.takeIf { it > 0L }?.div(1000.0)
            val expected = expectedDurationMinutes.takeIf { it > 0 }?.times(60.0)
            val shortMedia = durationSeconds != null && (
                durationSeconds < 60.0 || (expected != null && durationSeconds / expected < 0.55)
            )
            val result = when {
                terminalState == "success" && shortMedia -> NativePlayerProbe("short_media", "nuvio-mobile-production", "", "", 0, "duration_identity", host, durationSeconds)
                terminalState == "success" && snapshot?.isEnded == true -> NativePlayerProbe("ended", "nuvio-mobile-production", "", "", 0, "none", host, durationSeconds)
                terminalState == "success" && snapshot != null && !snapshot.isLoading && (snapshot.isPlaying || snapshot.positionMs > 0L || (snapshot.videoWidth > 0 && snapshot.videoHeight > 0)) ->
                    NativePlayerProbe("ready", "nuvio-mobile-production", "", "", 0, "none", host, durationSeconds)
                else -> NativePlayerProbe("timeout", "nuvio-mobile-production", "PlatformPlayerSurface", "READER_TIMEOUT", 0, "timeout", host, durationSeconds)
            }
            result.copy(
                engine = controllerRef.get()?.playbackEngine?.name ?: result.engine,
                audioTrackCount = audioTracks.size,
                audioTrackLanguages = audioLanguages,
                subtitleTrackCount = subtitleTracks.size,
                subtitleTrackLanguages = subtitleLanguages,
                subtitleTrackLabels = subtitleLabels,
                videoWidth = snapshot?.videoWidth ?: 0,
                videoHeight = snapshot?.videoHeight ?: 0,
            )
        } catch (error: Throwable) {
            val chain = generateSequence(error) { it.cause }
                .take(6)
                .joinToString(" -> ") { cause ->
                    cause::class.qualifiedName.orEmpty() + ":" + sanitizeDiag(cause.message)
                }
            NativePlayerProbe(
                "error",
                "nuvio-mobile-production",
                error::class.qualifiedName.orEmpty(),
                sanitizeDiag(error.message),
                0,
                "player_setup",
                host,
                null,
                chain,
            )
        } finally {
            runCatching { instrumentation.runOnMainSync { activity?.finish() } }
        }
    }
'''

OLD_ANDROID_PROBE_BLOCK = '''                rows.firstOrNull()?.let { row ->
                    val probe = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} state=${probe.state} kind=${probe.kind} status=${probe.status} content_type64=${b64(probe.contentType)} extm3u=${probe.extm3u} audio_track_count=${probe.audioTrackCount} audio_track_languages64=${b64(probe.audioTrackLanguages)} subtitle_track_count=${probe.subtitleTrackCount} subtitle_track_languages64=${b64(probe.subtitleTrackLanguages)} audio_variant_matrix64=${b64(probe.audioVariantMatrix)} subtitle_variant_matrix64=${b64(probe.subtitleVariantMatrix)} variant_heights64=${b64(probe.variantHeights)} variant_codecs64=${b64(probe.variantCodecs)} duration_seconds=${probe.durationSeconds ?: 0.0} host64=${b64(probe.host)} media_hint64=${b64(probe.mediaHint)}")
                }
'''


MOBILE_ENGINE_COMPARE_BLOCK = '''                    // Targeted diagnostic only: after the normal production/Auto
                    // attempt, replay the exact same row through each official Android
                    // engine. This never replaces acceptance and remains non-authoritative
                    // for short-lived/single-use URLs consumed by the first playback.
                    val exoReader = probeNativePlayer(
                        row.url, row.headers, row.type, __EXPECTED_MINUTES__,
                        AndroidPlaybackEngine.ExoPlayer,
                    )
                    val libmpvReader = probeNativePlayer(
                        row.url, row.headers, row.type, __EXPECTED_MINUTES__,
                        AndroidPlaybackEngine.Libmpv,
                    )
                    emit("FIELD_NATIVE_ENGINE_COMPARE client=mobile fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index same_source=true comparison_order=post_auto exo_state=${exoReader.state} exo_engine=${exoReader.engine} exo_video_width=${exoReader.videoWidth} exo_video_height=${exoReader.videoHeight} exo_audio_track_count=${exoReader.audioTrackCount} exo_audio_track_languages64=${b64(exoReader.audioTrackLanguages)} exo_subtitle_track_count=${exoReader.subtitleTrackCount} exo_subtitle_track_languages64=${b64(exoReader.subtitleTrackLanguages)} libmpv_state=${libmpvReader.state} libmpv_engine=${libmpvReader.engine} libmpv_video_width=${libmpvReader.videoWidth} libmpv_video_height=${libmpvReader.videoHeight} libmpv_audio_track_count=${libmpvReader.audioTrackCount} libmpv_audio_track_languages64=${b64(libmpvReader.audioTrackLanguages)} libmpv_subtitle_track_count=${libmpvReader.subtitleTrackCount} libmpv_subtitle_track_languages64=${b64(libmpvReader.subtitleTrackLanguages)}")
'''

NEW_ANDROID_PROBE_BLOCK = '''                rows.take(__MAX_PROBES__).forEachIndexed { index, row ->
                    // Human UX contract: Nuvio's production player is the first
                    // consumer. A diagnostic GET before playback can consume a
                    // signed/one-shot URL and manufacture a false failure.
                    emit("FIELD_NATIVE_PLAYER_BEGIN client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index entry=nuvio-production-player")
                    val reader = probeNativePlayer(row.url, row.headers, row.type, __EXPECTED_MINUTES__)
                    emit("FIELD_NATIVE_PLAYER client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index state=${reader.state} engine=${reader.engine} production_surface=true advertised_quality64=${b64(row.quality)} http_status=${reader.httpStatus} failure_stage=${reader.failureStage} duration_seconds=${reader.durationSeconds ?: 0.0} video_width=${reader.videoWidth} video_height=${reader.videoHeight} diagnostic_first_frame_ms=${reader.diagnosticFirstFrameMs} diagnostic_played=${reader.diagnosticPlayed} diagnostic_late_format=${reader.diagnosticLateFormat} host64=${b64(reader.host)} error_class64=${b64(reader.errorClass)} error_code64=${b64(reader.errorCode)} exception_chain64=${b64(reader.exceptionChain)} response_header_names64=${b64(reader.responseHeaderNames)} load_bytes=${reader.loadBytes} load_duration_ms=${reader.loadDurationMs} media_data_type=${reader.mediaDataType} track_type=${reader.trackType} audio_track_count=${reader.audioTrackCount} audio_track_languages64=${b64(reader.audioTrackLanguages)} subtitle_track_count=${reader.subtitleTrackCount} subtitle_track_languages64=${b64(reader.subtitleTrackLanguages)} subtitle_track_labels64=${b64(reader.subtitleTrackLabels)}")
__ENGINE_COMPARE_BLOCK__                    val transport = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client=__CLIENT__ fixture=$fixtureSlug provider64=${b64(provider.id)} index=$index state=${transport.state} kind=${transport.kind} status=${transport.status} content_type64=${b64(transport.contentType)} extm3u=${transport.extm3u} audio_track_count=${transport.audioTrackCount} audio_track_languages64=${b64(transport.audioTrackLanguages)} subtitle_track_count=${transport.subtitleTrackCount} subtitle_track_languages64=${b64(transport.subtitleTrackLanguages)} audio_variant_matrix64=${b64(transport.audioVariantMatrix)} subtitle_variant_matrix64=${b64(transport.subtitleVariantMatrix)} variant_heights64=${b64(transport.variantHeights)} variant_codecs64=${b64(transport.variantCodecs)} duration_seconds=${transport.durationSeconds ?: 0.0} host64=${b64(transport.host)} media_hint64=${b64(transport.mediaHint)}")
                }
'''


def augment_android_test(
    source: str,
    *,
    client: str,
    expected_duration_minutes: int | float | None = None,
    max_player_probes: int = 1,
    compare_engines: bool = False,
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
    helpers = (TV_HELPERS if client == "tv" else MOBILE_HELPERS).replace("__PLAYER_TIMEOUT_MS__", "25000")
    # Only an isolated SHA-attested official TV candidate pays the bounded
    # format-settlement wait; broad provider cohorts remain fast and unchanged.
    settle_ms = "4500" if (client == "tv" and os.environ.get("NIAKVIO_NATIVE_CANDIDATE_SHA256")) else "0"
    helpers = helpers.replace("__PLAYER_FORMAT_SETTLE_MS__", settle_ms)
    visible_hold_ms = "2400" if (client == "tv" and os.environ.get("NIAKVIO_NATIVE_CANDIDATE_SHA256")) else "0"
    helpers = helpers.replace("__PLAYER_VISIBLE_HOLD_MS__", visible_hold_ms)
    if source.count(TEST_ANCHOR) != 1:
        raise ValueError("test anchor missing or ambiguous")
    source = source.replace(TEST_ANCHOR, helpers + "\n" + TEST_ANCHOR, 1)
    old = OLD_ANDROID_PROBE_BLOCK.replace("__CLIENT__", client)
    if source.count(old) != 1:
        raise ValueError(f"transport probe anchor missing for {client}: count={source.count(old)}")
    engine_compare = MOBILE_ENGINE_COMPARE_BLOCK if client == "mobile" and compare_engines else ""
    new = (
        NEW_ANDROID_PROBE_BLOCK.replace("__CLIENT__", client)
        .replace("__MAX_PROBES__", str(max_player_probes))
        .replace("__EXPECTED_MINUTES__", str(expected))
        .replace("__ENGINE_COMPARE_BLOCK__", engine_compare)
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
