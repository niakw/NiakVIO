#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Reapply durable overrides to providers already published by this repository.

A new override must affect both newly discovered candidates and the exact JS
artifacts already referenced by manifests. Changed provider files are validated,
content-addressed again, and every manifest/provenance reference is updated
atomically.

Superseded bundles are deliberately not deleted here. The authoritative prune
step owns deletion after it has collected references from every published
manifest, LKG state and provenance record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "manifest.json"
SECONDARY = (ROOT / "vf" / "manifest.json", ROOT / "vostfr" / "manifest.json")
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def bump_provider_version(value: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or "").strip())
    if not match:
        return "1.0.1"
    major, minor, patch = (int(part) for part in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("scrapers"), list):
        raise ValueError(f"invalid manifest structure: {path.relative_to(ROOT)}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_manifest(path: Path, value: dict[str, Any]) -> None:
    write_json(path, value)


def validate_artifact(data: bytes) -> None:
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    try:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(temporary)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            detail = "\n".join(v.strip() for v in (result.stdout, result.stderr) if v.strip())
            raise ValueError(f"patched published provider rejected:\n{detail or 'no diagnostic'}")
    finally:
        temporary.unlink(missing_ok=True)


def published_name(provider_id: str, old_path: Path, digest: str, changed: bool) -> str:
    # Keep the artifact's source/lineage token stable when a local override is
    # reapplied. Provenance records the local patch separately; rewriting the
    # source token to generic ``nuvio`` erases meaningful identities such as
    # ``nuvio-tv-global`` and makes platform promotion metadata brittle.
    parts = old_path.stem.split("--")
    source = parts[-2] if len(parts) >= 3 else "nuvio"
    return f"{safe_fragment(provider_id.casefold())}--{safe_fragment(source)}--{digest[:16]}.js"


def merge_patch_records(existing: Any, records: list[dict[str, Any]]) -> list[Any]:
    """Preserve historical patch provenance while recording newly applied hooks."""
    merged = list(existing) if isinstance(existing, list) else []
    for record in records:
        if record not in merged:
            merged.append(record)
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    primary = load_manifest(PRIMARY)
    if primary is None:
        raise ValueError("manifest.json is missing")

    provenance: dict[str, Any] | None = None
    provenance_rows: dict[str, Any] = {}
    if PROVENANCE.exists():
        loaded = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("providers"), dict):
            raise ValueError("invalid PROVENANCE.json structure")
        provenance = loaded
        provenance_rows = loaded["providers"]

    updates: dict[str, tuple[str, str]] = {}
    outputs: dict[str, bytes] = {}
    old_paths: set[str] = set()
    provenance_updates: dict[str, dict[str, Any]] = {}
    applied_count = 0

    for entry in primary["scrapers"]:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        relative = str(entry.get("filename") or "").strip()
        if not provider_id or not relative.startswith("providers/"):
            continue
        path = (ROOT / relative).resolve()
        if PROVIDERS.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"missing or unsafe published provider: {relative}")

        original = path.read_bytes()
        patched, records = apply_overrides(provider_id, original, phase="discovery")
        changed = patched != original
        if changed:
            validate_artifact(patched)
            applied_count += 1
        digest = hashlib.sha256(patched).hexdigest()
        new_relative = f"providers/{published_name(provider_id, path, digest, changed)}"
        updates[provider_id] = (relative, new_relative)
        outputs[new_relative] = patched
        old_paths.add(relative)
        entry["filename"] = new_relative
        if relative != new_relative:
            entry["version"] = bump_provider_version(str(entry.get("version") or "1.0.0"))
        provenance_updates[provider_id] = {
            "old": relative,
            "new": new_relative,
            "sha256": digest,
            "records": records,
        }

    secondary_payloads: list[tuple[Path, dict[str, Any]]] = []
    for path in SECONDARY:
        payload = load_manifest(path)
        if payload is None:
            continue
        for entry in payload["scrapers"]:
            if not isinstance(entry, dict):
                continue
            provider_id = str(entry.get("id") or "").strip().casefold()
            if provider_id not in updates:
                continue
            _old, new = updates[provider_id]
            entry["filename"] = "../" + new
            primary_entry = next((row for row in primary["scrapers"] if isinstance(row, dict) and str(row.get("id") or "").strip().casefold() == provider_id), None)
            if isinstance(primary_entry, dict) and primary_entry.get("version"):
                entry["version"] = primary_entry["version"]
        secondary_payloads.append((path, payload))

    if provenance is not None:
        for provider_id, update in provenance_updates.items():
            row = provenance_rows.get(provider_id)
            if not isinstance(row, dict):
                continue
            row["published_filename"] = update["new"]
            row["sha256"] = update["sha256"]
            if "patched_sha256" in row or update["records"]:
                row["patched_sha256"] = update["sha256"]
            if update["records"]:
                row["local_patches"] = merge_patch_records(row.get("local_patches"), update["records"])

    stale = False
    for new_relative, data in outputs.items():
        destination = ROOT / new_relative
        if not destination.exists() or destination.read_bytes() != data:
            stale = True
    for entry in primary["scrapers"]:
        if isinstance(entry, dict):
            provider_id = str(entry.get("id") or "").strip().casefold()
            if provider_id in updates and entry.get("filename") != updates[provider_id][1]:
                stale = True

    if args.check:
        if json.loads(PRIMARY.read_text(encoding="utf-8")) != primary:
            stale = True
        for path, payload in secondary_payloads:
            if json.loads(path.read_text(encoding="utf-8")) != payload:
                stale = True
        if provenance is not None and json.loads(PROVENANCE.read_text(encoding="utf-8")) != provenance:
            stale = True
        if stale:
            print("published provider overrides or manifest/provenance references are stale")
            return 1
        print("published provider overrides are current")
        return 0

    for new_relative, data in outputs.items():
        destination = ROOT / new_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or destination.read_bytes() != data:
            destination.write_bytes(data)
    write_manifest(PRIMARY, primary)
    for path, payload in secondary_payloads:
        write_manifest(path, payload)
    if provenance is not None:
        write_json(PROVENANCE, provenance)

    referenced = {new for _old, new in updates.values()}
    deferred = sum(
        1
        for old_relative in old_paths
        if old_relative not in referenced and (ROOT / old_relative).is_file()
    )

    changed_refs = sum(1 for old, new in updates.values() if old != new)
    provenance_refs = sum(
        1 for update in provenance_updates.values() if update["old"] != update["new"]
    ) if provenance is not None else 0
    print(
        f"published overrides reapplied: patched={applied_count}, "
        f"manifest_refs={changed_refs}, provenance_refs={provenance_refs}, "
        f"superseded_deferred_to_prune={deferred}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
