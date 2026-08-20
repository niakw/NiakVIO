#!/usr/bin/env python3
"""Inject passive sanitized HTTP evidence into the accepted NuvioDesktop runtime.

Desktop test stdout is not a reliable evidence transport because Gradle may capture
it. The injected bridge therefore appends only NiakVIO's sanitized FIELD_NATIVE_HTTP
records to a dedicated workspace file consumed by the lab after the test.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"desktop evidence instrumentation anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def evidence_write(expression: str) -> str:
    return (
        'runCatching { java.io.File(System.getenv("GITHUB_WORKSPACE") ?: ".", '
        f'"desktop-native-http-evidence.log").appendText({expression} + "\\n") }}'
    )


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

    # Nuvio intentionally turns a thrown getStreams() into [] inside QuickJS. Keep
    # that production behavior unchanged, but surface the swallowed reason to the
    # lab in sanitized form so an empty provider result is diagnosable evidence.
    # This diagnostic is deliberately optional for minimal/synthetic runtimes used
    # by instrumentation contract tests. HTTP evidence remains mandatory. On the
    # accepted real NuvioDesktop runtime both anchors are present and the callback
    # is injected; a partial anchor match is treated as drift and fails closed.
    plugin_error_binding_anchor = '''                val callCode = """\n                    (async function() {\n'''
    plugin_error_callback_anchor = '''                            console.error("getStreams error:", e && e.message ? e.message : e, e && e.stack ? e.stack : "");\n                            __capture_result(JSON.stringify([]));\n'''
    binding_count = runtime_text.count(plugin_error_binding_anchor)
    callback_count = runtime_text.count(plugin_error_callback_anchor)
    plugin_error_capture = False
    if binding_count == 1 and callback_count == 1:
        plugin_error_line = evidence_write(
            '"FIELD_NATIVE_PLUGIN_ERROR client=desktop provider=$scraperId request_type=${mediaType.lowercase()} error=$safePluginError"'
        )
        runtime_text = runtime_text.replace(
            plugin_error_binding_anchor,
            f'''                function("__niakvio_capture_plugin_error") {{ args: Array<Any?> ->\n                    val rawPluginError = args.getOrNull(0)?.toString().orEmpty()\n                    val safePluginError = rawPluginError\n                        .replace(Regex("https?://\\\\S+", RegexOption.IGNORE_CASE), "<url>")\n                        .replace(Regex("(?i)(authorization|cookie|token|secret)\\\\s*[:=]\\\\s*\\\\S+"), "$1=<redacted>")\n                        .replace(Regex("\\\\s+"), "_")\n                        .take(360)\n                    {plugin_error_line}\n                    null\n                }}\n\n                val callCode = """\n                    (async function() {{\n''',
            1,
        )
        runtime_text = runtime_text.replace(
            plugin_error_callback_anchor,
            '''                            console.error("getStreams error:", e && e.message ? e.message : e, e && e.stack ? e.stack : "");\n                            __niakvio_capture_plugin_error(String(e && e.message ? e.message : e));\n                            __capture_result(JSON.stringify([]));\n''',
            1,
        )
        plugin_error_capture = True
    elif binding_count != 0 or callback_count != 0:
        raise SystemExit(
            "desktop evidence instrumentation partial plugin-error anchor drift "
            f"binding={binding_count} callback={callback_count}"
        )

    bridge_text = replace_once(
        bridge_text,
        "internal class FetchBridge : HostModule {",
        "internal class FetchBridge(private val scraperId: String, private val mediaType: String) : HostModule {",
        "bridge constructor",
    )
    error_line = evidence_write('"FIELD_NATIVE_HTTP_ERROR client=desktop provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint error_class=$errorName"')
    bridge_text = replace_once(
        bridge_text,
        '''            } catch (t: Throwable) {\n                log.e(t) { "Fetch bridge error for $method $url" }\n''',
        f'''            }} catch (t: Throwable) {{\n                val endpoint = url.substringBefore('?').substringBefore('#').replace(Regex("\\\\s+"), "%20")\n                val errorName = t::class.qualifiedName.orEmpty().replace(Regex("\\\\s+"), "_")\n                val requestType = mediaType.lowercase().replace(Regex("[^a-z0-9_-]"), "_")\n                {error_line}\n                log.e(t) {{ "Fetch bridge error for $method <redacted-url>" }}\n''',
        "bridge error",
    )
    request_line = evidence_write('"FIELD_NATIVE_HTTP_REQUEST client=desktop provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint header_names=$headerNames body_chars=${body.length} follow_redirects=$followRedirects"')
    bridge_text = replace_once(
        bridge_text,
        '''        val headers = parseHeaders(headersJson).toMutableMap()\n        if (!headers.containsKey("User-Agent")) {\n            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"\n        }\n\n        val response = httpRequestRaw(\n''',
        f'''        val headers = parseHeaders(headersJson).toMutableMap()\n        if (!headers.containsKey("User-Agent")) {{\n            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"\n        }}\n        val evidenceStartedAt = kotlin.time.TimeSource.Monotonic.markNow()\n        val endpoint = url.substringBefore('?').substringBefore('#').replace(Regex("\\\\s+"), "%20")\n        val headerNames = headers.keys.map {{ it.lowercase() }}.distinct().sorted().joinToString(",")\n        val requestType = mediaType.lowercase().replace(Regex("[^a-z0-9_-]"), "_")\n        {request_line}\n\n        val response = httpRequestRaw(\n''',
        "request evidence",
    )
    response_line = evidence_write('"FIELD_NATIVE_HTTP_RESPONSE client=desktop provider=$scraperId request_type=$requestType method=${method.uppercase()} endpoint=$endpoint final_endpoint=$finalEndpoint status=${response.status} duration_ms=${evidenceStartedAt.elapsedNow().inWholeMilliseconds} response_header_names=$responseHeaderNames body_chars=${response.body.length}"')
    bridge_text = replace_once(
        bridge_text,
        '''        val responseHeaders = response.headers.mapKeys { (key, _) -> key.lowercase() }\n            .mapValues { (_, value) -> truncateString(value, MAX_FETCH_HEADER_VALUE_CHARS) }\n        val result = JsonObject(\n''',
        f'''        val responseHeaders = response.headers.mapKeys {{ (key, _) -> key.lowercase() }}\n            .mapValues {{ (_, value) -> truncateString(value, MAX_FETCH_HEADER_VALUE_CHARS) }}\n        val finalEndpoint = response.url.substringBefore('?').substringBefore('#').replace(Regex("\\\\s+"), "%20")\n        val responseHeaderNames = responseHeaders.keys.sorted().joinToString(",")\n        {response_line}\n        val result = JsonObject(\n''',
        "response evidence",
    )

    runtime.write_text(runtime_text, encoding="utf-8")
    bridge.write_text(bridge_text, encoding="utf-8")
    print(
        f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=desktop runtime={runtime} bridge={bridge} "
        f"plugin_error_capture={str(plugin_error_capture).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
