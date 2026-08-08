#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "automation" / "mobile-vf-runtime.json"
POLICY = ROOT / "automation" / "mobile-vf-runtime-policy.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in document.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def android_disabled(row: dict[str, Any]) -> bool:
    return "android" in {str(value).casefold() for value in row.get("disabledPlatforms") or []}


def main() -> int:
    report = load(REPORT)
    policy = load(POLICY)
    main_doc = load(MAIN)
    vf_doc = load(VF)
    main_rows = rows(main_doc)
    vf_rows = rows(vf_doc)
    report_rows = {
        str(row.get("id") or "").casefold(): row
        for row in report.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }

    errors: list[str] = []
    if report.get("runtime_contract") != "Nuvio Mobile QuickJS positional getStreams + native direct-media playback":
        errors.append("diagnostic did not use the Nuvio Mobile runtime contract")
    proven = {provider_id for provider_id, row in report_rows.items() if row.get("android_direct_movie_proof") is True}
    if not {"purstream", "goated"}.issubset(proven):
        errors.append(f"required Android direct-media providers are not proven: {sorted(proven)}")

    for provider_id, evidence in sorted(report_rows.items()):
        main_row = main_rows.get(provider_id)
        if main_row is None:
            continue
        should_disable = evidence.get("android_direct_movie_proof") is not True
        if android_disabled(main_row) != should_disable:
            errors.append(f"{provider_id}: main Android platform state disagrees with direct-media proof")
        vf_row = vf_rows.get(provider_id)
        if vf_row is not None and android_disabled(vf_row) != should_disable:
            errors.append(f"{provider_id}: VF Android platform state disagrees with direct-media proof")
        if vf_row is not None and bool(vf_row.get("enabled")) != bool(main_row.get("enabled")):
            errors.append(f"{provider_id}: main/VF enabled mismatch")
        if evidence.get("supports_external_player") is True and not should_disable:
            # Current Nuvio Mobile drops the manifest external-player hint. Such
            # a provider may be allowed only when this diagnostic independently
            # proved that its returned URL is direct native-player media.
            if evidence.get("android_direct_movie_proof") is not True:
                errors.append(f"{provider_id}: external-player provider allowed on Android without direct-media proof")
        for fixture in evidence.get("fixtures") or []:
            names = set(fixture.get("invocation_names") or [])
            if names - {"positional_with_settings"}:
                errors.append(f"{provider_id}: non-Mobile invocation fallback observed: {sorted(names)}")

    purstream = main_rows.get("purstream")
    if not purstream:
        errors.append("purstream missing from main manifest")
    else:
        filename = str(purstream.get("filename") or "")
        path = ROOT / filename
        if "runtime-compat-v4" not in filename or not path.is_file():
            errors.append(f"purstream: mobile-safe runtime bundle missing ({filename})")
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            if '"patchRevision":4' not in text or "NUVIO_DESKTOP_RUNTIME_COMPAT_V1" not in text:
                errors.append("purstream: runtime compatibility revision 4 marker missing")

    if sorted(policy.get("android_direct_movie_proven") or []) != sorted(proven):
        errors.append("policy direct-media proof set disagrees with diagnostic")
    if str(main_doc.get("version") or "") != str(vf_doc.get("version") or ""):
        errors.append("main/VF release version mismatch")

    if errors:
        raise SystemExit("Android runtime policy validation failed:\n- " + "\n- ".join(errors))
    print(
        "Android runtime policy validated: "
        f"direct={','.join(sorted(proven))}; "
        f"android-disabled={','.join(sorted(set(report_rows) - proven))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
