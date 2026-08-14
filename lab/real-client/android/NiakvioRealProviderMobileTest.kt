package com.nuvio.app.features.plugins

import android.util.Log
import androidx.test.platform.app.InstrumentationRegistry
import com.nuvio.app.features.plugins.runtime.PluginRuntime
import java.net.URL
import kotlinx.coroutines.runBlocking
import okhttp3.OkHttpClient
import okhttp3.Request
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class NiakvioRealProviderMobileTest {
    private val http = OkHttpClient()
    private val providers = listOf(
        "moviebox" to "niakvio/moviebox--published-baseline--1c0c9c423a094e0d.js",
        "netmirror" to "niakvio/netmirror--published-baseline--ccbd35984c20fc8b.js",
        "streamzo" to "niakvio/streamzo--published-baseline--bc19a7586f9f3bb8.js",
    )

    private fun emit(message: String) {
        println(message)
        Log.i("NiakvioRealLab", message)
    }

    private fun providerCode(relative: String): String =
        InstrumentationRegistry.getInstrumentation().context.assets.open(relative)
            .bufferedReader().use { it.readText() }

    private fun requestText(url: String, headers: Map<String, String>?): Pair<String, String> {
        val builder = Request.Builder().url(url)
        headers.orEmpty().forEach { (key, value) -> builder.header(key, value) }
        http.newCall(builder.build()).execute().use { response ->
            assertTrue("Media transport must be HTTP-successful: $url status=${response.code}", response.isSuccessful)
            return response.header("Content-Type").orEmpty() to response.body?.string().orEmpty()
        }
    }

    private fun hlsDurationSeconds(url: String, headers: Map<String, String>?, depth: Int = 0): Double? {
        if (depth > 1) return null
        val (_, text) = requestText(url, headers)
        if (!text.contains("#EXTM3U")) return null
        val durations = Regex("#EXTINF:([0-9.]+)").findAll(text)
            .mapNotNull { it.groupValues.getOrNull(1)?.toDoubleOrNull() }
            .toList()
        if (durations.isNotEmpty()) return durations.sum()
        val variant = text.lineSequence()
            .map { it.trim() }
            .firstOrNull { it.isNotEmpty() && !it.startsWith("#") && it.contains(".m3u8") }
            ?: return null
        return hlsDurationSeconds(URL(URL(url), variant).toString(), headers, depth + 1)
    }

    @Test
    fun exactMonNinjaProviders() = runBlocking {
        providers.forEach { (id, relative) ->
            val started = System.currentTimeMillis()
            val rows = PluginRuntime.executePlugin(
                code = providerCode(relative),
                tmdbId = "1215638",
                mediaType = "movie",
                season = null,
                episode = null,
                scraperId = id,
            )
            emit("FIELD_ANDROID_RESULT provider=$id duration_ms=${System.currentTimeMillis()-started} count=${rows.size}")
            rows.forEachIndexed { index, row ->
                emit("FIELD_ANDROID_ROW provider=$id index=$index title=${row.title} name=${row.name} quality=${row.quality} language=${row.language} type=${row.type} url=${row.url} headers=${row.headers}")
                assertFalse("HTML YouTube embed must never reach Android player", row.url.contains("youtube.com/embed", ignoreCase = true))
            }

            if (id == "netmirror" && rows.isNotEmpty()) {
                rows.filter { it.url.contains(".m3u8", ignoreCase = true) }.forEach { row ->
                    val seconds = hlsDurationSeconds(row.url, row.headers)
                    if (seconds != null) {
                        emit("FIELD_ANDROID_NETMIRROR_DURATION seconds=$seconds")
                        assertTrue("NetMirror duration is implausibly short for Mon Ninja 3", seconds >= 45 * 60)
                        assertTrue("NetMirror duration is implausibly long for Mon Ninja 3", seconds <= 130 * 60)
                    }
                }
            }

            if (id == "streamzo") {
                assertTrue("StreamZo must resolve Mon Ninja 3 in official Android runtime", rows.isNotEmpty())
                val hls = rows.firstOrNull { it.url.contains(".m3u8", ignoreCase = true) }
                assertTrue("StreamZo must expose HLS on Android", hls != null)
                val hlsRow = requireNotNull(hls)
                val (contentType, body) = requestText(hlsRow.url, hlsRow.headers)
                emit("FIELD_ANDROID_STREAMZO_TRANSPORT contentType=$contentType extm3u=${body.contains("#EXTM3U")}")
                assertTrue("StreamZo Android transport must be HLS", body.contains("#EXTM3U"))
                assertFalse("StreamZo Android transport must not be HTML", contentType.contains("text/html", ignoreCase = true))
            }
        }
    }

    @Test
    fun missingAndUnknownOptionalMetadataAreAccepted() = runBlocking {
        val missing = PluginRuntime.executePlugin(
            code = "module.exports.getStreams=async()=>[{title:'Metadata missing',url:'https://example.test/video.mp4'}];",
            tmdbId = "1215638",
            mediaType = "movie",
            season = null,
            episode = null,
            scraperId = "metadata-missing",
        )
        assertEquals(1, missing.size)
        assertNull(missing.single().quality)
        assertNull(missing.single().language)
        emit("FIELD_ANDROID_METADATA_NULL_ACCEPTED=true")

        val unknown = PluginRuntime.executePlugin(
            code = "module.exports.getStreams=async()=>[{title:'Metadata unknown',name:'Metadata provider',url:'https://example.test/video.mp4',quality:'Unknown',description:'Unknown'}];",
            tmdbId = "1215638",
            mediaType = "movie",
            season = null,
            episode = null,
            scraperId = "metadata-unknown",
        )
        assertEquals(1, unknown.size)
        assertEquals("Unknown", unknown.single().quality)
        emit("FIELD_ANDROID_METADATA_LITERAL_UNKNOWN_ACCEPTED=true")
    }
}
