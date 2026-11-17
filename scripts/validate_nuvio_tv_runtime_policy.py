#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "automation" / "nuvio-tv-runtime-contract.json"
MAIN_PATH = ROOT / "manifest.json"
VF_PATH = ROOT / "vf" / "manifest.json"
PLATFORM_POLICY_PATH = ROOT / "automation" / "platform-runtime-policy.json"
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


def effective_media_safety_source(path: Path) -> str:
    """Compose the configured terminal sanitizer before validating inherited layers.

    V12 is intentionally a thin delta over V11/V10/V8. Requiring inherited markers to
    be copied into each newer source file would duplicate implementation text and
    make the validator disagree with the bytes actually emitted by Core.
    """
    spec = importlib.util.spec_from_file_location("nuvio_tv_media_safety_authority", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"{path}: cannot load media-safety authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    apply = getattr(module, "apply", None)
    if not callable(apply):
        raise ValueError(f"{path}: media-safety authority has no apply()")
    source = "module.exports={getStreams:async function(){return []}};\n"
    rendered = apply(
        source,
        options={
            "probe_direct_media": True,
            "probe_all_urls": True,
            "max_probes": 40,
            "probe_timeout_ms": 2000,
            "min_vod_duration_seconds": 60,
        },
    )
    if not isinstance(rendered, str) or not rendered.strip():
        raise ValueError(f"{path}: media-safety authority rendered no source")
    return rendered


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


def main() -> int:
    errors: list[str] = []
    contract = load(CONTRACT_PATH)

    if contract.get("schema_version") != 4:
        errors.append(f"NuvioTV runtime contract schema mismatch: {contract.get('schema_version')!r}")

    expected = {
        "client": "NuvioTV",
        "platform": "android-tv",
        "integration": "plugin-provider-repository",
        "runtime_contract": "getStreams(tmdbId, mediaType, season, episode) plus global SCRAPER_ID, SCRAPER_SETTINGS and runtime TMDB_API_KEY",
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
        "media_safety": contract.get("media_safety_authority"),
    }
    paths: dict[str, Path] = {}
    for label, relative in required.items():
        path = ROOT / str(relative or "")
        paths[label] = path
        if not path.is_file():
            errors.append(f"missing NuvioTV {label}: {relative}")

    historical = contract.get("historical_direct_media_promotion") or {}
    if historical.get("authority") is not False:
        errors.append("historical NuvioTV direct-media promotion must be non-authoritative")
    retired_patch = str(historical.get("retired_patch") or "")
    if not retired_patch:
        errors.append("missing retired NuvioTV patch provenance")
    elif (ROOT / retired_patch).exists():
        errors.append(f"retired NuvioTV direct-media patch unexpectedly restored: {retired_patch}")
    promoter = str(historical.get("promoter") or "")
    for workflow in (ROOT / ".github" / "workflows").glob("*.yml"):
        workflow_text = workflow.read_text(encoding="utf-8", errors="replace")
        if promoter and promoter in workflow_text:
            errors.append(f"historical NuvioTV promoter became workflow-authoritative: {workflow.name}")
        if retired_patch and retired_patch in workflow_text:
            errors.append(f"retired NuvioTV patch became workflow-authoritative: {workflow.name}")

    if paths.get("probe") and paths["probe"].is_file():
        text = paths["probe"].read_text(encoding="utf-8", errors="replace")
        markers = (
            "SCRAPER_SETTINGS",
            "Android TV",
            "nuvio_tv_positional",
            "invocation_authoritative",
            "starts_extm3u",
            "binary_signature",
            "<MPD",
            "result.kind = 'dash'",
        )
        for marker in markers:
            if marker not in text:
                errors.append(f"NuvioTV probe missing marker: {marker}")

    if paths.get("media_safety") and paths["media_safety"].is_file():
        try:
            text = effective_media_safety_source(paths["media_safety"])
        except Exception as error:
            errors.append(f"NuvioTV shared media-safety authority could not compose: {error}")
            text = ""
        for marker in (
            "NUVIO_STREAM_OUTPUT_MULTI_AUDIO_FRONTIER_V12",
            "NUVIO_STREAM_OUTPUT_HLS_MASTER_PREFERENCE_V11",
            "NUVIO_STREAM_OUTPUT_NETWORK_EVIDENCE_V10",
            "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8",
            "clearPrivateProofs",
        ):
            if marker not in text:
                errors.append(f"NuvioTV effective shared media-safety authority missing marker: {marker}")

    main_doc = load(MAIN_PATH)
    vf_doc = load(VF_PATH)
    platform_policy = load(PLATFORM_POLICY_PATH)
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

    # Platform failures stay internal; manifests deliberately publish
    # disabledPlatforms=[]. Providers with conclusive failures on every non-TV
    # runtime still need the strict NuvioTV media sanitizer because NuvioTV does
    # not enforce those manifest fields.
    managed = {
        str(provider_id).casefold(): {
            str(token).strip().casefold()
            for token in tokens
            if str(token).strip()
        }
        for provider_id, tokens in (platform_policy.get("managed_platform_tokens_by_provider") or {}).items()
    }
    strict_guarded: list[str] = []
    for provider_id, tokens in sorted(managed.items()):
        if not {"android", "ios", "desktop"}.issubset(tokens):
            continue
        row = main_rows.get(provider_id)
        if row is None or row.get("enabled") is not True:
            continue
        relative = normalized_provider_path(row.get("filename"))
        provider_path = ROOT / relative
        if not provider_path.is_file():
            errors.append(f"{provider_id}: internally guarded provider bundle missing: {relative}")
            continue
        text = provider_path.read_text(encoding="utf-8", errors="replace")
        if not strict_all_url_media_guard(text):
            errors.append(
                f"{provider_id}: internally guarded on android+ios+desktop but reachable by NuvioTV; "
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
