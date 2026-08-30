#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "tests" / "fixtures" / "provider-production-5.21.0-capabilities.json"
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
TYPE_POLICY = ROOT / "provider-type-policy.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(values: object) -> list[str]:
    result: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = str(value).strip().casefold()
        if item and item not in result:
            result.append(item)
    return result


baseline = load(BASELINE)
manifest = load(MANIFEST)
overrides = load(OVERRIDES)
type_policy = load(TYPE_POLICY)

current = {
    str(row.get("id") or "").casefold(): row
    for row in manifest.get("scrapers") or []
    if isinstance(row, dict) and str(row.get("id") or "").strip()
}
caps = overrides.get("provider_capabilities") or {}
patches = overrides.get("provider_patches") or {}
authoritative_type_policy = {
    str(provider_id).casefold(): norm(config.get("supportedTypes"))
    for provider_id, config in (type_policy.get("providers") or {}).items()
    if isinstance(config, dict)
}

missing = sorted(set(baseline["providers"]) - set(current))
assert not missing, f"5.21.0 production providers disappeared: {missing}"

hls_regressions: list[str] = []
semantic_regressions: list[str] = []
capability_regressions: list[str] = []

for provider_id, old in baseline["providers"].items():
    row = current[provider_id]
    old_formats = norm(old.get("formats"))
    now_formats = norm(row.get("formats"))
    if "m3u8" in old_formats and "m3u8" not in now_formats:
        hls_regressions.append(
            f"{provider_id}: 5.21.0 had m3u8, current formats={now_formats}"
        )

    canonical = norm(row.get("canonicalSupportedTypes"))
    semantic_now = canonical or norm(row.get("supportedTypes"))
    old_types = norm(old.get("supportedTypes"))

    # User-confirmed policies are exact semantic contracts.
    policy_types = authoritative_type_policy.get(provider_id)
    if policy_types:
        if semantic_now != policy_types:
            semantic_regressions.append(
                f"{provider_id}: policy semantic types {policy_types}, current semantic={semantic_now}"
            )
    elif "anime" in old_types:
        # Historical movie/tv on anime-centric providers may have been Nuvio
        # transport aliases, but semantic anime support must never disappear.
        if "anime" not in semantic_now:
            semantic_regressions.append(
                f"{provider_id}: 5.21.0 had anime support, current semantic={semantic_now}"
            )
    else:
        lost = [value for value in old_types if value not in semantic_now]
        if lost:
            semantic_regressions.append(
                f"{provider_id}: lost semantic types {lost}; current={semantic_now}"
            )

    cap = caps.get(provider_id) if isinstance(caps.get(provider_id), dict) else {}
    patch = patches.get(provider_id) if isinstance(patches.get(provider_id), dict) else {}
    now_contract = {
        "strategy": patch.get("capability") or cap.get("strategy"),
        "validation": cap.get("validation"),
        "allowHtml": cap.get("allow_html_url"),
        "requiresDirect": cap.get("requires_direct_media"),
    }
    for key in ("validation", "allowHtml", "requiresDirect"):
        old_value = old.get(key)
        if old_value is not None and now_contract.get(key) != old_value:
            capability_regressions.append(
                f"{provider_id}: {key} {old_value!r} -> {now_contract.get(key)!r}"
            )

playback = overrides.get("playback_integrity_policy") or {}
pre = [str(value) for value in playback.get("pre_media_discovery_hooks") or []]
post = [str(value) for value in playback.get("post_media_discovery_hooks") or []]
assert playback.get("enabled") is True, "global playback integrity must remain enabled"
assert "scripts/provider_patches/hls_runtime_integrity_v1.py" in pre
assert "scripts/provider_patches/hls_master_audio_preserver_v1.py" in post
assert playback.get("hls_master_external_audio") == "preserve_master_playlist"

assert not hls_regressions, "HLS capability regressions:\n- " + "\n- ".join(hls_regressions)
assert not semantic_regressions, "semantic type regressions:\n- " + "\n- ".join(semantic_regressions)
assert not capability_regressions, "provider runtime capability regressions:\n- " + "\n- ".join(capability_regressions)

print(
    "5.21.0 provider capability baseline preserved: "
    f"providers={len(baseline['providers'])} hls_global=ok semantic=ok runtime_contract=ok"
)
