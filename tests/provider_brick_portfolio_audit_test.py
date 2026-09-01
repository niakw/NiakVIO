#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
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
    # Textual/materialization order. getStreams wrapper execution is the reverse:
    # media-type is intentionally outermost and executes first.
    "CORE.CATALOGUE_ALIAS_RECOVERY.V2",
    "CORE.MEDIA_ENRICHMENT.V1",
    "CORE.RUNTIME_MEDIA_SAFETY.V4",
    "CORE.HLS_RUNTIME_INTEGRITY.V1",
    "CORE.RUNTIME_COMPAT.V1",
    "CORE.STREAM_FACTS.V1",
    "CORE.STREAM_IDENTITY.V1",
    "CORE.STREAM_PRESENTATION.V1",
    "CORE.PROVIDER_BRANDING.V1",
    "CORE.STREAM_SANITIZER.V6",
    "CORE.MEDIA_TYPE_RESOLUTION.V1",
]

checked = 0
managed_counts: dict[str, int] = {}
applied_script_counts: dict[str, int] = {}
portfolio_errors: list[str] = []

BLOCK_START = re.compile(r"/\* START NIAKVIO_FIX:([^*]+?) \*/")


def block_fingerprints(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in BLOCK_START.finditer(text):
        fix_id = match.group(1).strip()
        end_marker = f"/* END NIAKVIO_FIX:{fix_id} */"
        end = text.find(end_marker, match.end())
        if end < 0:
            result[fix_id] = "unterminated"
            continue
        body = text[match.start(): end + len(end_marker)]
        result[fix_id] = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return result


def first_diff(left: str, right: str) -> tuple[int, str, str]:
    limit = min(len(left), len(right))
    idx = next((i for i in range(limit) if left[i] != right[i]), limit)
    lo = max(0, idx - 120)
    hi_left = min(len(left), idx + 240)
    hi_right = min(len(right), idx + 240)
    return idx, left[lo:hi_left].replace("\n", "\\n"), right[lo:hi_right].replace("\n", "\\n")

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
        idx, left_ctx, right_ctx = first_diff(first_text, second_text)
        first_blocks = block_fingerprints(first_text)
        second_blocks = block_fingerprints(second_text)
        changed_blocks = sorted(
            fix_id
            for fix_id in set(first_blocks) | set(second_blocks)
            if first_blocks.get(fix_id) != second_blocks.get(fix_id)
        )
        first_paths = [
            str(record.get("path") or "")
            for record in records
            if isinstance(record, dict) and record.get("type") == "patch_script"
        ]
        second_paths = [
            str(record.get("path") or "")
            for record in second_records
            if isinstance(record, dict) and record.get("type") == "patch_script"
        ]
        portfolio_errors.append(
            f"{provider_id}: non_idempotent offset={idx} "
            f"changed_blocks={','.join(changed_blocks) or 'none'} "
            f"first_scripts={first_paths} second_scripts={second_paths} "
            f"first_ctx={left_ctx!r} second_ctx={right_ctx!r}"
        )

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

if portfolio_errors:
    for error in portfolio_errors:
        print("FIELD_PROVIDER_BRICK_NON_IDEMPOTENT " + error)
    raise AssertionError(
        f"provider brick portfolio non-idempotent providers={len(portfolio_errors)}"
    )

print(
    "FIELD_PROVIDER_BRICK_AUDIT "
    f"providers={checked} managed_ids={len(managed_counts)} "
    f"active_patch_scripts={len(applied_script_counts)}"
)
print("provider brick portfolio audit passed")
