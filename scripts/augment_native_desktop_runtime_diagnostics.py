#!/usr/bin/env python3
"""Expose failures hidden behind an empty official Nuvio Desktop result.

The Desktop acceptance path keeps using PluginRepository.executeScraper with the exact
scraper loaded by the official repository. Nuvio Desktop intentionally catches
getStreams() JavaScript exceptions and returns an empty list. Providers also commonly
catch their own network/parser errors, log them through console.* and return []. Both
behaviours are correct for the application but hide the reason for a Lab extraction
failure.

This postprocessor preserves the official result unchanged. Only when that result is
empty, it performs a second diagnostic execution through the same repository path on a
copy of the already-loaded scraper code. The diagnostic copy traps uncaught exceptions,
captures provider console output where the runtime permits it, and wraps the official
fetch polyfill to record requested URL/method plus native response status/statusText.
Production provider files and upstream Nuvio runtime sources are never modified.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ERROR_SENTINEL = "__NIAKVIO_RUNTIME_ERROR__"
DIAGNOSTIC_SENTINEL = "__NIAKVIO_RUNTIME_DIAGNOSTIC__"
MARKER = "FIELD_NATIVE_RUNTIME_DIAGNOSTIC"

OFFICIAL_CALL = (
    "val rows = PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()"
)

CONSOLE_HELPER = r'''
    private fun captureRuntimeConsole(code: String): String = code + """
;/* NIAKVIO_NATIVE_RUNTIME_CONSOLE_CAPTURE */
(function () {
    var marker = "__NIAKVIO_RUNTIME_DIAGNOSTIC__";
    var messages = [];
    var originalConsole = (typeof globalThis !== "undefined" && globalThis.console) ? globalThis.console : null;
    var originalFetch = (typeof globalThis !== "undefined" && typeof globalThis.fetch === "function") ? globalThis.fetch : null;
    var stringify = function (value) {
        try {
            if (value && value.message) return String(value.message);
            if (typeof value === "string") return value;
            if (value === undefined) return "undefined";
            if (value === null) return "null";
            if (typeof JSON !== "undefined" && JSON.stringify) {
                var encoded = JSON.stringify(value);
                if (encoded !== undefined) return encoded;
            }
            return String(value);
        } catch (_) {
            return "[unprintable]";
        }
    };
    var capture = function (level, args) {
        try {
            var parts = [];
            for (var i = 0; i < args.length; i++) parts.push(stringify(args[i]));
            var line = level + ":" + parts.join(" ");
            if (line.length > 1200) line = line.slice(0, 1200) + "...[truncated]";
            messages.push(line);
            if (messages.length > 32) messages.shift();
        } catch (_) {}
    };
    var inputUrl = function (input) {
        try {
            if (typeof input === "string") return input;
            if (input && typeof input.url === "string") return input.url;
            if (input && typeof input.href === "string") return input.href;
            return String(input || "");
        } catch (_) { return "[unprintable-url]"; }
    };
    var diagnosticConsole = {};
    ["log", "error", "warn", "info", "debug"].forEach(function (level) {
        diagnosticConsole[level] = function () {
            capture(level, arguments);
            try {
                if (originalConsole && typeof originalConsole[level] === "function") {
                    originalConsole[level].apply(originalConsole, arguments);
                }
            } catch (_) {}
        };
    });
    try {
        if (typeof globalThis !== "undefined") globalThis.console = diagnosticConsole;
    } catch (_) {}

    // Capture transport facts independently of console.*. NuvioDesktop's official
    // FetchBridge converts native exceptions to an ordinary response with status=0,
    // so this records the signal providers may otherwise catch and turn into [].
    try {
        if (originalFetch && typeof globalThis !== "undefined") {
            globalThis.fetch = async function (input, init) {
                var method = "GET";
                try { method = String((init && init.method) || "GET").toUpperCase(); } catch (_) {}
                var url = inputUrl(input);
                try {
                    var response = await originalFetch.apply(this, arguments);
                    capture("fetch", [method, url, "status=" + stringify(response && response.status), "ok=" + stringify(response && response.ok), "statusText=" + stringify(response && response.statusText)]);
                    return response;
                } catch (error) {
                    capture("fetch-error", [method, url, stringify(error)]);
                    throw error;
                }
            };
        }
    } catch (_) {}

    var exportsObject = null;
    try {
        if (typeof module !== "undefined" && module && module.exports) exportsObject = module.exports;
    } catch (_) {}
    var original = null;
    if (exportsObject && typeof exportsObject.getStreams === "function") original = exportsObject.getStreams;
    else if (typeof globalThis !== "undefined" && typeof globalThis.getStreams === "function") original = globalThis.getStreams;

    var makeDiagnostic = function () {
        var detail = messages.length ? messages.join(" | ") : "no_console_or_fetch_output";
        return [{
            title: marker,
            name: marker,
            url: "data:application/x-niakvio-runtime-diagnostic,1",
            quality: "",
            language: "",
            provider: marker + ":" + detail,
            type: marker
        }];
    };

    var wrapped;
    if (typeof original !== "function") {
        wrapped = async function () { return makeDiagnostic(); };
    } else {
        wrapped = async function () {
            try {
                var result = await original.apply(this, arguments);
                var empty = Array.isArray(result) ? result.length === 0 :
                    !!(result && typeof result === "object" &&
                        ((Array.isArray(result.streams) && result.streams.length === 0) ||
                         (Array.isArray(result.results) && result.results.length === 0) ||
                         (Array.isArray(result.data) && result.data.length === 0)));
                if (empty) return makeDiagnostic();
                return result;
            } finally {
                try {
                    if (typeof globalThis !== "undefined" && originalConsole) globalThis.console = originalConsole;
                    if (typeof globalThis !== "undefined" && originalFetch) globalThis.fetch = originalFetch;
                } catch (_) {}
            }
        };
    }
    if (exportsObject) exportsObject.getStreams = wrapped;
    else if (typeof globalThis !== "undefined") globalThis.getStreams = wrapped;
})();
""".trimIndent()
'''

DIAGNOSTIC_CALL = f'''val rows = PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()
                if (rows.isEmpty()) {{
                    // Cross-check the exact same loaded code through the historical
                    // direct runtime path. This isolates repository/ID handling from
                    // provider/Core behavior without changing production code.
                    val directManifestIdRows = PluginRuntime.executePlugin(
                        code = loadedScraper.code,
                        tmdbId = tmdbId,
                        mediaType = requestMediaType,
                        season = season,
                        episode = episode,
                        scraperId = provider.id,
                    )
                    val directLoadedIdRows = PluginRuntime.executePlugin(
                        code = loadedScraper.code,
                        tmdbId = tmdbId,
                        mediaType = requestMediaType,
                        season = season,
                        episode = episode,
                        scraperId = loadedScraper.id,
                    )
                    emit("FIELD_NATIVE_DESKTOP_RUNTIME_BISECT client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode repository_count=${{rows.size}} direct_manifest_id_count=${{directManifestIdRows.size}} direct_loaded_id_count=${{directLoadedIdRows.size}} loaded_scraper_id64=${{b64(loadedScraper.id)}}")

                    val diagnosticRows = PluginRepository.executeScraper(
                        loadedScraper.copy(code = captureRuntimeConsole(trapRuntimeErrors(loadedScraper.code))),
                        tmdbId,
                        requestMediaType,
                        season,
                        episode,
                    ).getOrElse {{ emptyList() }}
                    val runtimeError = diagnosticRows.firstOrNull {{ row ->
                        row.title.contains("{ERROR_SENTINEL}") ||
                            row.name.orEmpty().contains("{ERROR_SENTINEL}") ||
                            row.type.orEmpty().contains("{ERROR_SENTINEL}") ||
                            row.provider.orEmpty().contains("{ERROR_SENTINEL}")
                    }}
                    val runtimeDiagnostic = diagnosticRows.firstOrNull {{ row ->
                        row.title.contains("{DIAGNOSTIC_SENTINEL}") ||
                            row.name.orEmpty().contains("{DIAGNOSTIC_SENTINEL}") ||
                            row.type.orEmpty().contains("{DIAGNOSTIC_SENTINEL}") ||
                            row.provider.orEmpty().contains("{DIAGNOSTIC_SENTINEL}")
                    }}
                    if (runtimeError != null) {{
                        emit("{MARKER} client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode class=uncaught_exception detail64=${{b64(runtimeError.provider)}}")
                        emit("FIELD_NATIVE_ROW client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=-1 title64=${{b64(runtimeError.title)}} name64=${{b64(runtimeError.name)}} quality64=${{b64(runtimeError.quality)}} language64=${{b64(runtimeError.language)}} type64=${{b64(runtimeError.type)}} diagnostic=true")
                    }} else if (runtimeDiagnostic != null) {{
                        emit("{MARKER} client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode class=caught_or_empty detail64=${{b64(runtimeDiagnostic.provider)}}")
                    }} else {{
                        emit("{MARKER} client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode class=empty_without_diagnostic detail64=${{b64(\"empty_without_diagnostic\")}}")
                    }}
                }}'''


def augment(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "NIAKVIO_NATIVE_RUNTIME_CONSOLE_CAPTURE" in text:
        print(f"FIELD_NATIVE_DESKTOP_RUNTIME_DIAGNOSTICS already=true source={path}")
        return False
    if "private fun trapRuntimeErrors(code: String): String" not in text:
        raise SystemExit("desktop runtime diagnostics requires the generated runtime-error trap helper")

    helper_anchor = "    private fun b64(value: Any?): String ="
    helper_count = text.count(helper_anchor)
    if helper_count != 1:
        raise SystemExit(f"desktop runtime diagnostics helper anchor count={helper_count}")
    text = text.replace(helper_anchor, CONSOLE_HELPER + "\n" + helper_anchor, 1)

    count = text.count(OFFICIAL_CALL)
    if count != 1:
        raise SystemExit(f"desktop runtime diagnostics official-call anchor count={count}")
    path.write_text(text.replace(OFFICIAL_CALL, DIAGNOSTIC_CALL, 1), encoding="utf-8")
    print(f"FIELD_NATIVE_DESKTOP_RUNTIME_DIAGNOSTICS added=true console_capture=true fetch_capture=true source={path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    augment(Path(args.source).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
