package com.nuvio.tv.core.plugin

import android.util.Log
import androidx.test.platform.app.InstrumentationRegistry
import java.net.URL
import kotlinx.coroutines.runBlocking
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class NiakvioTvRealProviderTest {
    private data class ProviderCase(
        val id: String,
        val enabled: Boolean,
        val version: String,
        val filename: String,
        val asset: String,
    )

    private val runtime = PluginRuntime()
    private val http = OkHttpClient()

    private fun emit(message: String) {
        println(message)
        Log.i("NiakvioTvRealLab", message)
    }

    private fun assetText(relative: String): String =
        InstrumentationRegistry.getInstrumentation().context.assets.open(relative)
            .bufferedReader().use { it.readText() }

    private fun providers(): List<ProviderCase> {
        val rows = JSONArray(assetText("niakvio/selection.json"))
        return (0 until rows.length()).map { index ->
            val row = rows.getJSONObject(index)
            ProviderCase(
                id = row.getString("id"),
                enabled = row.getBoolean("enabled"),
                version = row.getString("version"),
                filename = row.getString("filename"),
                asset = row.getString("asset"),
            )
        }
    }

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
    fun exactMonNinjaProvidersOnOfficialTvRuntime() = runBlocking {
        val cases = providers()
        assertEquals(setOf("moviebox", "netmirror", "streamzo"), cases.map { it.id }.toSet())
        cases.forEach { provider ->
            emit(
                "FIELD_TV_SELECTED provider=${provider.id} enabled=${provider.enabled} " +
                    "version=${provider.version} filename=${provider.filename}"
            )
            val started = System.currentTimeMillis()
            val rows = runtime.executePlugin(
                code = assetText(provider.asset),
                tmdbId = "1215638",
                mediaType = "movie",
                season = null,
                episode = null,
                scraperId = provider.id,
            )
            emit(
                "FIELD_TV_RESULT provider=${provider.id} enabled=${provider.enabled} " +
                    "duration_ms=${System.currentTimeMillis()-started} count=${rows.size}"
            )
            rows.forEachIndexed { index, row ->
                emit("FIELD_TV_ROW provider=${provider.id} index=$index title=${row.title} name=${row.name} quality=${row.quality} size=${row.size} language=${row.language} providerField=${row.provider} type=${row.type} url=${row.url} headers=${row.headers}")
                assertFalse("HTML YouTube embed must never reach TV player", row.url.contains("youtube.com/embed", ignoreCase = true))
            }

            if (!provider.enabled) {
                assertTrue("Disabled/quarantined provider ${provider.id} must be inert", rows.isEmpty())
                return@forEach
            }

            if (provider.id == "netmirror" && rows.isNotEmpty()) {
                rows.filter { it.url.contains(".m3u8", ignoreCase = true) }.forEach { row ->
                    val seconds = hlsDurationSeconds(row.url, row.headers)
                    if (seconds != null) {
                        emit("FIELD_TV_NETMIRROR_DURATION seconds=$seconds")
                        assertTrue("NetMirror duration is implausibly short for Mon Ninja 3", seconds >= 45 * 60)
                        assertTrue("NetMirror duration is implausibly long for Mon Ninja 3", seconds <= 130 * 60)
                    }
                }
            }

            if (provider.id == "streamzo") {
                assertTrue("StreamZo must resolve Mon Ninja 3 in official TV runtime", rows.isNotEmpty())
                val hlsRow = requireNotNull(rows.firstOrNull { it.url.contains(".m3u8", ignoreCase = true) }) {
                    "StreamZo must expose HLS on TV"
                }
                val (contentType, body) = requestText(hlsRow.url, hlsRow.headers)
                emit("FIELD_TV_STREAMZO_TRANSPORT contentType=$contentType extm3u=${body.contains("#EXTM3U")}")
                assertTrue("StreamZo TV HLS must be an HLS manifest", body.contains("#EXTM3U"))
                assertFalse("StreamZo TV transport must not be HTML", contentType.contains("text/html", ignoreCase = true))
            }
        }
    }

    @Test
    fun missingAndUnknownMetadataAreAcceptedByOfficialTvRuntime() = runBlocking {
        val missing = runtime.executePlugin(
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
        assertNull(missing.single().size)
        emit("FIELD_TV_METADATA_MISSING_ACCEPTED=true")

        val unknown = runtime.executePlugin(
            code = "module.exports.getStreams=async()=>[{title:'Metadata unknown',name:'Metadata provider',url:'https://example.test/video.mp4',quality:'Unknown',description:'Unknown'}];",
            tmdbId = "1215638",
            mediaType = "movie",
            season = null,
            episode = null,
            scraperId = "metadata-unknown",
        )
        assertEquals(1, unknown.size)
        assertEquals("Unknown", unknown.single().quality)
        emit("FIELD_TV_METADATA_LITERAL_UNKNOWN_ACCEPTED=true")
    }
}
