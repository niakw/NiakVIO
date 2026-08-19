#!/usr/bin/env python3
"""Inject passive sanitized HTTP evidence into the accepted NuvioDesktop runtime."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"desktop evidence instrumentation anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    runtime = repo / "composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/PluginRuntime.kt"
    bridge = repo / "composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/network/FetchBridge.kt"
    runtime_text = runtime.read_text(encoding="utf-8")
    bridge_text = bridge.read_text(encoding="utf-8")
    if "FIELD_NATIVE_HTTP_REQUEST client=desktop" in bridge_text:
        print(f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=desktop bridge={bridge}")
        return 0

    runtime_text = replace_once(
        runtime_text,
        "addModule(FetchBridge())",
        "addModule(FetchBridge(scraperId, mediaType))",
        "bridge ownership",
    )
    bridge_text = replace_once(
        bridge_text,
        "internal class FetchBridge : HostModule {",
        "internal class FetchBridge(private val scraperId: String, private val mediaType: String) : HostModule {",
        "bridge constructor",
    )
    bridge_text = replace_once(
        bridge_text,
        '''            } catch (t: Throwable) {\n                log.e(t) { "Fetch bridge error for $method $url" }\n''',
        '''            } catch (t: Throwable) {\n                val endpoint = url.substringBefore('?').substringBefore('#').replace(Regex("\\\\s+"), "%20")\n                val errorName = t::class.qualifiedName.orEmpty().replace(Regex("\\\\s+"), "_")\n                val requestType = mediaType.lowercase().replace(Regex("[^a-z0-9_-]"), "_")\n                log.i { "FIELD_NATIVE_HTTP_ERROR client=desktop provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint error_class=$errorName" }\n                log.e(t) { "Fetch bridge error for $method <redacted-url>" }\n''',
        "bridge error",
    )
    bridge_text = replace_once(
        bridge_text,
        '''        val headers = parseHeaders(headersJson).toMutableMap()\n        if (!headers.containsKey("User-Agent")) {\n            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"\n        }\n\n        val response = httpRequestRaw(\n''',
        '''        val headers = parseHeaders(headersJson).toMutableMap()\n        if (!headers.containsKey("User-Agent")) {\n            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"\n        }\n        val evidenceStartedAt = kotlin.time.TimeSource.Monotonic.markNow()\n        val endpoint = url.substringBefore('?').substringBefore('#').replace(Regex("\\\\s+"), "%20")\n        val headerNames = headers.keys.map { it.lowercase() }.distinct().sorted().joinToString(",")\n        val requestType = mediaType.lowercase().replace(Regex("[^a-z0-9_-]"), "_")\n        log.i { "FIELD_NATIVE_HTTP_REQUEST client=desktop provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint header_names=$headerNames body_chars=${body.length} follow_redirects=$followRedirects" }\n\n        val response = httpRequestRaw(\n''',
        "request evidence",
    )
    bridge_text = replace_once(
        bridge_text,
        '''        val responseHeaders = response.headers.mapKeys { (key, _) -> key.lowercase() }\n            .mapValues { (_, value) -> truncateString(value, MAX_FETCH_HEADER_VALUE_CHARS) }\n        val result = JsonObject(\n''',
        '''        val responseHeaders = response.headers.mapKeys { (key, _) -> key.lowercase() }\n            .mapValues { (_, value) -> truncateString(value, MAX_FETCH_HEADER_VALUE_CHARS) }\n        val finalEndpoint = response.url.substringBefore('?').substringBefore('#').replace(Regex("\\\\s+"), "%20")\n        val responseHeaderNames = responseHeaders.keys.sorted().joinToString(",")\n        log.i { "FIELD_NATIVE_HTTP_RESPONSE client=desktop provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint final_endpoint=$finalEndpoint status=${response.status} duration_ms=${evidenceStartedAt.elapsedNow().inWholeMilliseconds} response_header_names=$responseHeaderNames body_chars=${response.body.length}" }\n        val result = JsonObject(\n''',
        "response evidence",
    )

    runtime.write_text(runtime_text, encoding="utf-8")
    bridge.write_text(bridge_text, encoding="utf-8")
    print(f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=desktop runtime={runtime} bridge={bridge}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
