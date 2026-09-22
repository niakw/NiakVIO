#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_patch_blocks import begin_marker, end_marker, owned_span, validate_managed_fixes  # noqa: E402
from apply_provider_overrides import _load_patch_module, load_overrides  # noqa: E402

MANIFEST = ROOT / "manifest.json"
CORE_BOUNDARY = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"

UNIVERSAL_CORE_IDS = {
    "CORE.RUNTIME_MEDIA_SAFETY.V4",
    "CORE.PROVIDER_SECURITY_BOUNDARY.V1",
    "CORE.RUNTIME_COMPAT.V1",
    "CORE.STREAM_PRESENTATION.V1",
    "CORE.PROVIDER_BRANDING.V1",
    "CORE.STREAM_SANITIZER.V6",
    "CORE.MEDIA_TYPE_RESOLUTION.V1",
}

MEDIA_TYPE_SOURCE = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
_media_source = MEDIA_TYPE_SOURCE.read_text(encoding="utf-8")
_media_revision_match = re.search(
    r'"revision"\s*:\s*"(tmdb-data-contract-launch-gate-v[^"]+)"',
    _media_source,
)
if _media_revision_match is None:
    raise AssertionError("Core media-type source exposes no launch-gate revision")
MEDIA_TYPE_REVISION = _media_revision_match.group(1)
LAUNCH_EVENT_GATE = 'if(providerEvent!=="launch")return []'
POSITIVE_OUTPUT_GATE = 'if(!hasProviderOutput(value))return []'


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    overrides = load_overrides()
    provider_patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    checked = 0
    quarantined = 0
    errors: list[str] = []

    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        relative = str(entry.get("filename") or "").strip()
        if not provider_id or not relative.startswith("providers/"):
            continue

        path = (ROOT / relative).resolve()
        try:
            path.relative_to((ROOT / "providers").resolve())
        except ValueError:
            errors.append(f"{provider_id}: unsafe provider path={relative}")
            continue
        if not path.is_file():
            errors.append(f"{provider_id}: missing published bundle={relative}")
            continue

        text = path.read_text(encoding="utf-8", errors="strict")
        if QUARANTINE_MARKER in text:
            quarantined += 1
            continue

        checked += 1
        boundary_count = text.count(CORE_BOUNDARY)
        if boundary_count != 1:
            errors.append(f"{provider_id}: Core boundary count={boundary_count} expected=1")
            continue

        try:
            fix_ids = validate_managed_fixes(text)
        except Exception as exc:
            errors.append(f"{provider_id}: managed Lego invalid: {type(exc).__name__}: {exc}")
            continue

        missing = sorted(UNIVERSAL_CORE_IDS - set(fix_ids))
        if missing:
            errors.append(f"{provider_id}: missing universal Core bricks={','.join(missing)}")

        specific = provider_patches.get(provider_id) if isinstance(provider_patches.get(provider_id), dict) else {}
        declared_provider_legos = [
            str(value) for value in specific.get("provider_lego_scripts") or []
            if str(value).strip()
        ]
        for patch_script in declared_provider_legos:
            try:
                module = _load_patch_module(patch_script, provider_id)
            except Exception as exc:
                errors.append(
                    f"{provider_id}: declared Provider Lego cannot load={patch_script}: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue
            fix_id = str(getattr(module, "MANAGED_FIX_ID", "") or "").strip().upper()
            optional = bool(getattr(module, "MANAGED_FIX_OPTIONAL", False))
            if not fix_id:
                errors.append(f"{provider_id}: declared Provider Lego has no MANAGED_FIX_ID={patch_script}")
                continue
            if not optional and fix_id not in fix_ids:
                errors.append(
                    f"{provider_id}: declared Provider Lego missing from published bytes="
                    f"{fix_id} script={patch_script}"
                )

        boundary = text.index(CORE_BOUNDARY)
        for fix_id in fix_ids:
            start_marker = begin_marker(fix_id)
            close_marker = end_marker(fix_id)
            if text.count(start_marker) != 1 or text.count(close_marker) != 1:
                errors.append(f"{provider_id}: non-canonical STARTFIX/CLOSEFIX ownership={fix_id}")
                continue
            span = owned_span(text, fix_id)
            if span is None:
                errors.append(f"{provider_id}: missing owned span={fix_id}")
                continue
            if fix_id.startswith("CORE.") and span[0] <= boundary:
                errors.append(f"{provider_id}: Core brick outside managed tail={fix_id}")
            if fix_id.startswith("PROVIDER.") and span[1] > boundary:
                errors.append(f"{provider_id}: Provider brick leaked into Core tail={fix_id}")

        if MEDIA_TYPE_REVISION not in text:
            errors.append(
                f"{provider_id}: media-type runtime revision mismatch expected={MEDIA_TYPE_REVISION}"
            )
        if LAUNCH_EVENT_GATE not in text:
            errors.append(f"{provider_id}: launch event gate missing")
        if POSITIVE_OUTPUT_GATE not in text:
            errors.append(f"{provider_id}: positive-output gate missing")

    expected = len([
        row for row in manifest.get("scrapers") or []
        if (
            isinstance(row, dict)
            and str(row.get("id") or "").strip()
            and str(row.get("filename") or "").strip().startswith("providers/")
        )
    ])
    if checked + quarantined != expected:
        errors.append(f"portfolio incomplete: checked={checked} quarantined={quarantined} expected={expected}")

    if errors:
        for error in errors:
            print("FIELD_PUBLISHED_PROVIDER_LEGO_ERROR " + error)
        raise AssertionError(f"published provider Lego contract errors={len(errors)}")

    print(
        "FIELD_PUBLISHED_PROVIDER_LEGO "
        f"providers={checked} quarantined={quarantined} "
        f"universal_bricks={len(UNIVERSAL_CORE_IDS)} media_type={MEDIA_TYPE_REVISION} launch_gate=true"
    )
    print("published provider Lego contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
