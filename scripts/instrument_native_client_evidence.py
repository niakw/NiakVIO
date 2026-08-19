#!/usr/bin/env python3
"""Inject passive, sanitized evidence logging into ephemeral official Nuvio checkouts.

The lab must observe the exact client runtime used by Nuvio without changing request
semantics. This patch only emits method/endpoint/header-name/status/timing metadata.
It never logs query strings, header values, cookies, authorization values or bodies.

Anchors intentionally fail closed when an accepted Nuvio revision drifts. A lab that
cannot prove its instrumentation is invalid evidence and must not teach the Brain.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"native evidence instrumentation anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def instrument_tv(repo: Path) -> None:
    path = repo / "app/src/full/java/com/nuvio/tv/core/plugin/PluginRuntime.kt"
    text = path.read_text(encoding="utf-8")
    if "FIELD_NATIVE_HTTP_REQUEST client=tv" in text:
        return

    text = replace_once(
        text,
        "performNativeFetch(url, method, headersJson, body, inFlightCalls)",
        "performNativeFetch(url, method, headersJson, body, scraperId, mediaType, inFlightCalls)",
        "tv fetch call",
    )
    text = replace_once(
        text,
        """    private fun performNativeFetch(\n        url: String,\n        method: String,\n        headersJson: String,\n        body: String,\n        inFlightCalls: MutableSet<Call>\n    ): String {\n        Log.d(TAG, \"Fetch: $method $url body=${body.take(200)}\")\n        return try {\n""",
        """    private fun performNativeFetch(\n        url: String,\n        method: String,\n        headersJson: String,\n        body: String,\n        scraperId: String,\n        mediaType: String,\n        inFlightCalls: MutableSet<Call>\n    ): String {\n        val evidenceStartedAt = System.currentTimeMillis()\n        val evidenceEndpoint = url.substringBefore('?').substringBefore('#').replace(Regex(\"\\\\s+\"), \"%20\")\n        val evidenceRequestType = mediaType.lowercase().replace(Regex(\"[^a-z0-9_-]\"), \"_\")\n        return try {\n""",
        "tv fetch signature",
    )
    text = replace_once(
        text,
        """            // Default User-Agent\n            if (!headers.containsKey(\"User-Agent\")) {\n                headers[\"User-Agent\"] = \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\"\n            }\n\n            val requestBuilder = Request.Builder()\n""",
        """            // Default User-Agent\n            if (!headers.containsKey(\"User-Agent\")) {\n                headers[\"User-Agent\"] = \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\"\n            }\n            val evidenceHeaderNames = headers.keys.map { it.lowercase() }.distinct().sorted().joinToString(\",\")\n            Log.i(\"NiakvioEvidence\", \"FIELD_NATIVE_HTTP_REQUEST client=tv provider=$scraperId request_type=$evidenceRequestType method=${method.uppercase()} endpoint=$evidenceEndpoint header_names=$evidenceHeaderNames body_bytes=${body.toByteArray(Charsets.UTF_8).size}\")\n\n            val requestBuilder = Request.Builder()\n""",
        "tv request evidence",
    )
    text = replace_once(
        text,
        """                    Log.d(TAG, \"Fetch result: ${httpResponse.code} ${httpResponse.message} url=$url bodyLen=${responseBody.length} bodyPreview=${responseBody.take(300)}\")\n                    gson.toJson(result)\n""",
        """                    val finalEndpoint = httpResponse.request.url.toString().substringBefore('?').substringBefore('#').replace(Regex(\"\\\\s+\"), \"%20\")\n                    val responseHeaderNames = httpResponse.headers.names().map { it.lowercase() }.sorted().joinToString(\",\")\n                    val evidenceContentType = bodyContentType?.toString().orEmpty().replace(Regex(\"\\\\s+\"), \"_\")\n                    Log.i(\"NiakvioEvidence\", \"FIELD_NATIVE_HTTP_RESPONSE client=tv provider=$scraperId request_type=$evidenceRequestType method=${method.uppercase()} endpoint=$evidenceEndpoint final_endpoint=$finalEndpoint status=${httpResponse.code} duration_ms=${System.currentTimeMillis() - evidenceStartedAt} content_type=$evidenceContentType response_header_names=$responseHeaderNames body_bytes=${decodedRead.bytes.size} truncated=${decodedRead.truncated}\")\n                    gson.toJson(result)\n""",
        "tv response evidence",
    )
    text = replace_once(
        text,
        """        } catch (e: Exception) {\n            Log.e(TAG, \"Fetch error: ${e.message}\")\n            gson.toJson(mapOf(\n""",
        """        } catch (e: Exception) {\n            val errorName = e::class.qualifiedName.orEmpty().replace(Regex(\"\\\\s+\"), \"_\")\n            Log.i(\"NiakvioEvidence\", \"FIELD_NATIVE_HTTP_ERROR client=tv provider=$scraperId request_type=$evidenceRequestType method=${method.uppercase()} endpoint=$evidenceEndpoint duration_ms=${System.currentTimeMillis() - evidenceStartedAt} error_class=$errorName\")\n            Log.e(TAG, \"Fetch error: ${e.message}\")\n            gson.toJson(mapOf(\n""",
        "tv error evidence",
    )
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=tv path={path}")


def instrument_mobile(repo: Path) -> None:
    runtime = repo / "composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt"
    bridge = repo / "composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/network/FetchBridge.kt"
    runtime_text = runtime.read_text(encoding="utf-8")
    bridge_text = bridge.read_text(encoding="utf-8")
    if "FIELD_NATIVE_HTTP_REQUEST client=mobile" in bridge_text:
        return

    runtime_text = replace_once(runtime_text, "addModule(FetchBridge())", "addModule(FetchBridge(scraperId, mediaType))", "mobile bridge ownership")
    bridge_text = replace_once(
        bridge_text,
        "internal class FetchBridge : HostModule {",
        "internal class FetchBridge(private val scraperId: String, private val mediaType: String) : HostModule {",
        "mobile bridge constructor",
    )
    bridge_text = replace_once(
        bridge_text,
        """            try {\n                performNativeFetch(url, method, headersJson, body, followRedirects)\n            } catch (t: Throwable) {\n                log.e(t) { \"Fetch bridge error for $method $url\" }\n""",
        """            try {\n                performNativeFetch(url, method, headersJson, body, followRedirects)\n            } catch (t: Throwable) {\n                val endpoint = url.substringBefore('?').substringBefore('#').replace(Regex(\"\\\\s+\"), \"%20\")\n                val errorName = t::class.qualifiedName.orEmpty().replace(Regex(\"\\\\s+\"), \"_\")\n                val requestType = mediaType.lowercase().replace(Regex(\"[^a-z0-9_-]\"), \"_\")\n                log.i { \"FIELD_NATIVE_HTTP_ERROR client=mobile provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint error_class=$errorName\" }\n                log.e(t) { \"Fetch bridge error for $method <redacted-url>\" }\n""",
        "mobile bridge error",
    )
    bridge_text = replace_once(
        bridge_text,
        """        val headers = parseHeaders(headersJson).toMutableMap()\n        if (!headers.containsKey(\"User-Agent\")) {\n            headers[\"User-Agent\"] = \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\"\n        }\n\n        val response = runBlocking {\n""",
        """        val headers = parseHeaders(headersJson).toMutableMap()\n        if (!headers.containsKey(\"User-Agent\")) {\n            headers[\"User-Agent\"] = \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\"\n        }\n        val evidenceStartedAt = kotlin.time.TimeSource.Monotonic.markNow()\n        val endpoint = url.substringBefore('?').substringBefore('#').replace(Regex(\"\\\\s+\"), \"%20\")\n        val headerNames = headers.keys.map { it.lowercase() }.distinct().sorted().joinToString(\",\")\n        val requestType = mediaType.lowercase().replace(Regex(\"[^a-z0-9_-]\"), \"_\")\n        log.i { \"FIELD_NATIVE_HTTP_REQUEST client=mobile provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint header_names=$headerNames body_chars=${body.length} follow_redirects=$followRedirects\" }\n\n        val response = runBlocking {\n""",
        "mobile request evidence",
    )
    bridge_text = replace_once(
        bridge_text,
        """        val responseHeaders = response.headers.mapKeys { (key, _) -> key.lowercase() }\n            .mapValues { (_, value) -> truncateString(value, MAX_FETCH_HEADER_VALUE_CHARS) }\n        val result = JsonObject(\n""",
        """        val responseHeaders = response.headers.mapKeys { (key, _) -> key.lowercase() }\n            .mapValues { (_, value) -> truncateString(value, MAX_FETCH_HEADER_VALUE_CHARS) }\n        val finalEndpoint = response.url.substringBefore('?').substringBefore('#').replace(Regex(\"\\\\s+\"), \"%20\")\n        val responseHeaderNames = responseHeaders.keys.sorted().joinToString(\",\")\n        val responseRequestType = mediaType.lowercase().replace(Regex(\"[^a-z0-9_-]\"), \"_\")\n        log.i { \"FIELD_NATIVE_HTTP_RESPONSE client=mobile provider=$scraperId request_type=$responseRequestType method=${method.uppercase()} endpoint=$endpoint final_endpoint=$finalEndpoint status=${response.status} duration_ms=${evidenceStartedAt.elapsedNow().inWholeMilliseconds} response_header_names=$responseHeaderNames body_chars=${response.body.length}\" }\n        val result = JsonObject(\n""",
        "mobile response evidence",
    )
    runtime.write_text(runtime_text, encoding="utf-8")
    bridge.write_text(bridge_text, encoding="utf-8")
    print(f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=mobile runtime={runtime} bridge={bridge}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("tv", "mobile"))
    parser.add_argument("repo")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    if args.client == "tv":
        instrument_tv(repo)
    else:
        instrument_mobile(repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
