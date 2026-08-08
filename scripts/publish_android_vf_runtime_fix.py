#!/usr/bin/env python3
"""Publish the evidence-backed Android VF runtime compatibility state.

The current Nuvio Mobile plugin runtime invokes getStreams positionally and sends
plugin URLs to the native player. Providers without a currently proven direct
movie payload are therefore disabled on Android only; their desktop/global
activation is preserved. Purstream additionally receives the mobile-safe
runtime failover wrapper proven by the targeted Android diagnostic.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "automation" / "mobile-vf-runtime.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
PROVENANCE = ROOT / "PROVENANCE.json"
PATCH_REL = "scripts/provider_patches/desktop_runtime_compat_v1.py"
PATCH = ROOT / PATCH_REL
# The old baseline was legitimately pruned. Rebuild from the current published
# Purstream lineage, first removing its rev-3 compatibility wrapper so rev-4
# replaces it instead of stacking on top of it.
PURSTREAM_SOURCE = ROOT / "providers" / "purstream--nuvio--56f5640cdb9dd4f6.js"
RUNTIME_MARKER = "/* NUVIO_DESKTOP_RUNTIME_COMPAT_V1:"
BRIDGE_MARKER = "/* NUVIO_PURSTREAM_BRIDGE_V1 */"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in document.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def bump(value: object) -> str:
    match = SEMVER.fullmatch(str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def import_apply():
    spec = importlib.util.spec_from_file_location("nuvio_runtime_compat", PATCH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {PATCH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def split_purstream_runtime_lineage(source: str) -> tuple[str, str]:
    """Return provider core and bridge, dropping any existing compat wrapper."""
    if RUNTIME_MARKER in source:
        prefix, remainder = source.split(RUNTIME_MARKER, 1)
        if BRIDGE_MARKER not in remainder:
            raise RuntimeError("cannot safely locate the end of the existing Purstream runtime wrapper")
        _old_runtime, bridge_tail = remainder.split(BRIDGE_MARKER, 1)
        return prefix.rstrip() + "\n", BRIDGE_MARKER + bridge_tail
    if BRIDGE_MARKER in source:
        prefix, bridge_tail = source.split(BRIDGE_MARKER, 1)
        return prefix.rstrip() + "\n", BRIDGE_MARKER + bridge_tail
    return source.rstrip() + "\n", ""


def platform_list(row: dict[str, Any]) -> list[str]:
    output: list[str] = []
    for value in row.get("disabledPlatforms") or []:
        item = str(value).strip().casefold()
        if item and item not in output:
            output.append(item)
    return output


def set_android(row: dict[str, Any], disabled: bool) -> bool:
    current = platform_list(row)
    updated = [value for value in current if value != "android"]
    if disabled:
        updated.append("android")
    if current == updated and row.get("disabledPlatforms") is not None:
        return False
    row["disabledPlatforms"] = updated
    return True


def sync_vf(main_row: dict[str, Any], vf_row: dict[str, Any] | None) -> None:
    if vf_row is None:
        return
    filename = str(main_row.get("filename") or "")
    vf_row.clear()
    vf_row.update(deepcopy(main_row))
    if filename.startswith("providers/"):
        vf_row["filename"] = "../" + filename


def update_override_platform(overrides: dict[str, Any], provider_id: str, disabled: bool) -> None:
    patch = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
    manifest_overrides = patch.setdefault("manifest_overrides", {})
    values = []
    for value in manifest_overrides.get("disabledPlatforms") or []:
        item = str(value).strip().casefold()
        if item and item != "android" and item not in values:
            values.append(item)
    if disabled:
        values.append("android")
    manifest_overrides["disabledPlatforms"] = values


def publish_purstream(main_row: dict[str, Any], vf_row: dict[str, Any] | None, overrides: dict[str, Any], provenance: dict[str, Any]) -> str:
    if not PURSTREAM_SOURCE.is_file():
        raise RuntimeError(f"missing current Purstream source: {PURSTREAM_SOURCE.relative_to(ROOT)}")
    patch = overrides.get("provider_patches", {}).get("purstream", {})
    options = dict((patch.get("patch_script_options") or {}).get(PATCH_REL) or {})
    if not options.get("domain_failover"):
        raise RuntimeError("Purstream mobile-safe domain failover options are missing")

    source = PURSTREAM_SOURCE.read_text(encoding="utf-8", errors="replace")
    core, bridge = split_purstream_runtime_lineage(source)
    patched_core = import_apply()(core, options)
    patched = patched_core.rstrip() + ("\n" + bridge.lstrip() if bridge else "\n")
    if patched.count("NUVIO_DESKTOP_RUNTIME_COMPAT_V1:") != 1:
        raise RuntimeError("Purstream runtime bundle must contain exactly one compatibility wrapper")
    if '"patchRevision":4' not in patched or '"patchRevision":3' in patched:
        raise RuntimeError("Purstream runtime bundle did not replace revision 3 with revision 4")

    digest = hashlib.sha256(patched.encode("utf-8")).hexdigest()
    filename = f"providers/purstream--runtime-compat-v4--{digest[:16]}.js"
    target = ROOT / filename
    if not target.is_file() or target.read_text(encoding="utf-8", errors="replace") != patched:
        target.write_text(patched, encoding="utf-8")
    if str(main_row.get("filename") or "") != filename:
        main_row["filename"] = filename
        main_row["version"] = bump(main_row.get("version"))
    set_android(main_row, False)
    sync_vf(main_row, vf_row)

    now = datetime.now(timezone.utc).isoformat()
    provider_rows = provenance.setdefault("providers", {})
    current = dict(provider_rows.get("purstream") or provider_rows.get("PURSTREAM") or {})
    patches = list(current.get("local_patches") or [])
    # Remove stale records for the same compatibility layer before recording
    # the exact rev-4 options that produced this immutable artifact.
    patches = [
        item for item in patches
        if not (
            isinstance(item, dict)
            and (item.get("path") == PATCH_REL or item.get("profile") == "desktop_runtime_compat_v1")
        )
        and str(item) != PATCH_REL
    ]
    patches.append({"type": "patch_script", "path": PATCH_REL, "phase": "runtime", "options": options})
    current.update({
        "id": "purstream",
        "published_filename": filename,
        "sha256": digest,
        "patched_sha256": digest,
        "local_patches": patches,
        "checked_at": now,
        "check_mode": "android-targeted-runtime-contract",
        "check_status": "healthy",
        "activation_mode": "android_direct_movie_proof",
        "android_direct_movie_proof": True,
    })
    provider_rows["purstream"] = current
    return filename


def main() -> int:
    report = load(REPORT)
    if str(report.get("release") or "") != str(load(MAIN).get("version") or ""):
        raise SystemExit("Android diagnostic release does not match current manifest release")
    report_rows = {
        str(row.get("id") or "").casefold(): row
        for row in report.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    proven = {provider_id for provider_id, row in report_rows.items() if row.get("android_direct_movie_proof") is True}
    if "purstream" not in proven or "goated" not in proven:
        raise SystemExit(f"required Android direct-media proofs missing: proven={sorted(proven)}")

    main_doc = load(MAIN)
    vf_doc = load(VF)
    overrides = load(OVERRIDES)
    provenance = load(PROVENANCE)
    main_rows = rows(main_doc)
    vf_rows = rows(vf_doc)

    changed: list[str] = []
    for provider_id, evidence in sorted(report_rows.items()):
        main_row = main_rows.get(provider_id)
        if main_row is None:
            continue
        disabled = evidence.get("android_direct_movie_proof") is not True
        before = platform_list(main_row)
        set_android(main_row, disabled)
        update_override_platform(overrides, provider_id, disabled)
        sync_vf(main_row, vf_rows.get(provider_id))
        if before != platform_list(main_row):
            changed.append(provider_id)

    purstream_filename = publish_purstream(main_rows["purstream"], vf_rows.get("purstream"), overrides, provenance)
    if "purstream" not in changed:
        changed.append("purstream")

    now = datetime.now(timezone.utc).isoformat()
    provenance["generated_at"] = now
    provenance["schema_version"] = int(provenance.get("schema_version") or 0) + 1
    policy = {
        "schema_version": 1,
        "generated_at": now,
        "source_report": str(REPORT.relative_to(ROOT)),
        "release_before_bump": main_doc.get("version"),
        "android_direct_movie_proven": sorted(proven),
        "android_disabled_no_direct_movie_proof": sorted(set(report_rows) - proven),
        "purstream_runtime_bundle": purstream_filename,
        "changed_providers": sorted(set(changed)),
    }

    dump(MAIN, main_doc)
    dump(VF, vf_doc)
    dump(OVERRIDES, overrides)
    dump(PROVENANCE, provenance)
    dump(ROOT / "automation" / "mobile-vf-runtime-policy.json", policy)
    print(json.dumps(policy, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
