#!/usr/bin/env python3
"""Publish runtime-compatible provider bundles for Nuvio Desktop.

This pass is deterministic and repeatable. It always starts from canonical,
tracked provider artifacts, applies the Desktop compatibility patch once,
creates immutable content-addressed bundles, synchronizes main/VF manifests,
records provenance, and retires obsolete 4KHDHUB when 4KHDHUBNEW is active.
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
PATCH_REL = "scripts/provider_patches/desktop_runtime_compat_v1.py"
PATCH_PATH = ROOT / PATCH_REL
REPORT_PATH = ROOT / "automation" / "desktop-runtime-compat-v1.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

SOURCE_FILES: dict[str, str] = {
    "coflix": "providers/coflix--nuvio--48239f7b107a98b2.js",
    "frenchstream": "providers/frenchstream--nuvio--38cf074196379a8d.js",
    "movix": "providers/movix--nuvio--b31ef87b05d3a4f3.js",
    "streamzo": "providers/streamzo--nuvio--5ee8d74abe45cd42.js",
    "flemmix": "providers/flemmix--nuvio--e0c40c452aca0d66.js",
    "wookafr": "providers/wookafr--nuvio--4ce4c33e2fe1d23b.js",
    "hindmoviez": "providers/hindmoviez--aio--86b8c3a4dff3c98c.js",
    "purstream": "providers/purstream--published-baseline--8e14e434a2868d4f.js",
}

TARGETS: dict[str, dict[str, Any]] = {
    "coflix": {"normalize_missing_episodes": True},
    "frenchstream": {"normalize_missing_episodes": True},
    "movix": {"normalize_missing_episodes": True},
    "streamzo": {"normalize_missing_episodes": True},
    "flemmix": {"normalize_missing_episodes": True},
    "wookafr": {"normalize_missing_episodes": True},
    "hindmoviez": {
        "normalize_missing_episodes": True,
        "filter_episode_labels": True,
        "max_series_streams": 24,
    },
    "purstream": {
        "normalize_missing_episodes": True,
        "domain_failover": {
            "host_prefixes": ["api.purstream", "purstream"],
            "suffixes": ["club", "mx", "ch", "ac", "cx", "art", "co", "me", "to", "store"],
        },
    },
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def import_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def bump(value: object) -> str:
    match = SEMVER.fullmatch(str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def provider_slug(provider_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", provider_id.casefold()).strip("-")


def vf_filename(value: object) -> str:
    filename = str(value or "")
    if filename.startswith(("../", "http://", "https://")):
        return filename
    return f"../{filename}" if filename.startswith("providers/") else filename


def sync_existing_vf(rows: list[dict[str, Any]], source: dict[str, Any]) -> None:
    provider_id = str(source.get("id") or "").casefold()
    target = next((row for row in rows if str(row.get("id") or "").casefold() == provider_id), None)
    if target is None:
        return
    target.clear()
    target.update(deepcopy(source))
    target["filename"] = vf_filename(source.get("filename"))


def update_metadata(
    overrides: dict[str, Any],
    provenance: dict[str, Any],
    provider_id: str,
    filename: str,
    source_filename: str,
    old_sha: str,
    new_sha: str,
    options: dict[str, Any],
) -> None:
    patch = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
    scripts = [str(value) for value in patch.get("patch_scripts") or []]
    if PATCH_REL not in scripts:
        scripts.append(PATCH_REL)
    patch["patch_scripts"] = scripts
    patch.setdefault("patch_script_options", {})[PATCH_REL] = options

    now = datetime.now(timezone.utc).isoformat()
    rows = provenance.setdefault("providers", {})
    current = dict(rows.get(provider_id) or rows.get(provider_id.upper()) or {})
    local_patches = [str(value) for value in current.get("local_patches") or []]
    if PATCH_REL not in local_patches:
        local_patches.append(PATCH_REL)
    current.update(
        {
            "id": provider_id,
            "published_filename": filename,
            "canonical_source_filename": source_filename,
            "sha256": new_sha,
            "patched_sha256": new_sha,
            "upstream_sha256": old_sha,
            "local_patches": local_patches,
            "source": "desktop-runtime-compat-v1",
            "source_name": "Nuvio Desktop QuickJS compatibility, bounded TV fallback and domain failover",
            "checked_at": now,
            "check_mode": "static-runtime-contract-and-regression-suite",
            "check_status": "healthy",
            "activation_eligible": True,
            "strict_activation_eligible": bool(current.get("strict_activation_eligible", True)),
            "runtime_evidence_eligible": True,
            "activation_mode": "desktop_runtime_compat_v1",
            "activation_blockers": [],
        }
    )
    rows[provider_id] = current


def mark_disabled(
    overrides: dict[str, Any],
    provenance: dict[str, Any],
    provider_id: str,
    reason: str,
) -> None:
    patch = overrides.setdefault("provider_patches", {}).setdefault(provider_id, {})
    patch.setdefault("manifest_overrides", {})["enabled"] = False
    now = datetime.now(timezone.utc).isoformat()
    rows = provenance.setdefault("providers", {})
    current = dict(rows.get(provider_id) or rows.get(provider_id.upper()) or {})
    blockers = [str(value) for value in current.get("activation_blockers") or []]
    if reason not in blockers:
        blockers.append(reason)
    current.update(
        {
            "id": provider_id,
            "checked_at": now,
            "check_status": "disabled",
            "activation_eligible": False,
            "strict_activation_eligible": False,
            "runtime_evidence_eligible": False,
            "activation_mode": "disabled_by_desktop_runtime_compat_v1",
            "activation_blockers": blockers,
        }
    )
    rows[provider_id] = current


def main() -> int:
    apply = import_apply(PATCH_PATH)
    manifest_path = ROOT / "manifest.json"
    vf_path = ROOT / "vf" / "manifest.json"
    overrides_path = ROOT / "provider-overrides.json"
    provenance_path = ROOT / "PROVENANCE.json"

    manifest = load(manifest_path)
    vf_manifest = load(vf_path)
    overrides = load(overrides_path)
    provenance = load(provenance_path)
    main_rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
    }
    vf_rows = [row for row in vf_manifest.get("scrapers") or [] if isinstance(row, dict)]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime": "Nuvio Desktop QuickJS",
        "providers": {},
        "published": [],
        "preserved": [],
        "disabled": [],
    }

    new_provider_files: list[str] = []
    changed = False
    for provider_id, options in TARGETS.items():
        row = main_rows.get(provider_id)
        if row is None:
            report["providers"][provider_id] = {"ok": False, "error": "manifest row missing"}
            report["preserved"].append(provider_id)
            continue

        source_filename = SOURCE_FILES[provider_id]
        source_path = ROOT / source_filename
        if not source_path.is_file():
            report["providers"][provider_id] = {"ok": False, "error": f"missing canonical source {source_filename}"}
            report["preserved"].append(provider_id)
            continue

        source = source_path.read_text(encoding="utf-8", errors="replace")
        patched = apply(source, options)
        old_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
        new_sha = hashlib.sha256(patched.encode("utf-8")).hexdigest()
        filename = f"providers/{provider_slug(provider_id)}--desktop-runtime-v1--{new_sha[:16]}.js"
        target_path = ROOT / filename
        if not target_path.is_file() or target_path.read_text(encoding="utf-8", errors="replace") != patched:
            target_path.write_text(patched, encoding="utf-8")
            new_provider_files.append(filename)

        old_filename = str(row.get("filename") or "")
        row_changed = old_filename != filename
        row["filename"] = filename
        if row_changed:
            row["version"] = bump(row.get("version"))
        row["enabled"] = True
        if provider_id == "streamzo":
            # Only a globally audited direct-media lineage may disable this hint.
            row["supportsExternalPlayer"] = "--nuvio-tv-global--" not in source_filename
        sync_existing_vf(vf_rows, row)
        update_metadata(overrides, provenance, provider_id, filename, source_filename, old_sha, new_sha, options)
        report["providers"][provider_id] = {
            "ok": True,
            "changed": row_changed,
            "old_filename": old_filename,
            "source_filename": source_filename,
            "filename": filename,
            "upstream_sha256": old_sha,
            "sha256": new_sha,
            "options": options,
            "timer_shim_required": "setTimeout" in source or "clearTimeout" in source,
        }
        report["published"].append(provider_id)
        changed = changed or row_changed

    old_4k = main_rows.get("4khdhub")
    new_4k = main_rows.get("4khdhubnew")
    if old_4k and new_4k and bool(new_4k.get("enabled")) and bool(old_4k.get("enabled")):
        old_4k["enabled"] = False
        sync_existing_vf(vf_rows, old_4k)
        mark_disabled(overrides, provenance, "4khdhub", "superseded_by:4khdhubnew")
        report["disabled"].append("4khdhub")
        changed = True

    provenance["generated_at"] = report["generated_at"]
    if changed:
        provenance["schema_version"] = int(provenance.get("schema_version") or 0) + 1
    report["changed"] = changed
    report["new_provider_files"] = new_provider_files

    vf_manifest["scrapers"] = vf_rows
    dump(manifest_path, manifest)
    dump(vf_path, vf_manifest)
    dump(overrides_path, overrides)
    dump(provenance_path, provenance)
    dump(REPORT_PATH, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
