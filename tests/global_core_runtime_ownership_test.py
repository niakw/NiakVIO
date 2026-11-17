#!/usr/bin/env python3
"""Global runtime/client adaptations must stay Core-owned across the dynamic active provider scope."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_provider_scope import projection_active_provider_count, projection_active_provider_rows

OVERRIDES = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
APPLY = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
RUNTIME = (ROOT / "scripts/provider_patches/global_runtime_compat_v1.py").read_text(encoding="utf-8")
DESKTOP = (ROOT / "scripts/provider_patches/desktop_runtime_compat_v1.py").read_text(encoding="utf-8")
SANITIZER_BASE = (ROOT / "scripts/provider_patches/stream_output_sanitizer.py").read_text(encoding="utf-8")
SANITIZER_V10 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v10.py").read_text(encoding="utf-8")
SANITIZER_V11 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v11.py").read_text(encoding="utf-8")
SANITIZER_V12 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v12.py").read_text(encoding="utf-8")
STREAM_SCORE = (ROOT / "scripts/provider_patches/global_stream_score_v1.py").read_text(encoding="utf-8")
TELEMETRY = (ROOT / "scripts/provider_patches/global_telemetry_v1.py").read_text(encoding="utf-8")
MATERIALIZATION = json.loads((ROOT / "provider-v3-materialization.json").read_text(encoding="utf-8"))

REQUIRED_GLOBAL_CORE_IDS = (
    "CORE.HLS_RUNTIME_INTEGRITY.V1",
    "CORE.PROVIDER_SECURITY_BOUNDARY.V1",
    "CORE.RUNTIME_COMPAT.V1",
    "CORE.STREAM_FACTS.V1",
    "CORE.STREAM_SANITIZER.V6",
    "CORE.STREAM_IDENTITY.V1",
    "CORE.MEDIA_TYPE_RESOLUTION.V1",
    "CORE.STREAM_PRESENTATION.V1",
    "CORE.PROVIDER_BRANDING.V1",
    "CORE.RUNTIME_MEDIA_SAFETY.V4",
    "CORE.STREAM_SCORE.V1",
    "CORE.TELEMETRY.V1",
)


CORE_RUNTIME = "scripts/provider_patches/global_runtime_compat_v1.py"
CORE_DESKTOP = "scripts/provider_patches/desktop_runtime_compat_v1.py"
CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v12.py"
CORE_STREAM_SCORE = "scripts/provider_patches/global_stream_score_v1.py"
CORE_TELEMETRY = "scripts/provider_patches/global_telemetry_v1.py"
CORE_MEDIA_SAFETY = "scripts/provider_patches/runtime_capability_media_safety_v4.py"

# Architecture ownership: these are Core-managed bricks. Provider rows may pass
# data/options but may never own/materialize them in provider patch_scripts.
assert 'GLOBAL_RUNTIME_COMPAT = "scripts/provider_patches/global_runtime_compat_v1.py"' in APPLY
assert 'GLOBAL_DESKTOP_RUNTIME_COMPAT = "scripts/provider_patches/desktop_runtime_compat_v1.py"' in APPLY
assert 'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v12.py"' in APPLY
assert 'GLOBAL_STREAM_SCORE = "scripts/provider_patches/global_stream_score_v1.py"' in APPLY
assert 'GLOBAL_PROVIDER_BRANDING = "scripts/provider_patches/global_provider_branding_v1.py"' in APPLY
assert 'GLOBAL_TELEMETRY = "scripts/provider_patches/global_telemetry_v1.py"' in APPLY
assert 'GLOBAL_RUNTIME_MEDIA_SAFETY = "scripts/provider_patches/runtime_capability_media_safety_v4.py"' in APPLY
assert "provider_patches.{provider_id}.patch_scripts contains Core-global modules" in APPLY

patches = OVERRIDES.get("provider_patches") or {}
for provider_id, row in patches.items():
    if not isinstance(row, dict):
        continue
    scripts = [str(value) for value in row.get("patch_scripts") or []]
    leaked = sorted(set(scripts) & {CORE_RUNTIME, CORE_DESKTOP, CORE_SANITIZER, CORE_MEDIA_SAFETY, CORE_STREAM_SCORE, CORE_TELEMETRY})
    assert not leaked, (provider_id, leaked)

# Timers/URL/fetch portability are global Core behavior, never a named provider fix.
assert 'MANAGED_FIX_ID = "CORE.RUNTIME_COMPAT.V1"' in RUNTIME
for token in ('typeof g.setTimeout!=="function"', 'typeof g.clearTimeout!=="function"', 'staleMutableUrl', 'compatFetch'):
    assert token in RUNTIME, token
assert 'MANAGED_FIX_ID = "CORE.DESKTOP_RUNTIME_COMPAT.V1"' in DESKTOP
assert 'forbidden = {"domain_replacements", "domain_failover"}' in DESKTOP

# Terminal returned-media rejection is likewise Core-global. HTTP 403/404/410
# are conclusive invalidity; V8 also converts unknown/opaque ordinary probes to
# fail-closed rather than leaking them to official clients. V10 preserves only
# bounded terminal-probe network evidence for the outer Stream Score Bloc.
assert 'status===403||status===404||status===410' in SANITIZER_BASE
assert 'MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"' in SANITIZER_V10
assert "NUVIO_STREAM_OUTPUT_NETWORK_EVIDENCE_V10" in SANITIZER_V10
assert "__nuvioStreamNetworkEvidenceV1" in SANITIZER_V10
assert "NUVIO_STREAM_OUTPUT_HLS_MASTER_PREFERENCE_V11" in SANITIZER_V11
assert "__nuvioHlsMasterAudioCountV1" in SANITIZER_V11
assert "NUVIO_STREAM_OUTPUT_MULTI_AUDIO_FRONTIER_V12" in SANITIZER_V12
assert "probeLimit=Math.min(candidates.length,16)" in SANITIZER_V12
assert 'MANAGED_FIX_ID = "CORE.STREAM_SCORE.V1"' in STREAM_SCORE
assert "NUVIO_GLOBAL_STREAM_SCORE_V1" in STREAM_SCORE
assert 'MANAGED_FIX_ID = "CORE.TELEMETRY.V1"' in TELEMETRY
assert "NUVIO_GLOBAL_TELEMETRY_V1" in TELEMETRY
assert "accountPseudonym" in TELEMETRY
assert "localStorage" in TELEMETRY
assert "rawMediaIdentifiers" in TELEMETRY
assert '[id].concat(clean)' in STREAM_SCORE
assert 'out.displayBadges=g?[g].concat(cleanDisplay):cleanDisplay' in STREAM_SCORE
for forbidden in ("streamflix", "movix", "vidrock", "cineby", "coflix"):
    assert forbidden not in SANITIZER_V12.casefold(), forbidden

rows = projection_active_provider_rows()
assert len(rows) == projection_active_provider_count()
materialized = {
    str(row.get("provider") or "").strip().casefold().replace("_", "-"): row
    for row in MATERIALIZATION.get("providers") or []
    if isinstance(row, dict)
}
assert set(materialized) == {
    str(row.get("id") or "").strip().casefold().replace("_", "-")
    for row in rows
}, (len(materialized), len(rows))
for row in rows:
    provider_id = str(row.get("id") or "")
    path = ROOT / str(row.get("filename") or "")
    assert path.is_file(), (provider_id, path)
    text = path.read_text(encoding="utf-8")
    boundary = text.find("/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */")
    assert boundary >= 0, provider_id
    canonical_provider_id = provider_id.strip().casefold().replace("_", "-")
    ledger = materialized[canonical_provider_id]
    ledger_fix_ids = set(ledger.get("fixIds") or [])
    missing_ledger = sorted(set(REQUIRED_GLOBAL_CORE_IDS) - ledger_fix_ids)
    assert not missing_ledger, (provider_id, "materialization-ledger", missing_ledger)

    sanitizer_start = text.find("/* STARTFIX:CORE.STREAM_SANITIZER.V6 */")
    sanitizer_close = text.find("/* CLOSEFIX:CORE.STREAM_SANITIZER.V6 */", sanitizer_start)
    assert sanitizer_start >= 0 and sanitizer_close > sanitizer_start, provider_id
    sanitizer_region = text[sanitizer_start:sanitizer_close]
    assert '"probeAllUrls":true' in sanitizer_region, (provider_id, "probeAllUrls")
    assert '"maxProbes":40' in sanitizer_region, (provider_id, "maxProbes", sanitizer_region[:500])

    positions = {}
    for fix_id in REQUIRED_GLOBAL_CORE_IDS:
        start_marker = f"/* STARTFIX:{fix_id} */"
        close_marker = f"/* CLOSEFIX:{fix_id} */"
        assert text.count(start_marker) == 1, (provider_id, start_marker, text.count(start_marker))
        assert text.count(close_marker) == 1, (provider_id, close_marker, text.count(close_marker))
        positions[fix_id] = text.find(start_marker)
        assert positions[fix_id] > boundary, (provider_id, fix_id, positions[fix_id], boundary)

    # These are output/request wrappers whose ordering is itself part of the
    # shared Core ABI. HLS/security run before host compatibility; normalized
    # facts preserve discovery metadata; terminal resolution then runs before
    # identity/media type/presentation so downstream checks see the real media.
    # Safety precedes scoring; telemetry remains the outermost observer.
    ordered = (
        "CORE.HLS_RUNTIME_INTEGRITY.V1",
        "CORE.PROVIDER_SECURITY_BOUNDARY.V1",
        "CORE.RUNTIME_COMPAT.V1",
        "CORE.STREAM_FACTS.V1",
        "CORE.STREAM_SANITIZER.V6",
        "CORE.STREAM_IDENTITY.V1",
        "CORE.MEDIA_TYPE_RESOLUTION.V1",
        "CORE.STREAM_PRESENTATION.V1",
        "CORE.RUNTIME_MEDIA_SAFETY.V4",
        "CORE.PROVIDER_BRANDING.V1",
        "CORE.STREAM_SCORE.V1",
        "CORE.TELEMETRY.V1",
    )
    assert [positions[key] for key in ordered] == sorted(positions[key] for key in ordered), (
        provider_id,
        [(key, positions[key]) for key in ordered],
    )

print(f"GLOBAL_CORE_RUNTIME_OWNERSHIP_OK providers={len(rows)} scope=Global+France required_core={len(REQUIRED_GLOBAL_CORE_IDS)} timers=core 403=core facts=core identity=core hls=core presentation=core branding=core sanitizer_v11=master-audio+network-evidence stream_score=core telemetry=core provider_specific_runtime_hacks=forbidden")
