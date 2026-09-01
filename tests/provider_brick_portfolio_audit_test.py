#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from apply_provider_overrides import apply_overrides
from provider_base_store import canonical_id, resolve_runtime_base
from provider_patch_blocks import validate_managed_fixes

MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
PROVENANCE = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
ROWS = PROVENANCE.get("providers") or {}

CORE_ORDER = [
    "CORE.MEDIA_TYPE_RESOLUTION.V1",
    "CORE.RUNTIME_MEDIA_SAFETY.V4",
    "CORE.RUNTIME_COMPAT.V1",
    "CORE.STREAM_FACTS.V1",
    "CORE.STREAM_IDENTITY.V1",
    "CORE.STREAM_PRESENTATION.V1",
    "CORE.PROVIDER_BRANDING.V1",
]

checked = 0
managed_counts: dict[str, int] = {}
applied_script_counts: dict[str, int] = {}

for entry in MANIFEST.get("scrapers") or []:
    if not isinstance(entry, dict):
        continue
    provider_id = canonical_id(str(entry.get("id") or ""))
    if not provider_id:
        continue
    row = ROWS.get(provider_id)
    if not isinstance(row, dict):
        raise AssertionError(f"{provider_id}: missing provenance row")

    base_path, _digest = resolve_runtime_base(provider_id, row, require=True)
    assert base_path is not None
    original_bytes = base_path.read_bytes()
    original_sha = hashlib.sha256(original_bytes).hexdigest()
    base_text = original_bytes.decode("utf-8", errors="strict")

    if "NIAKVIO_FIX" in base_text:
        raise AssertionError(f"{provider_id}: managed fix leaked into ProviderBase")

    first, records = apply_overrides(provider_id, original_bytes, phase="discovery")
    first_text = first.decode("utf-8", errors="strict") if isinstance(first, bytes) else str(first)

    second, second_records = apply_overrides(
        provider_id,
        first_text.encode("utf-8"),
        phase="discovery",
    )
    second_text = second.decode("utf-8", errors="strict") if isinstance(second, bytes) else str(second)

    if second_text != first_text:
        raise AssertionError(f"{provider_id}: full Lego composition is not byte-idempotent")

    if hashlib.sha256(base_path.read_bytes()).hexdigest() != original_sha:
        raise AssertionError(f"{provider_id}: ProviderBase source mutated during compilation")

    fix_ids = validate_managed_fixes(first_text)
    for fix_id in fix_ids:
        managed_counts[fix_id] = managed_counts.get(fix_id, 0) + 1

    positions = {
        fix_id: first_text.find(f"/* START NIAKVIO_FIX:{fix_id} */")
        for fix_id in CORE_ORDER
        if f"/* START NIAKVIO_FIX:{fix_id} */" in first_text
    }
    previous = -1
    for fix_id in CORE_ORDER:
        if fix_id not in positions:
            continue
        if positions[fix_id] <= previous:
            raise AssertionError(
                f"{provider_id}: Core brick order regression at {fix_id}"
            )
        previous = positions[fix_id]

    record_paths = [
        str(record.get("path") or "")
        for record in records
        if isinstance(record, dict) and record.get("type") == "patch_script"
    ]
    for script in record_paths:
        applied_script_counts[script] = applied_script_counts.get(script, 0) + 1


    checked += 1

expected = len([x for x in MANIFEST.get("scrapers") or [] if isinstance(x, dict) and str(x.get("id") or "").strip()])
if checked != expected:
    raise AssertionError(f"portfolio audit incomplete: checked={checked} expected={expected}")

print(
    "FIELD_PROVIDER_BRICK_AUDIT "
    f"providers={checked} managed_ids={len(managed_counts)} "
    f"active_patch_scripts={len(applied_script_counts)}"
)
print("provider brick portfolio audit passed")
