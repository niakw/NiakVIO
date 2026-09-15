#!/usr/bin/env python3
"""Global runtime/client adaptations must stay Core-owned across all 96 bundles."""
from __future__ import annotations

import json
from pathlib import Path
from current_provider_scope import active_provider_count

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
APPLY = (ROOT / "scripts/apply_provider_overrides.py").read_text(encoding="utf-8")
RUNTIME = (ROOT / "scripts/provider_patches/global_runtime_compat_v1.py").read_text(encoding="utf-8")
DESKTOP = (ROOT / "scripts/provider_patches/desktop_runtime_compat_v1.py").read_text(encoding="utf-8")
SANITIZER_BASE = (ROOT / "scripts/provider_patches/stream_output_sanitizer.py").read_text(encoding="utf-8")
SANITIZER_V8 = (ROOT / "scripts/provider_patches/stream_output_sanitizer_v8.py").read_text(encoding="utf-8")

CORE_RUNTIME = "scripts/provider_patches/global_runtime_compat_v1.py"
CORE_DESKTOP = "scripts/provider_patches/desktop_runtime_compat_v1.py"
CORE_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"
CORE_MEDIA_SAFETY = "scripts/provider_patches/runtime_capability_media_safety_v4.py"

# Architecture ownership: these are Core-managed bricks. Provider rows may pass
# data/options but may never own/materialize them in provider patch_scripts.
assert 'GLOBAL_RUNTIME_COMPAT = "scripts/provider_patches/global_runtime_compat_v1.py"' in APPLY
assert 'GLOBAL_DESKTOP_RUNTIME_COMPAT = "scripts/provider_patches/desktop_runtime_compat_v1.py"' in APPLY
assert 'GLOBAL_STREAM_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v8.py"' in APPLY
assert 'GLOBAL_RUNTIME_MEDIA_SAFETY = "scripts/provider_patches/runtime_capability_media_safety_v4.py"' in APPLY
assert "provider_patches.{provider_id}.patch_scripts contains Core-global modules" in APPLY

patches = OVERRIDES.get("provider_patches") or {}
for provider_id, row in patches.items():
    if not isinstance(row, dict):
        continue
    scripts = [str(value) for value in row.get("patch_scripts") or []]
    leaked = sorted(set(scripts) & {CORE_RUNTIME, CORE_DESKTOP, CORE_SANITIZER, CORE_MEDIA_SAFETY})
    assert not leaked, (provider_id, leaked)

# Timers/URL/fetch portability are global Core behavior, never a named provider fix.
assert 'MANAGED_FIX_ID = "CORE.RUNTIME_COMPAT.V1"' in RUNTIME
for token in ('typeof g.setTimeout!=="function"', 'typeof g.clearTimeout!=="function"', 'staleMutableUrl', 'compatFetch'):
    assert token in RUNTIME, token
assert 'MANAGED_FIX_ID = "CORE.DESKTOP_RUNTIME_COMPAT.V1"' in DESKTOP
assert 'forbidden = {"domain_replacements", "domain_failover"}' in DESKTOP

# Terminal returned-media rejection is likewise Core-global. HTTP 403/404/410
# are conclusive invalidity; V8 also converts unknown/opaque ordinary probes to
# fail-closed rather than leaking them to official clients.
assert 'status===403||status===404||status===410' in SANITIZER_BASE
assert 'MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"' in SANITIZER_V8
assert 'return verdict===true?clearPrivateProofs(item.stream):null;' in SANITIZER_V8
for forbidden in ("streamflix", "movix", "vidrock", "cineby", "coflix"):
    assert forbidden not in SANITIZER_V8.casefold(), forbidden

rows = MANIFEST.get("scrapers") or []
assert len(rows) == active_provider_count()
for row in rows:
    provider_id = str(row.get("id") or "")
    path = ROOT / str(row.get("filename") or "")
    assert path.is_file(), (provider_id, path)
    text = path.read_text(encoding="utf-8")
    boundary = text.find("/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */")
    assert boundary >= 0, provider_id
    runtime_at = text.find("/* STARTFIX:CORE.RUNTIME_COMPAT.V1 */")
    sanitizer_at = text.find("/* STARTFIX:CORE.STREAM_SANITIZER.V6 */")
    assert runtime_at > boundary, provider_id
    assert sanitizer_at > boundary, provider_id
    assert text.count("/* STARTFIX:CORE.RUNTIME_COMPAT.V1 */") == 1, provider_id
    assert text.count("/* CLOSEFIX:CORE.RUNTIME_COMPAT.V1 */") == 1, provider_id
    assert text.count("/* STARTFIX:CORE.STREAM_SANITIZER.V6 */") == 1, provider_id
    assert text.count("/* CLOSEFIX:CORE.STREAM_SANITIZER.V6 */") == 1, provider_id

print("GLOBAL_CORE_RUNTIME_OWNERSHIP_OK providers=96 timers=core 403=core sanitizer_v8=strict provider_specific_runtime_hacks=forbidden")
