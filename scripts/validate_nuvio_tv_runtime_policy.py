#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "automation" / "nuvio-tv-runtime-contract.json"
MAIN_PATH = ROOT / "manifest.json"
VF_PATH = ROOT / "vf" / "manifest.json"
ALL_NON_TV_RUNTIME_BLOCKS = {"android", "ios", "desktop"}
COFLIX_REQUIRED_RUNTIME_MARKERS = {
    "NUVIO_TARGET_MEDIA_HOST_FILTER_V4",
    "NUVIO_STREAM_OUTPUT_SANITIZER",
    "/wp-admin/",
    "/wp-json/",
    "/wp-content/plugins/ajax-search-lite/",
}
JS_TRUE_FIELD = re.compile(
    r"(?<![A-Za-z0-9_$])(?:[\"']?probeAllUrls[\"']?)\s*:\s*true\b"
)
JS_POSITIVE_MAX_PROBES = re.compile(
    r"(?<![A-Za-z0-9_$])(?:[\"']?maxProbes[\"']?)\s*:\s*(\d+)\b"
)
TV_TARGET_MEDIA_CURRENT = re.compile(r"NUVIO_TV_TARGET_MEDIA_V(?:[4-9]|[1-9]\d+)\b")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in document.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def normalized_provider_path(filename: object) -> str:
    value = str(filename or "")
    while value.startswith("../"):
        value = value[3:]
    return value


def report_has_playable_evidence(report: dict[str, Any]) -> bool:
    for provider in (report.get("providers") or {}).values():
        if not isinstance(provider, dict):
            continue
        for group_name in ("candidate", "baseline"):
            for result in provider.get(group_name) or []:
                if not isinstance(result, dict):
                    continue
                parsed = result.get("result") or {}
                if int(parsed.get("playable_stream_count") or 0) > 0:
                    return True
    return False


def strict_all_url_media_guard(text: str) -> bool:
    """Recognize the executable all-URL sanitizer contract, minified or pretty.

    Published bundles are JavaScript, so object keys may legally be quoted or
    unquoted. The old validator only accepted JSON-style quoted keys and produced
    false negatives after minification even though probeAllUrls=true/maxProbes>0
    were present in the executable config.
    """
    if "NUVIO_STREAM_OUTPUT_SANITIZER" not in text:
        return False
    if JS_TRUE_FIELD.search(text) is None:
        return False
    match = JS_POSITIVE_MAX_PROBES.search(text)
    return bool(match and int(match.group(1)) > 0)


def coflix_strict_runtime_guard(text: str) -> list[str]:
    missing = sorted(marker for marker in COFLIX_REQUIRED_RUNTIME_MARKERS if marker not in text)
    if TV_TARGET_MEDIA_CURRENT.search(text) is None:
        missing.append("NUVIO_TV_TARGET_MEDIA_V4+")
    if JS_TRUE_FIELD.search(text) is None:
        missing.append("probeAllUrls:true")
    return sorted(set(missing))


def platform_values(row: dict[str, Any], key: str) -> set[str]:
    return {
        str(value).strip().casefold()
        for value in row.get(key) or []
        if str(value).strip()
    }


def main() -> int:
    errors: list[str] = []
    contract = load(CONTRACT_PATH)

    expected = {
        "client": "NuvioTV",
        "platform": "android-tv",
        "integration": "plugin-provider-repository",
        "runtime_contract": "getStreams(tmdbId, mediaType, season, episode) plus global SCRAPER_ID, SCRAPER_SETTINGS and TV-only TMDB_API_KEY",
        "player_model": "direct-media-first",
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            errors.append(f"contract {key} mismatch: {contract.get(key)!r}")

    expected_gate = {"hls-extm3u", "dash-mpd", "real-video-container-signature"}
    if set(contract.get("media_gate") or []) != expected_gate:
        errors.append("NuvioTV media gate mismatch")

    filtering = contract.get("manifest_platform_filtering") or {}
    if set(filtering.get("fields_parsed") or []) != {"supportedPlatforms", "disabledPlatforms"}:
        errors.append("NuvioTV manifest platform-field contract mismatch")
    if filtering.get("enforced_by_plugin_manager") is not False:
        errors.append("NuvioTV platform filters must not be assumed enforced by PluginManager")

    required = {
        "probe": contract.get("probe"),
        "promoter": contract.get("promoter"),
        "patch": contract.get("direct_media_patch"),
        "report": contract.get("promotion_report"),
    }
    paths: dict[str, Path] = {}
    for label, relative in required.items():
        path = ROOT / str(relative or "")
        paths[label] = path
        if not path.is_file():
            errors.append(f"missing NuvioTV {label}: {relative}")

    if paths.get("probe") and paths["probe"].is_file():
        text = paths["probe"].read_text(encoding="utf-8", errors="replace")
        markers = (
            "SCRAPER_SETTINGS",
            "Android TV",
            "provider.getStreams(String(fixture.tmdbId",
            "starts_extm3u",
            "binary_signature",
            "<MPD",
            "result.kind = 'dash'",
        )
        for marker in markers:
            if marker not in text:
                errors.append(f"NuvioTV probe missing marker: {marker}")

    if paths.get("patch") and paths["patch"].is_file():
        text = paths["patch"].read_text(encoding="utf-8", errors="replace")
        markers = (
            "NUVIO_TV_DIRECT_MEDIA_V2",
            "SCRAPER_SETTINGS",
            "async function(tmdbId,mediaType,season,episode)",
            "#EXTM3U",
            "<MPD",
        )
        for marker in markers:
            if marker not in text:
                errors.append(f"NuvioTV direct-media patch missing marker: {marker}")

    if paths.get("promoter") and paths["promoter"].is_file():
        text = paths["promoter"].read_text(encoding="utf-8", errors="replace")
        markers = (
            "nuvio_tv_probe_v2.cjs",
            "nuvio_tv_direct_media_v2.py",
            "NuvioTV four positional args plus global SCRAPER_SETTINGS",
            "strictly_better",
        )
        for marker in markers:
            if marker not in text:
                errors.append(f"NuvioTV promoter missing marker: {marker}")

    if paths.get("report") and paths["report"].is_file():
        report = load(paths["report"])
        if report.get("contract") != "NuvioTV four positional args plus global SCRAPER_SETTINGS":
            errors.append("NuvioTV historical promotion report contract mismatch")
        if report.get("media_gate") != "#EXTM3U, DASH MPD, or real video container signature":
            errors.append("NuvioTV historical promotion report media gate mismatch")
        if not report_has_playable_evidence(report):
            errors.append("NuvioTV promotion report has no strict playable-media evidence")

    main_doc = load(MAIN_PATH)
    vf_doc = load(VF_PATH)
    main_rows = rows(main_doc)
    vf_rows = rows(vf_doc)

    published_tv = {
        provider_id: row
        for provider_id, row in main_rows.items()
        if "--nuvio-tv-global--" in str(row.get("filename") or "")
    }
    # A TV-specific promotion is an optimization, not an availability quota.
    # After a conclusive safety quarantine there may legitimately be zero
    # currently published --nuvio-tv-global-- bundles. Requiring at least one
    # would pressure the publisher to resurrect stale bytes without current
    # proof. When promoted bundles do exist, all strict checks below still apply.
    for provider_id, row in sorted(published_tv.items()):
        relative = normalized_provider_path(row.get("filename"))
        if not (ROOT / relative).is_file():
            errors.append(f"{provider_id}: published NuvioTV bundle missing: {relative}")
        if row.get("enabled") is not True:
            errors.append(f"{provider_id}: NuvioTV-promoted bundle is not enabled")
        vf_row = vf_rows.get(provider_id)
        if vf_row is not None and normalized_provider_path(vf_row.get("filename")) != relative:
            errors.append(f"{provider_id}: main/VF NuvioTV bundle mismatch")

    strict_guarded: list[str] = []
    for provider_id, row in sorted(main_rows.items()):
        if row.get("enabled") is not True:
            continue
        disabled = platform_values(row, "disabledPlatforms")
        if not ALL_NON_TV_RUNTIME_BLOCKS.issubset(disabled):
            continue
        relative = normalized_provider_path(row.get("filename"))
        provider_path = ROOT / relative
        if not provider_path.is_file():
            errors.append(f"{provider_id}: client-blocked provider bundle missing: {relative}")
            continue
        text = provider_path.read_text(encoding="utf-8", errors="replace")
        if not strict_all_url_media_guard(text):
            errors.append(
                f"{provider_id}: blocked on android+ios+desktop but still reachable by NuvioTV; "
                "bundle must probe every returned URL and reject non-media payloads"
            )
            continue
        if provider_id == "coflix":
            missing = coflix_strict_runtime_guard(text)
            if missing:
                errors.append(
                    "coflix: NuvioTV safety chain incomplete; missing " + ", ".join(missing)
                )
                continue
        strict_guarded.append(provider_id)

    package = load(ROOT / "package.json")
    test_command = str((package.get("scripts") or {}).get("test") or "")
    if "validate_nuvio_tv_runtime_policy.py" not in test_command:
        errors.append("npm test does not include the NuvioTV runtime policy validator")

    if errors:
        raise SystemExit("NuvioTV runtime policy validation failed:\n- " + "\n- ".join(errors))

    print(
        "NuvioTV runtime policy validated: "
        f"published_tv={','.join(sorted(published_tv)) or '-'}; "
        f"strict_tv_guard={','.join(strict_guarded) or '-'}; "
        "contract=positional+SCRAPER_SETTINGS; media=HLS/DASH/container"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
