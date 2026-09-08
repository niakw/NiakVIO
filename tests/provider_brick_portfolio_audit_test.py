#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from apply_provider_overrides import apply_overrides
from provider_base_store import CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS, canonical_id, requires_clean_reconstruction, resolve_runtime_base
from provider_patch_blocks import begin_marker, end_marker, owned_span, validate_managed_fixes

MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
PROVENANCE = json.loads((ROOT / "PROVENANCE.json").read_text(encoding="utf-8"))
ROWS = PROVENANCE.get("providers") or {}
FORCE_TRIGGER = ROOT / ".github" / "triggers" / "force-clean-provider-reconstruction.json"

CORE_ORDER = [
    # Textual/materialization order. Request-side media type resolution wraps
    # provider/facts/identity; output-only presentation/branding/sanitizer wrap it.
    "CORE.CATALOGUE_ALIAS_RECOVERY.V2",
    "CORE.MEDIA_ENRICHMENT.V1",
    "CORE.RUNTIME_MEDIA_SAFETY.V4",
    "CORE.HLS_RUNTIME_INTEGRITY.V1",
    "CORE.PROVIDER_SECURITY_BOUNDARY.V1",
    "CORE.RUNTIME_COMPAT.V1",
    "CORE.STREAM_FACTS.V1",
    "CORE.STREAM_IDENTITY.V1",
    "CORE.MEDIA_TYPE_RESOLUTION.V1",
    "CORE.STREAM_PRESENTATION.V1",
    "CORE.PROVIDER_BRANDING.V1",
    "CORE.STREAM_SANITIZER.V6",
]

BLOCK_START = re.compile(r"/\* START NIAKVIO_FIX:([^*]+?) \*/")

UNIVERSAL_CORE_IDS = {
    "CORE.RUNTIME_MEDIA_SAFETY.V4",
    "CORE.PROVIDER_SECURITY_BOUNDARY.V1",
    "CORE.RUNTIME_COMPAT.V1",
    "CORE.STREAM_PRESENTATION.V1",
    "CORE.PROVIDER_BRANDING.V1",
    "CORE.STREAM_SANITIZER.V6",
    "CORE.MEDIA_TYPE_RESOLUTION.V1",
}
CORE_BOUNDARY = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"


def forced_ids() -> set[str]:
    if not FORCE_TRIGGER.is_file():
        return set()
    payload = json.loads(FORCE_TRIGGER.read_text(encoding="utf-8"))
    if payload.get("mode") != "explicit-one-shot":
        return set()
    return {
        canonical_id(str(value or ""))
        for value in payload.get("providers") or []
        if canonical_id(str(value or ""))
    }


def stage_rows(stage: Path) -> dict[str, dict]:
    registry = json.loads((stage / "candidates.json").read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for row in registry.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        provider_id = canonical_id(str(row.get("canonical_id") or row.get("upstream_id") or ""))
        if provider_id:
            result[provider_id] = row
    return result


def block_fingerprints(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for fix_id in validate_managed_fixes(text):
        span = owned_span(text, fix_id)
        if span is None:
            result[fix_id] = "missing-owned-span"
            continue
        body = text[span[0]:span[1]]
        result[fix_id] = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    return result


def first_diff(left: str, right: str) -> tuple[int, str, str]:
    limit = min(len(left), len(right))
    idx = next((i for i in range(limit) if left[i] != right[i]), limit)
    lo = max(0, idx - 120)
    hi_left = min(len(left), idx + 240)
    hi_right = min(len(right), idx + 240)
    return idx, left[lo:hi_left].replace("\n", "\\n"), right[lo:hi_right].replace("\n", "\\n")


def audit_order(provider_id: str, text: str) -> None:
    positions = {
        fix_id: text.find(begin_marker(fix_id))
        for fix_id in CORE_ORDER
        if begin_marker(fix_id) in text
    }
    previous = -1
    for fix_id in CORE_ORDER:
        if fix_id not in positions:
            continue
        if positions[fix_id] <= previous:
            raise AssertionError(f"{provider_id}: Core brick order regression at {fix_id}")
        previous = positions[fix_id]


def audit_composed(provider_id: str, first_text: str, second_text: str, records: list[dict]) -> tuple[list[str], list[str]]:
    first_ids = validate_managed_fixes(first_text)
    second_ids = validate_managed_fixes(second_text)
    audit_order(provider_id, first_text)

    errors: list[str] = []
    if first_text.count(CORE_BOUNDARY) != 1:
        errors.append(
            f"{provider_id}: canonical Core boundary count={first_text.count(CORE_BOUNDARY)} expected=1"
        )
    missing = sorted(UNIVERSAL_CORE_IDS - set(first_ids))
    if missing:
        errors.append(f"{provider_id}: missing universal Core bricks={','.join(missing)}")
    if first_ids != second_ids:
        errors.append(
            f"{provider_id}: managed Core id set changed on reapply "
            f"first={','.join(first_ids)} second={','.join(second_ids)}"
        )
    if second_text != first_text:
        idx, left_ctx, right_ctx = first_diff(first_text, second_text)
        first_blocks = block_fingerprints(first_text)
        second_blocks = block_fingerprints(second_text)
        changed_blocks = sorted(
            fix_id
            for fix_id in set(first_blocks) | set(second_blocks)
            if first_blocks.get(fix_id) != second_blocks.get(fix_id)
        )
        errors.append(
            f"{provider_id}: non_idempotent offset={idx} "
            f"changed_blocks={','.join(changed_blocks) or 'none'} "
            f"first_ctx={left_ctx!r} second_ctx={right_ctx!r}"
        )
    paths = [
        str(record.get("path") or "")
        for record in records
        if isinstance(record, dict) and record.get("type") == "patch_script"
    ]
    return errors, paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        type=Path,
        help="Audit already reconstructed/materialized staging candidates instead of current ProviderBase files.",
    )
    parser.add_argument(
        "--published",
        action="store_true",
        help="Audit the exact Provider JS files referenced by the current manifest.",
    )
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Require every manifest provider to exist in the supplied staging registry.",
    )
    args = parser.parse_args()

    checked = 0
    deferred = 0
    managed_counts: dict[str, int] = {}
    applied_script_counts: dict[str, int] = {}
    portfolio_errors: list[str] = []
    force = forced_ids()
    if args.stage and args.published:
        raise SystemExit("--stage and --published are mutually exclusive")
    staged = stage_rows(args.stage.resolve()) if args.stage else {}

    for entry in MANIFEST.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = canonical_id(str(entry.get("id") or ""))
        if not provider_id:
            continue

        row = ROWS.get(provider_id)
        if not isinstance(row, dict):
            raise AssertionError(f"{provider_id}: missing provenance row")

        if args.published:
            local_path = str(entry.get("filename") or "").strip()
            if not local_path:
                portfolio_errors.append(f"{provider_id}: manifest provider filename missing")
                continue
            target = (ROOT / local_path).resolve()
            providers_root = (ROOT / "providers").resolve()
            if providers_root not in target.parents or not target.is_file():
                portfolio_errors.append(f"{provider_id}: published provider file missing: {local_path}")
                continue
            first_text = target.read_text(encoding="utf-8", errors="strict")
            try:
                second, records = apply_overrides(
                    provider_id,
                    first_text.encode("utf-8"),
                    phase="discovery",
                )
                second_text = second.decode("utf-8", errors="strict") if isinstance(second, bytes) else str(second)
                errors, record_paths = audit_composed(provider_id, first_text, second_text, records)
                portfolio_errors.extend(errors)
                fix_ids = validate_managed_fixes(first_text)
            except Exception as exc:
                portfolio_errors.append(f"{provider_id}: published composition exception: {type(exc).__name__}: {exc}")
                continue
        elif args.stage:
            candidate = staged.get(provider_id)
            if not candidate:
                if args.require_all:
                    portfolio_errors.append(f"{provider_id}: missing reconstructed staging candidate")
                continue
            local_path = str(candidate.get("local_path") or "").strip()
            if not local_path:
                portfolio_errors.append(f"{provider_id}: staging candidate missing local_path")
                continue
            target = (args.stage.resolve() / local_path).resolve()
            if args.stage.resolve() not in target.parents or not target.is_file():
                portfolio_errors.append(f"{provider_id}: staging provider file missing: {local_path}")
                continue
            first_text = target.read_text(encoding="utf-8", errors="strict")
            clean_seed_origin = str(candidate.get("candidate_code_origin") or "") in {
                "new-niakvio-clean-seed",
                "pending-niakvio-clean-reconstruction-v2",
            }
            try:
                second, records = apply_overrides(
                    provider_id,
                    first_text.encode("utf-8"),
                    phase="discovery",
                    excluded_patch_scripts=(
                        CLEAN_RECONSTRUCTION_EXCLUDED_PATCH_SCRIPTS
                        if clean_seed_origin
                        else None
                    ),
                )
                second_text = second.decode("utf-8", errors="strict") if isinstance(second, bytes) else str(second)
                errors, record_paths = audit_composed(provider_id, first_text, second_text, records)
                portfolio_errors.extend(errors)
                fix_ids = validate_managed_fixes(first_text)
            except Exception as exc:
                portfolio_errors.append(f"{provider_id}: staged composition exception: {type(exc).__name__}: {exc}")
                continue
        else:
            # A forced Deep exists specifically to replace pending legacy bases.
            # Auditing those obsolete bytes before reconstruction would prevent
            # the corrective rebuild from ever running. Defer only providers
            # explicitly named by the one-shot trigger; all others still fail closed.
            if requires_clean_reconstruction(row) and provider_id in force:
                deferred += 1
                print(f"FIELD_PROVIDER_BRICK_DEFERRED provider={provider_id} reason=explicit_forced_clean_reconstruction")
                continue

            base_path, _digest = resolve_runtime_base(provider_id, row, require=True)
            assert base_path is not None
            original_bytes = base_path.read_bytes()
            original_sha = hashlib.sha256(original_bytes).hexdigest()
            base_text = original_bytes.decode("utf-8", errors="strict")
            forbidden_markers = (
                "/* STARTFIX:",
                "/* CLOSEFIX:",
                "/* FIXDATA:",
                "/* START NIAKVIO_FIX:",
                "/* END NIAKVIO_FIX:",
            )
            if any(marker in base_text for marker in forbidden_markers):
                raise AssertionError(f"{provider_id}: managed fix leaked into ProviderBase")

            try:
                first, records = apply_overrides(provider_id, original_bytes, phase="discovery")
                first_text = first.decode("utf-8", errors="strict") if isinstance(first, bytes) else str(first)
                second, _second_records = apply_overrides(
                    provider_id,
                    first_text.encode("utf-8"),
                    phase="discovery",
                )
                second_text = second.decode("utf-8", errors="strict") if isinstance(second, bytes) else str(second)
                errors, record_paths = audit_composed(provider_id, first_text, second_text, records)
                portfolio_errors.extend(errors)
                fix_ids = validate_managed_fixes(first_text)
            except Exception as exc:
                portfolio_errors.append(f"{provider_id}: base composition exception: {type(exc).__name__}: {exc}")
                continue

            if hashlib.sha256(base_path.read_bytes()).hexdigest() != original_sha:
                raise AssertionError(f"{provider_id}: ProviderBase source mutated during compilation")

        for fix_id in fix_ids:
            managed_counts[fix_id] = managed_counts.get(fix_id, 0) + 1
        for script in record_paths:
            applied_script_counts[script] = applied_script_counts.get(script, 0) + 1
        checked += 1

    expected = len([
        x for x in MANIFEST.get("scrapers") or []
        if isinstance(x, dict) and str(x.get("id") or "").strip()
    ])
    if args.published:
        if args.require_all and checked != expected:
            portfolio_errors.append(f"published audit incomplete: checked={checked} expected={expected}")
    elif args.stage:
        if args.require_all and checked != expected:
            portfolio_errors.append(f"staging audit incomplete: checked={checked} expected={expected}")
    elif checked + deferred != expected:
        portfolio_errors.append(
            f"base audit incomplete: checked={checked} deferred={deferred} expected={expected}"
        )

    if portfolio_errors:
        for error in portfolio_errors:
            print("FIELD_PROVIDER_BRICK_ERROR " + error)
        raise AssertionError(f"provider brick portfolio errors={len(portfolio_errors)}")

    scope = "published" if args.published else ("staging" if args.stage else "providerbase")
    print(
        "FIELD_PROVIDER_BRICK_AUDIT "
        f"scope={scope} providers={checked} deferred={deferred} "
        f"managed_ids={len(managed_counts)} active_patch_scripts={len(applied_script_counts)}"
    )
    print("provider brick portfolio audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
