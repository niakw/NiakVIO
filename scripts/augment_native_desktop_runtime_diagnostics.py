#!/usr/bin/env python3
"""Expose JavaScript errors that the official Nuvio Desktop runtime maps to [].

The Desktop acceptance path must keep using PluginRepository.executeScraper with the
exact scraper loaded by the official repository. Nuvio Desktop intentionally catches
getStreams() JavaScript exceptions inside PluginRuntime and returns an empty list,
which makes a real runtime incompatibility indistinguishable from a legitimate empty
provider response.

This postprocessor preserves the official result unchanged. Only when that result is
empty, it performs a second diagnostic execution through the same
PluginRepository.executeScraper path with the generated Lab-only trap appended to a
copy of the already-loaded scraper code. A trapped exception is emitted as structured
Lab evidence and as a sentinel FIELD_NATIVE_ROW so existing runtime gates can classify
it. Production provider files and upstream Nuvio sources are never modified.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SENTINEL = "__NIAKVIO_RUNTIME_ERROR__"
MARKER = "FIELD_NATIVE_RUNTIME_DIAGNOSTIC"

OFFICIAL_CALL = (
    "val rows = PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()"
)

DIAGNOSTIC_CALL = f'''val rows = PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()
                if (rows.isEmpty()) {{
                    val diagnosticRows = PluginRepository.executeScraper(
                        loadedScraper.copy(code = trapRuntimeErrors(loadedScraper.code)),
                        tmdbId,
                        requestMediaType,
                        season,
                        episode,
                    ).getOrElse {{ emptyList() }}
                    val runtimeDiagnostic = diagnosticRows.firstOrNull {{ row ->
                        row.title.contains("{SENTINEL}") ||
                            row.name.orEmpty().contains("{SENTINEL}") ||
                            row.type.orEmpty().contains("{SENTINEL}") ||
                            row.provider.orEmpty().contains("{SENTINEL}")
                    }}
                    if (runtimeDiagnostic != null) {{
                        emit("{MARKER} client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode error64=${{b64(runtimeDiagnostic.provider)}}")
                        emit("FIELD_NATIVE_ROW client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode index=-1 title64=${{b64(runtimeDiagnostic.title)}} name64=${{b64(runtimeDiagnostic.name)}} quality64=${{b64(runtimeDiagnostic.quality)}} language64=${{b64(runtimeDiagnostic.language)}} type64=${{b64(runtimeDiagnostic.type)}} diagnostic=true")
                    }} else {{
                        emit("{MARKER} client=desktop fixture=$fixtureSlug provider64=${{b64(provider.id)}} request_type=$requestMediaType route_mode=$routeMode error64=${{b64(\"empty_without_trapped_exception\")}}")
                    }}
                }}'''


def augment(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"FIELD_NATIVE_DESKTOP_RUNTIME_DIAGNOSTICS already=true source={path}")
        return False
    if "private fun trapRuntimeErrors(code: String): String" not in text:
        raise SystemExit("desktop runtime diagnostics requires the generated runtime-error trap helper")
    count = text.count(OFFICIAL_CALL)
    if count != 1:
        raise SystemExit(f"desktop runtime diagnostics official-call anchor count={count}")
    path.write_text(text.replace(OFFICIAL_CALL, DIAGNOSTIC_CALL, 1), encoding="utf-8")
    print(f"FIELD_NATIVE_DESKTOP_RUNTIME_DIAGNOSTICS added=true source={path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    augment(Path(args.source).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
