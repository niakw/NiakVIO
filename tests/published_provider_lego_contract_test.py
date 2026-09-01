#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_patch_blocks import validate_managed_fixes  # noqa: E402

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

MEDIA_TYPE_REVISION = "tmdb-api-first-semantic-transport-split-v20-event-launch-nonzero-gate"
LAUNCH_EVENT = 'providerEvent="launch"'
LAUNCH_OUTPUT_GATE = 'providerEvent!=="launch"||!hasProviderOutput(value)'


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
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
            # Terminal quarantine deliberately replaces the whole runtime bundle
            # with an inert empty export after Core composition. It is therefore
            # the only published state exempt from the Core Lego tail contract.
            quarantined += 1
            continue

        checked += 1
        boundary_count = text.count(CORE_BOUNDARY)
        if boundary_count != 1:
            errors.append(
                f"{provider_id}: Core boundary count={boundary_count} expected=1"
            )
            continue

        try:
            fix_ids = validate_managed_fixes(text)
        except Exception as exc:
            errors.append(
                f"{provider_id}: managed Lego invalid: {type(exc).__name__}: {exc}"
            )
            continue

        missing = sorted(UNIVERSAL_CORE_IDS - set(fix_ids))
        if missing:
            errors.append(
                f"{provider_id}: missing universal Core bricks={','.join(missing)}"
            )

        boundary = text.index(CORE_BOUNDARY)
        before_core = text[:boundary]
        if "/* START NIAKVIO_FIX:CORE." in before_core:
            errors.append(f"{provider_id}: Core Lego leaked before canonical boundary")

        for fix_id in fix_ids:
            if not fix_id.startswith("CORE."):
                continue
            start = text.find(f"/* START NIAKVIO_FIX:{fix_id} */")
            end = text.find(f"/* END NIAKVIO_FIX:{fix_id} */")
            if start <= boundary or end <= start:
                errors.append(
                    f"{provider_id}: Core brick outside managed tail={fix_id}"
                )

        if MEDIA_TYPE_REVISION not in text:
            errors.append(f"{provider_id}: media-type runtime is not v20")
        if LAUNCH_EVENT not in text:
            errors.append(f"{provider_id}: launch event gate missing")
        if LAUNCH_OUTPUT_GATE not in text:
            errors.append(f"{provider_id}: launch/nonzero output short-circuit missing")

        if text.count("/* START NIAKVIO_FIX:") != len(fix_ids):
            errors.append(f"{provider_id}: START marker cardinality drift")
        if text.count("/* END NIAKVIO_FIX:") != len(fix_ids):
            errors.append(f"{provider_id}: END marker cardinality drift")

    expected = len([
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    ])
    if checked + quarantined != expected:
        errors.append(
            f"portfolio incomplete: checked={checked} quarantined={quarantined} expected={expected}"
        )

    if errors:
        for error in errors:
            print("FIELD_PUBLISHED_PROVIDER_LEGO_ERROR " + error)
        raise AssertionError(
            f"published provider Lego contract errors={len(errors)}"
        )

    print(
        "FIELD_PUBLISHED_PROVIDER_LEGO "
        f"providers={checked} quarantined={quarantined} "
        f"universal_bricks={len(UNIVERSAL_CORE_IDS)} media_type=v20 launch_gate=true"
    )
    print("published provider Lego contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
