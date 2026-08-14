package com.nuvio.app.features.plugins

import com.nuvio.app.features.plugins.runtime.PluginRuntime
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class NiakvioRealProviderDesktopTest {
    private data class ProviderCase(
        val id: String,
        val enabled: Boolean,
        val version: String,
        val filename: String,
        val bundle: File,
    )

    private val workspace = File(System.getenv("GITHUB_WORKSPACE"))
    private val runtimeRoot = File(workspace, "desktop-real-client-runtime")
    private val resultFile = File(workspace, "desktop-real-client-results.log")

    private fun emit(message: String) {
        println(message)
        resultFile.appendText(message + "\n")
    }

    private fun providers(): List<ProviderCase> =
        File(runtimeRoot, "selection.tsv").readLines()
            .filter { it.isNotBlank() }
            .map { line ->
                val parts = line.split('\t')
                require(parts.size == 5) { "invalid selection row: $line" }
                ProviderCase(
                    id = parts[0],
                    enabled = parts[1] == "true",
                    version = parts[2],
                    filename = parts[3],
                    bundle = File(runtimeRoot, parts[4]),
                )
            }

    private fun requestText(url: String, headers: Map<String, String>?): Pair<String, String> {
        val connection = URL(url).openConnection() as HttpURLConnection
        connection.instanceFollowRedirects = true
        connection.connectTimeout = 10_000
        connection.readTimeout = 15_000
        headers.orEmpty().forEach { (key, value) -> connection.setRequestProperty(key, value) }
        try {
            val status = connection.responseCode
            assertTrue(status in 200..299, "Media transport must be HTTP-successful: $url status=$status")
            val contentType = connection.contentType.orEmpty()
            val body = connection.inputStream.bufferedReader().use { it.readText() }
            return contentType to body
        } finally {
            connection.disconnect()
        }
    }

    @Test
    fun exactMonNinjaProviders() = runBlocking {
        resultFile.writeText("")
        val cases = providers()
        assertEquals(setOf("moviebox", "netmirror", "streamzo"), cases.map { it.id }.toSet())
        cases.forEach { provider ->
            emit(
                "FIELD_DESKTOP_SELECTED provider=${provider.id} enabled=${provider.enabled} " +
                    "version=${provider.version} filename=${provider.filename}"
            )
            val started = System.currentTimeMillis()
            val rows = PluginRuntime.executePlugin(
                code = provider.bundle.readText(),
                tmdbId = "1215638",
                mediaType = "movie",
                season = null,
                episode = null,
                scraperId = provider.id,
            )
            emit(
                "FIELD_DESKTOP_RESULT provider=${provider.id} enabled=${provider.enabled} " +
                    "duration_ms=${System.currentTimeMillis()-started} count=${rows.size}"
            )
            rows.forEachIndexed { index, row ->
                emit("FIELD_DESKTOP_ROW provider=${provider.id} index=$index title=${row.title} name=${row.name} quality=${row.quality} language=${row.language} type=${row.type} url=${row.url} headers=${row.headers}")
                assertFalse(row.url.contains("youtube.com/embed", ignoreCase = true), "HTML YouTube embed must never reach desktop player")
            }
            if (!provider.enabled) {
                assertTrue(rows.isEmpty(), "Disabled/quarantined provider ${provider.id} must be inert")
                return@forEach
            }
            if (provider.id == "streamzo") {
                assertTrue(rows.isNotEmpty(), "StreamZo must resolve Mon Ninja 3 in official desktop runtime")
                val hlsRow = requireNotNull(rows.firstOrNull { it.url.contains(".m3u8", ignoreCase = true) }) {
                    "StreamZo must expose HLS on desktop"
                }
                val (contentType, body) = requestText(hlsRow.url, hlsRow.headers)
                emit("FIELD_DESKTOP_STREAMZO_TRANSPORT contentType=$contentType extm3u=${body.contains("#EXTM3U")}")
                assertTrue(body.contains("#EXTM3U"), "StreamZo desktop transport must be HLS")
                assertFalse(contentType.contains("text/html", ignoreCase = true), "StreamZo desktop transport must not be HTML")
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
        emit("FIELD_DESKTOP_METADATA_NULL_ACCEPTED=true")

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
        emit("FIELD_DESKTOP_METADATA_LITERAL_UNKNOWN_ACCEPTED=true")
    }
}
