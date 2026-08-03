#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate stable overrides and accepted runtime profiles in published files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.next.json"
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"


def canonical_id(value: str) -> str:
    return value.strip().casefold().replace("_", "-")


def load(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path.name} must contain an object")
    return value


def bare_host_marker(value: str) -> bool:
    """Return True for host-only routing metadata, not code markers/URLs."""
    value = str(value or "").strip().lower().rstrip(".")
    if not value or "://" in value or "/" in value or " " in value:
        return False
    labels = value.split(".")
    return len(labels) >= 2 and all(label and all(ch.isalnum() or ch == "-" for ch in label) for label in labels)


def provider_file_matches_id(path: Path, provider_id: str) -> bool:
    """Match one provider bundle exactly, never a longer provider-id prefix.

    For example, ``4khdhub`` must not match ``4khdhubnew--...js``.  The old
    prefix glob could delete another provider's freshly promoted bundle before
    that provider was validated.
    """
    name = path.name
    stem = name[:-3] if name.lower().endswith(".js") else name
    bundle_id = stem.split("--", 1)[0]
    return canonical_id(bundle_id) == canonical_id(provider_id)


def main() -> int:
    config = load(CONFIG, {})
    manifest = load(MANIFEST, {})
    provenance = load(PROVENANCE, {"providers": {}})
    patches = config.get("provider_patches") or {}
    profiles = config.get("patch_profiles") or {}
    global_replacements = config.get("domain_replacements") or {}
    if not isinstance(patches, dict):
        raise SystemExit("provider_patches must be an object")
    if not isinstance(profiles, dict):
        raise SystemExit("patch_profiles must be an object")

    referenced: dict[str, Path] = {}
    for entry in manifest.get("scrapers", []):
        if not isinstance(entry, dict):
            continue
        cid = canonical_id(str(entry.get("id") or ""))
        filename = entry.get("filename")
        if cid and isinstance(filename, str):
            referenced[cid] = (ROOT / filename).resolve()

    errors: list[str] = []
    removed: list[str] = []
    provenance_by_id = provenance.get("providers") or {}

    for cid, target in referenced.items():
        if not target.exists():
            errors.append(f"{cid}: final manifest provider file is missing")
            continue
        try:
            target.relative_to(PROVIDERS.resolve())
        except ValueError:
            errors.append(f"{cid}: published provider path escapes providers/: {target}")
            continue

        text = target.read_text(encoding="utf-8", errors="strict")
        cfg = patches.get(cid) if isinstance(patches.get(cid), dict) else {}
        replacements = dict(global_replacements)
        replacements.update(cfg.get("replacements") or {})
        replacements.update(cfg.get("route_replacements") or {})
        for old, new in replacements.items():
            old, new = str(old), str(new)
            if old in text:
                errors.append(f"{cid}: forbidden value remains in {target.relative_to(ROOT)}: {old}")
            # A destination is required only when this provider's provenance says
            # the corresponding replacement was actually applied.
            records = (provenance_by_id.get(cid) or {}).get("local_patches") or []
            applied = any(
                isinstance(record, dict)
                and record.get("type") == "replace"
                and str(record.get("from")) == old
                and int(record.get("count") or 0) > 0
                for record in records
            )
            if applied and new not in text:
                errors.append(f"{cid}: recorded replacement destination missing: {new}")

        required_values = [str(value) for value in cfg.get("required_values") or []]
        records = (provenance_by_id.get(cid) or {}).get("local_patches") or []
        for record in records:
            if not isinstance(record, dict) or record.get("type") != "patch_profile":
                continue
            profile_name = str(record.get("profile") or "")
            profile = profiles.get(profile_name)
            if not isinstance(profile, dict):
                errors.append(f"{cid}: provenance references unknown profile {profile_name}")
                continue
            required_values.extend(str(value) for value in profile.get("required_values") or [])
        for required in dict.fromkeys(required_values):
            # Bare domains written by older resolver revisions are routing
            # metadata. They are not guaranteed to be literals in provider code.
            if bare_host_marker(required):
                continue
            if required not in text:
                errors.append(
                    f"{cid}: required value missing from {target.relative_to(ROOT)}: {required}"
                )

        # Remove stale aliases/old hashes only when they retain a forbidden value
        # and are not the exact file selected by manifest.next.json.
        if replacements:
            for candidate in PROVIDERS.glob("*.js"):
                if not provider_file_matches_id(candidate, cid):
                    continue
                if candidate.resolve() == target:
                    continue
                candidate_text = candidate.read_text(encoding="utf-8", errors="ignore")
                if any(str(old) in candidate_text for old in replacements):
                    candidate.unlink()
                    removed.append(candidate.relative_to(ROOT).as_posix())

    if errors:
        raise SystemExit("published override validation failed:\n- " + "\n- ".join(errors))
    for item in removed:
        print(f"removed stale unpatched provider: {item}")
    print("published override validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
