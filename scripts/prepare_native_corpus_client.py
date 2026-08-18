#!/usr/bin/env python3
"""Prepare exactly one official Nuvio client for the native corpus lab.

The corpus follows the same path as a user: provider runtime, transport, then the
client's real reader. A returned URL is evidence only; playback READY is the final
proof. Reader failures remain observations for Repair and Brain rather than test
infrastructure failures.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_corpus_validation as corpus  # noqa: E402


def _collector_test(source: str, client: str) -> str:
    if client == "desktop":
        old = '        assertTrue(errors.isEmpty(), "native provider runtime errors: " + errors.take(12).joinToString(" | "))\n'
        new = '        assertTrue(providers.isNotEmpty(), "native corpus provider list must not be empty")\n'
    else:
        old = '        assertTrue("native provider runtime errors: " + errors.take(12).joinToString(" | "), errors.isEmpty())\n'
        new = '        assertTrue("native corpus provider list must not be empty", providers.isNotEmpty())\n'
    if source.count(old) != 1:
        raise SystemExit(f"unable to relax {client} provider-error assertion: anchor count={source.count(old)}")
    return source.replace(old, new, 1)


def _player_policy() -> tuple[int, int]:
    payload = json.loads((ROOT / ".github/triggers/nuvio-client-lab.json").read_text(encoding="utf-8"))
    max_streams = max(1, min(int(payload.get("max_streams_per_runtime") or 3), 5))
    timeout_ms = max(4_000, min(int(payload.get("playback_timeout_ms") or 18_000), 30_000))
    return max_streams, timeout_ms


COMMON_ANDROID_PLAYER_HELPERS = r'''
    data class NativeSourceProbe(
        val status: Int,
        val contentType: String,
        val signature: String,
        val finalHost: String,
        val acceptsRanges: Boolean,
    )

    data class NativeReaderAttempt(
        val state: String,
        val code: Int,
        val codeName: String,
        val cause: String,
        val mimeType: String,
        val durationMs: Long,
    )

    data class NativePlaybackProbe(
        val ready: Boolean,
        val engine: String,
        val exo: NativeReaderAttempt,
        val mpv: NativeReaderAttempt?,
        val source: NativeSourceProbe,
        val repairClass: String,
        val retryMime: String,
    )

    private fun sanitizeReaderCause(error: Throwable): String {
        val out = mutableListOf<String>()
        var current: Throwable? = error
        var depth = 0
        while (current != null && depth < 5) {
            val name = current::class.simpleName.orEmpty()
            val message = current.message.orEmpty()
                .replace(Regex("https?://\\S+"), "<url>")
                .replace(Regex("(?i)(authorization|cookie|token|secret)\\s*[:=]\\s*\\S+"), "$1=<redacted>")
            out += if (message.isBlank()) name else "$name:$message"
            current = current.cause
            depth++
        }
        return out.joinToString(" <- ").replace(Regex("\\s+"), " ").take(700)
    }

    private fun probeNativeSource(url: String, headers: Map<String, String>?): NativeSourceProbe {
        var connection: java.net.HttpURLConnection? = null
        return try {
            connection = java.net.URL(url).openConnection() as java.net.HttpURLConnection
            connection.instanceFollowRedirects = true
            connection.connectTimeout = 8_000
            connection.readTimeout = 10_000
            connection.setRequestProperty("Range", "bytes=0-4095")
            connection.setRequestProperty("Accept", "application/vnd.apple.mpegurl,application/x-mpegURL,application/dash+xml,video/*,*/*;q=0.8")
            headers.orEmpty().forEach { (key, value) ->
                if (!key.equals("Range", ignoreCase = true)) connection.setRequestProperty(key, value)
            }
            val status = connection.responseCode
            val contentType = connection.contentType.orEmpty().substringBefore(';').trim().lowercase()
            val input = if (status in 200..299) connection.inputStream else connection.errorStream
            val bytes = if (input == null) ByteArray(0) else input.use { stream ->
                val out = java.io.ByteArrayOutputStream()
                val buffer = ByteArray(1024)
                while (out.size() < 4096) {
                    val count = stream.read(buffer, 0, minOf(buffer.size, 4096 - out.size()))
                    if (count <= 0) break
                    out.write(buffer, 0, count)
                }
                out.toByteArray()
            }
            val text = runCatching { bytes.toString(Charsets.UTF_8).trimStart() }.getOrDefault("")
            val signature = when {
                text.startsWith("#EXTM3U", ignoreCase = true) -> "hls"
                text.startsWith("<MPD", ignoreCase = true) || (text.startsWith("<?xml") && text.contains("<MPD", ignoreCase = true)) -> "dash"
                bytes.size >= 8 && String(bytes.copyOfRange(4, 8), Charsets.ISO_8859_1) == "ftyp" -> "mp4_ftyp"
                bytes.size >= 4 && bytes[0].toInt() and 0xff == 0x1a && bytes[1].toInt() and 0xff == 0x45 && bytes[2].toInt() and 0xff == 0xdf && bytes[3].toInt() and 0xff == 0xa3 -> "matroska_ebml"
                bytes.size >= 376 && bytes[0].toInt() and 0xff == 0x47 && bytes[188].toInt() and 0xff == 0x47 -> "mpeg_ts"
                text.startsWith("<!doctype", ignoreCase = true) || text.startsWith("<html", ignoreCase = true) -> "html"
                text.startsWith("{") || text.startsWith("[") -> "json"
                bytes.isEmpty() -> "empty"
                else -> "unknown_binary"
            }
            NativeSourceProbe(
                status = status,
                contentType = contentType,
                signature = signature,
                finalHost = hostOnly(connection.url.toString()),
                acceptsRanges = status == 206 || connection.getHeaderField("Accept-Ranges")?.contains("bytes", ignoreCase = true) == true,
            )
        } catch (error: Throwable) {
            NativeSourceProbe(0, error::class.simpleName.orEmpty(), "probe_error", hostOnly(url), false)
        } finally {
            connection?.disconnect()
        }
    }

    private fun readerFailureClass(
        exo: NativeReaderAttempt,
        mpv: NativeReaderAttempt?,
        source: NativeSourceProbe,
    ): String {
        if (exo.state == "ready") return "healthy"
        if (source.status in setOf(401, 403, 407, 429, 451)) return "playback_context_gap"
        if (source.signature in setOf("html", "json", "empty", "probe_error")) return "media_extraction_gap"
        return when (exo.codeName) {
            "ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED" -> if (mpv?.state == "ready") "player_engine_compatibility_gap" else "player_container_unsupported"
            "ERROR_CODE_PARSING_CONTAINER_MALFORMED" -> "player_container_malformed"
            "ERROR_CODE_PARSING_MANIFEST_UNSUPPORTED",
            "ERROR_CODE_PARSING_MANIFEST_MALFORMED" -> "player_manifest_gap"
            "ERROR_CODE_DECODING_FAILED",
            "ERROR_CODE_DECODING_FORMAT_EXCEEDS_CAPABILITIES",
            "ERROR_CODE_DECODING_FORMAT_UNSUPPORTED",
            "ERROR_CODE_DECODING_FORMAT_UNSUPPORTED_DRM" -> "player_decoder_gap"
            else -> if (mpv?.state == "ready") "player_engine_compatibility_gap" else "player_runtime_gap"
        }
    }
'''


TV_PLAYER_IMPORTS = r'''import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import com.nuvio.tv.ui.screens.player.NuvioMpvSurfaceView
import com.nuvio.tv.ui.screens.player.PlayerMediaSourceFactory
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
'''


TV_PLAYER_HELPERS = r'''
    private suspend fun probeTvExo(
        url: String,
        headers: Map<String, String>?,
        mimeOverride: String? = null,
    ): NativeReaderAttempt = withContext(Dispatchers.Main) {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val request = PlayerMediaSourceFactory.normalizePlaybackRequest(url, headers)
        val factory = PlayerMediaSourceFactory(context).apply {
            useParallelConnections = false
            vodCacheEnabled = false
            nuvioPerformanceModeEnabled = false
        }
        val player = ExoPlayer.Builder(context).build()
        val result = CompletableDeferred<NativeReaderAttempt>()
        val listener = object : Player.Listener {
            override fun onPlaybackStateChanged(playbackState: Int) {
                if (playbackState == Player.STATE_READY && !result.isCompleted) {
                    result.complete(
                        NativeReaderAttempt(
                            state = "ready",
                            code = 0,
                            codeName = "READY",
                            cause = "",
                            mimeType = mimeOverride.orEmpty(),
                            durationMs = player.duration.coerceAtLeast(0L),
                        )
                    )
                }
            }

            override fun onPlayerError(error: PlaybackException) {
                if (!result.isCompleted) {
                    result.complete(
                        NativeReaderAttempt(
                            state = "error",
                            code = error.errorCode,
                            codeName = error.errorCodeName,
                            cause = sanitizeReaderCause(error),
                            mimeType = mimeOverride.orEmpty(),
                            durationMs = player.duration.coerceAtLeast(0L),
                        )
                    )
                }
            }
        }
        player.addListener(listener)
        try {
            val mediaSource = factory.createMediaSource(
                context = context,
                url = request.url,
                headers = request.headers,
                filename = null,
                responseHeaders = emptyMap(),
                mimeTypeOverride = mimeOverride,
            )
            player.setMediaSource(mediaSource)
            player.playWhenReady = false
            player.prepare()
            withTimeoutOrNull(PLAYER_TIMEOUT_MS) { result.await() }
                ?: NativeReaderAttempt("timeout", 0, "TIMEOUT", "", mimeOverride.orEmpty(), player.duration.coerceAtLeast(0L))
        } catch (error: Throwable) {
            NativeReaderAttempt("exception", 0, error::class.simpleName.orEmpty(), sanitizeReaderCause(error), mimeOverride.orEmpty(), player.duration.coerceAtLeast(0L))
        } finally {
            player.removeListener(listener)
            player.release()
            factory.shutdown()
        }
    }

    private suspend fun probeTvMpv(url: String, headers: Map<String, String>?): NativeReaderAttempt {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        var view: NuvioMpvSurfaceView? = null
        return try {
            withContext(Dispatchers.Main) {
                view = NuvioMpvSurfaceView(context)
                view!!.ensureInitialized()
                view!!.setMedia(url, headers.orEmpty())
                view!!.setPaused(false)
            }
            val deadline = android.os.SystemClock.elapsedRealtime() + PLAYER_TIMEOUT_MS
            var duration = 0L
            var video = false
            var idle = true
            while (android.os.SystemClock.elapsedRealtime() < deadline) {
                withContext(Dispatchers.Main) {
                    duration = view?.durationMs() ?: 0L
                    video = view?.hasVideoTrackSelectedNow() == true
                    idle = view?.isCoreIdleNow() != false
                }
                if (video && (duration > 0L || !idle)) {
                    return NativeReaderAttempt("ready", 0, "MPV_READY", "", "", duration)
                }
                delay(350L)
            }
            NativeReaderAttempt("timeout", 0, "MPV_TIMEOUT", "video=$video idle=$idle", "", duration)
        } catch (error: Throwable) {
            NativeReaderAttempt("exception", 0, error::class.simpleName.orEmpty(), sanitizeReaderCause(error), "", 0L)
        } finally {
            withContext(Dispatchers.Main) { runCatching { view?.releasePlayer() } }
        }
    }

    private suspend fun probeClientPlayback(url: String, headers: Map<String, String>?, streamType: String?): NativePlaybackProbe {
        val source = withContext(Dispatchers.IO) { probeNativeSource(url, headers) }
        val request = PlayerMediaSourceFactory.normalizePlaybackRequest(url, headers)
        val initialMime = PlayerMediaSourceFactory.inferMimeType(request.url, null, emptyMap()).orEmpty()
        var exo = probeTvExo(url, headers)
        var retryMime = ""
        if (exo.codeName == "ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED") {
            val probedMime = PlayerMediaSourceFactory.probeNetworkMimeType(request.url, request.headers)
            if (!probedMime.isNullOrBlank() && probedMime != initialMime) {
                retryMime = probedMime
                exo = probeTvExo(url, headers, probedMime)
            }
        }
        val obviousNonMedia = source.signature in setOf("html", "json", "empty", "probe_error")
        val mpv = if (exo.state == "ready" || obviousNonMedia) null else probeTvMpv(url, headers)
        val repair = readerFailureClass(exo, mpv, source)
        val ready = exo.state == "ready" || mpv?.state == "ready"
        val engine = when {
            exo.state == "ready" -> "exo"
            mpv?.state == "ready" -> "mpv"
            else -> "none"
        }
        return NativePlaybackProbe(ready, engine, exo, mpv, source, repair, retryMime)
    }
'''


MOBILE_PLAYER_IMPORTS = r'''import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.exoplayer.DefaultRenderersFactory
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory
import androidx.media3.extractor.DefaultExtractorsFactory
import com.nuvio.app.features.player.AndroidLibmpvVideoOutput
import com.nuvio.app.features.player.PlatformPlaybackDataSourceFactory
import com.nuvio.app.features.player.playbackMediaItemFromUrl
import com.nuvio.app.features.player.probeMimeType
import `is`.xyz.mpv.BaseMPVView
import `is`.xyz.mpv.Utils
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
'''


MOBILE_PLAYER_HELPERS = r'''
    private suspend fun probeMobileExo(
        url: String,
        headers: Map<String, String>?,
        streamType: String?,
        mimeOverride: String? = null,
    ): NativeReaderAttempt = withContext(Dispatchers.Main) {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val requestHeaders = headers.orEmpty()
        val dataSourceFactory = PlatformPlaybackDataSourceFactory.create(
            context = context,
            defaultRequestHeaders = requestHeaders,
            defaultResponseHeaders = emptyMap(),
            useYoutubeChunkedPlayback = false,
        )
        val renderers = DefaultRenderersFactory(context).setEnableDecoderFallback(true)
        val player = ExoPlayer.Builder(context, renderers).build()
        val result = CompletableDeferred<NativeReaderAttempt>()
        val listener = object : Player.Listener {
            override fun onPlaybackStateChanged(playbackState: Int) {
                if (playbackState == Player.STATE_READY && !result.isCompleted) {
                    result.complete(NativeReaderAttempt("ready", 0, "READY", "", mimeOverride.orEmpty(), player.duration.coerceAtLeast(0L)))
                }
            }

            override fun onPlayerError(error: PlaybackException) {
                if (!result.isCompleted) {
                    result.complete(
                        NativeReaderAttempt(
                            "error",
                            error.errorCode,
                            error.errorCodeName,
                            sanitizeReaderCause(error),
                            mimeOverride.orEmpty(),
                            player.duration.coerceAtLeast(0L),
                        )
                    )
                }
            }
        }
        player.addListener(listener)
        try {
            val item = if (mimeOverride.isNullOrBlank()) {
                playbackMediaItemFromUrl(url = url, responseHeaders = emptyMap(), streamType = streamType)
            } else {
                MediaItem.Builder().setUri(url).setMimeType(mimeOverride).build()
            }
            val mediaSource = DefaultMediaSourceFactory(dataSourceFactory, DefaultExtractorsFactory()).createMediaSource(item)
            player.setMediaSource(mediaSource)
            player.playWhenReady = false
            player.prepare()
            withTimeoutOrNull(PLAYER_TIMEOUT_MS) { result.await() }
                ?: NativeReaderAttempt("timeout", 0, "TIMEOUT", "", mimeOverride.orEmpty(), player.duration.coerceAtLeast(0L))
        } catch (error: Throwable) {
            NativeReaderAttempt("exception", 0, error::class.simpleName.orEmpty(), sanitizeReaderCause(error), mimeOverride.orEmpty(), player.duration.coerceAtLeast(0L))
        } finally {
            player.removeListener(listener)
            player.release()
        }
    }

    private suspend fun probeMobileMpv(url: String, headers: Map<String, String>?): NativeReaderAttempt {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        var view: BaseMPVView? = null
        return try {
            withContext(Dispatchers.Main) {
                Utils.copyAssets(context)
                val clazz = Class.forName("com.nuvio.app.features.player.NuvioLibmpvView")
                val constructor = clazz.declaredConstructors.firstOrNull { it.parameterTypes.size == 5 }
                    ?: error("NuvioLibmpvView primary constructor unavailable")
                constructor.isAccessible = true
                val instance = constructor.newInstance(context, AndroidLibmpvVideoOutput.Gpu, true, false, null)
                view = instance as BaseMPVView
                view!!.initialize(context.filesDir.path, context.cacheDir.path)
                val load = clazz.declaredMethods.firstOrNull { it.name == "loadSource" && it.parameterTypes.size == 5 }
                    ?: error("NuvioLibmpvView.loadSource unavailable")
                load.isAccessible = true
                load.invoke(instance, url, null, headers.orEmpty(), emptyList<Any>(), false)
            }
            val deadline = android.os.SystemClock.elapsedRealtime() + PLAYER_TIMEOUT_MS
            var duration = 0L
            var video = false
            var idle = true
            while (android.os.SystemClock.elapsedRealtime() < deadline) {
                withContext(Dispatchers.Main) {
                    duration = ((view?.mpv?.getPropertyDouble("duration") ?: 0.0) * 1000.0).toLong().coerceAtLeast(0L)
                    val vid = view?.mpv?.getPropertyString("vid")?.trim()
                    video = !vid.isNullOrBlank() && !vid.equals("no", ignoreCase = true)
                    idle = view?.mpv?.getPropertyBoolean("core-idle") ?: true
                }
                if (video && (duration > 0L || !idle)) {
                    return NativeReaderAttempt("ready", 0, "MPV_READY", "", "", duration)
                }
                delay(350L)
            }
            NativeReaderAttempt("timeout", 0, "MPV_TIMEOUT", "video=$video idle=$idle", "", duration)
        } catch (error: Throwable) {
            NativeReaderAttempt("exception", 0, error::class.simpleName.orEmpty(), sanitizeReaderCause(error), "", 0L)
        } finally {
            withContext(Dispatchers.Main) { runCatching { view?.destroy() } }
        }
    }

    private suspend fun probeClientPlayback(url: String, headers: Map<String, String>?, streamType: String?): NativePlaybackProbe {
        val source = withContext(Dispatchers.IO) { probeNativeSource(url, headers) }
        var exo = probeMobileExo(url, headers, streamType)
        var retryMime = ""
        val sourceError = exo.cause.contains("UnrecognizedInputFormatException") ||
            exo.codeName == "ERROR_CODE_IO_UNSPECIFIED" ||
            exo.codeName == "ERROR_CODE_BEHIND_LIVE_WINDOW"
        if (exo.state != "ready" && sourceError) {
            val probedMime = withContext(Dispatchers.IO) { probeMimeType(url, headers.orEmpty()) }
            if (!probedMime.isNullOrBlank()) {
                retryMime = probedMime
                exo = probeMobileExo(url, headers, streamType, probedMime)
            }
        }
        val obviousNonMedia = source.signature in setOf("html", "json", "empty", "probe_error")
        val mpv = if (exo.state == "ready" || obviousNonMedia) null else probeMobileMpv(url, headers)
        val repair = readerFailureClass(exo, mpv, source)
        val ready = exo.state == "ready" || mpv?.state == "ready"
        val engine = when {
            exo.state == "ready" -> "exo"
            mpv?.state == "ready" -> "mpv"
            else -> "none"
        }
        return NativePlaybackProbe(ready, engine, exo, mpv, source, repair, retryMime)
    }
'''


def _android_player_test(source: str, client: str) -> str:
    if client not in {"mobile", "tv"}:
        return source
    max_streams, timeout_ms = _player_policy()
    import_anchor = "import android.util.Log\n"
    imports = TV_PLAYER_IMPORTS if client == "tv" else MOBILE_PLAYER_IMPORTS
    if source.count(import_anchor) != 1:
        raise SystemExit(f"{client} player import anchor count={source.count(import_anchor)}")
    source = source.replace(import_anchor, import_anchor + imports, 1)

    test_anchor = "    @Test\n    fun selectedFixtureAcrossEveryProvider()"
    if source.count(test_anchor) != 1:
        raise SystemExit(f"{client} player helper anchor count={source.count(test_anchor)}")
    helpers = COMMON_ANDROID_PLAYER_HELPERS + (TV_PLAYER_HELPERS if client == "tv" else MOBILE_PLAYER_HELPERS)
    constants = f"\n    private val PLAYER_TIMEOUT_MS = {timeout_ms}L\n    private val PLAYER_MAX_STREAMS = {max_streams}\n"
    source = source.replace(test_anchor, constants + helpers + "\n" + test_anchor, 1)

    start = source.find("                rows.firstOrNull()?.let { row ->")
    end = source.find("            } catch (error: Throwable)", start)
    if start < 0 or end < 0:
        raise SystemExit(f"{client} transport/player loop anchor missing")
    replacement = f'''                var providerPlaybackReady = false
                for ((index, row) in rows.take(PLAYER_MAX_STREAMS).withIndex()) {{
                    val probe = probeTransport(row.url, row.headers)
                    emit("FIELD_NATIVE_TRANSPORT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} index=$index state=${{probe.state}} kind=${{probe.kind}} status=${{probe.status}} content_type64=${{b64(probe.contentType)}} extm3u=${{probe.extm3u}} duration_seconds=${{probe.durationSeconds ?: 0.0}} host64=${{b64(probe.host)}} media_hint64=${{b64(probe.mediaHint)}}")
                    if (providerPlaybackReady) continue
                    val playback = probeClientPlayback(row.url, row.headers, row.type)
                    emit(
                        "FIELD_NATIVE_PLAYBACK client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} index=$index " +
                        "state=${{if (playback.ready) "ready" else "error"}} engine=${{playback.engine}} repair_class=${{playback.repairClass}} " +
                        "source_status=${{playback.source.status}} signature=${{playback.source.signature}} ranges=${{playback.source.acceptsRanges}} " +
                        "content_type64=${{b64(playback.source.contentType)}} final_host64=${{b64(playback.source.finalHost)}} " +
                        "exo_state=${{playback.exo.state}} exo_code=${{playback.exo.code}} exo_name=${{playback.exo.codeName}} " +
                        "exo_cause64=${{b64(playback.exo.cause)}} retry_mime64=${{b64(playback.retryMime)}} " +
                        "mpv_state=${{playback.mpv?.state ?: "not_needed"}} mpv_name=${{playback.mpv?.codeName ?: ""}} mpv_cause64=${{b64(playback.mpv?.cause)}}"
                    )
                    if (playback.ready) providerPlaybackReady = true
                }}
                if (rows.isNotEmpty()) {{
                    emit("FIELD_NATIVE_PLAYBACK_PROVIDER client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=${{if (providerPlaybackReady) "ready" else "unplayable"}}")
                }}
'''
    return source[:start] + replacement + source[end:]


def player_test(source: str, client: str) -> str:
    """Embed reader proof in the existing native corpus generated test."""
    return _android_player_test(source, client)


def _isolate_tv_android_test_sources(tv: Path) -> int:
    removed = 0
    for source_dir in (tv / "app/src/androidTest/java", tv / "app/src/androidTest/kotlin"):
        if not source_dir.is_dir():
            continue
        for source in source_dir.rglob("*"):
            if source.is_file() and source.suffix.lower() in {".kt", ".java"}:
                source.unlink()
                removed += 1
    print(f"FIELD_NATIVE_CORPUS_TV_TEST_SOURCES_ISOLATED removed={removed}")
    return removed


def prepare_desktop(workspace: Path, fixture: dict) -> None:
    providers = corpus.stage_providers(ROOT / "native-corpus-stage")
    target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_collector_test(corpus.desktop_test(fixture, providers), "desktop"), encoding="utf-8")


def prepare_mobile(workspace: Path, fixture: dict) -> None:
    mobile = workspace / "nuvio-mobile"
    corpus.enable_mobile_device_tests(mobile)
    assets = mobile / "composeApp/src/androidDeviceTest/assets/niakvio"
    providers = corpus.stage_providers(assets)
    target = mobile / "composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    generated = _collector_test(corpus.android_test(fixture, providers, "mobile"), "mobile")
    target.write_text(player_test(generated, "mobile"), encoding="utf-8")


def prepare_tv(workspace: Path, fixture: dict) -> None:
    tv = workspace / "nuvio-tv"
    corpus.enable_tv_tests(tv)
    _isolate_tv_android_test_sources(tv)
    assets = tv / "app/src/androidTest/assets/niakvio"
    providers = corpus.stage_providers(assets)
    target = tv / "app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
    target.parent.mkdir(parents=True, exist_ok=True)
    generated = _collector_test(corpus.android_test(fixture, providers, "tv"), "tv")
    target.write_text(player_test(generated, "tv"), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "mobile", "tv"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    workspace = Path(args.workspace).resolve()
    {"desktop": prepare_desktop, "mobile": prepare_mobile, "tv": prepare_tv}[args.target](workspace, fixture)
    print(
        f"FIELD_NATIVE_CORPUS_PREPARED_ISOLATED target={args.target} fixture={args.fixture} "
        f"title={fixture.get('title')} tmdb={fixture.get('tmdbId')} player_proof={'true' if args.target in {'mobile', 'tv'} else 'pending-desktop-native'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
