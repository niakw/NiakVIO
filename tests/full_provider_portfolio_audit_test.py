#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
rows = manifest.get("scrapers") or []
assert isinstance(rows, list) and rows, "manifest must contain provider scrapers"
provider_patches = overrides.get("provider_patches") or {}
assert isinstance(provider_patches, dict)

hard: list[str] = []
soft: list[str] = []
ids: list[str] = []
on_ids: list[str] = []
off_ids: list[str] = []
quarantined_ids: list[str] = []
hls_without_common_repair: list[str] = []
wrapper_counts: Counter[str] = Counter()


def canonical_from_row(row: dict) -> str:
    filename = str(row.get("filename") or "")
    if filename.startswith("providers/"):
        stem = Path(filename).name
        if "--" in stem:
            return stem.split("--", 1)[0].casefold()
        return Path(stem).stem.casefold()
    return str(row.get("id") or "").casefold()


for index, row in enumerate(rows):
    if not isinstance(row, dict):
        hard.append(f"row[{index}]:not_object")
        continue
    provider_id = canonical_from_row(row)
    display_id = str(row.get("id") or provider_id)
    ids.append(provider_id)
    enabled = row.get("enabled", True) is not False
    (on_ids if enabled else off_ids).append(provider_id)

    filename = str(row.get("filename") or "")
    if not filename:
        hard.append(f"{provider_id}:missing_filename")
        continue
    path = ROOT / filename
    if not path.is_file():
        hard.append(f"{provider_id}:missing_bundle:{filename}")
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        hard.append(f"{provider_id}:bundle_not_utf8:{filename}")
        continue

    cfg = provider_patches.get(provider_id) or {}
    if not isinstance(cfg, dict):
        hard.append(f"{provider_id}:override_not_object")
        cfg = {}
    scripts = [str(v) for v in (cfg.get("patch_scripts") or [])]
    capability = str(cfg.get("capability") or "").casefold()
    manifest_override = cfg.get("manifest_overrides") or {}
    explicitly_quarantined = (
        capability == "quarantined"
        or "scripts/provider_patches/quarantine_provider_v1.py" in scripts
        or (isinstance(manifest_override, dict) and manifest_override.get("enabled") is False)
    )
    if explicitly_quarantined:
        quarantined_ids.append(provider_id)
        if enabled:
            hard.append(f"{provider_id}:quarantined_but_enabled")
    elif not enabled:
        soft.append(f"{provider_id}:disabled_without_quarantine")

    sanitizer = text.find("/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:")
    target = text.rfind("/* NUVIO_TV_TARGET_MEDIA_V3:")
    sanitizer_count = text.count("/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:")
    target_count = text.count("/* NUVIO_TV_TARGET_MEDIA_V3:")
    repair_count = text.count("/* NUVIO_STREAM_OUTPUT_HLS_HTML_REPAIR_V7 */")
    strict_count = text.count("/* NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6 */")
    hls_integrity_count = text.count("/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:")

    wrapper_counts["sanitizer"] += sanitizer_count
    wrapper_counts["target_media"] += target_count
    wrapper_counts["hls_repair"] += repair_count
    wrapper_counts["strict_sanitizer"] += strict_count
    wrapper_counts["hls_integrity"] += hls_integrity_count

    if sanitizer_count > 1:
        hard.append(f"{provider_id}:duplicate_sanitizer:{sanitizer_count}")
    if target_count > 1:
        hard.append(f"{provider_id}:duplicate_target_media:{target_count}")
    if repair_count > 1:
        hard.append(f"{provider_id}:duplicate_hls_repair:{repair_count}")
    if strict_count > 1:
        hard.append(f"{provider_id}:duplicate_strict_sanitizer:{strict_count}")
    if repair_count and sanitizer < 0:
        hard.append(f"{provider_id}:hls_repair_without_sanitizer")
    if strict_count and not repair_count:
        hard.append(f"{provider_id}:strict_sanitizer_without_generic_repair")
    # Later textual wrappers are outer wrappers at runtime. If target-media is
    # rewrapped after the sanitizer, its final URL bypasses terminal validation.
    if sanitizer >= 0 and target >= 0 and sanitizer <= target:
        hard.append(
            f"{provider_id}:terminal_order_invalid:sanitizer={sanitizer}:target_media={target}"
        )

    formats = {str(v).casefold() for v in (row.get("formats") or [])}
    hls_capable = "m3u8" in formats or "hls" in formats
    has_common_hls_layer = repair_count > 0 or hls_integrity_count > 0
    if hls_capable and not has_common_hls_layer:
        hls_without_common_repair.append(provider_id)

# Canonical names are derived from filenames because manifest IDs may differ in
# case from provider-overrides keys. Filenames themselves must still be unique.
duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
if duplicates:
    hard.append("duplicate_canonical_ids:" + ",".join(duplicates))

print(
    "full provider portfolio audit: "
    f"total={len(rows)} on={len(on_ids)} off={len(off_ids)} "
    f"quarantined={len(set(quarantined_ids))} hard={len(hard)} soft={len(soft)}"
)
print("portfolio OFF: " + (",".join(sorted(off_ids)) or "none"))
print("portfolio quarantined: " + (",".join(sorted(set(quarantined_ids))) or "none"))
print(
    "portfolio HLS without common repair layer: "
    + (",".join(sorted(hls_without_common_repair)) or "none")
)
print("portfolio wrapper totals: " + json.dumps(dict(wrapper_counts), sort_keys=True))
if soft:
    print("portfolio observations: " + " | ".join(sorted(soft)))
if hard:
    raise AssertionError("full provider portfolio audit failed: " + " | ".join(sorted(hard)))
