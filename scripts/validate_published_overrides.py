#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate stable overrides and accepted runtime profiles in published files."""
from __future__ import annotations

import json
from pathlib import Path
from override_text_utils import contains_literal
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.next.json"
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"
PROVIDER_LKG = ROOT / "provider-lkg.json"

# Runtime-generated strategies are deliberately not static patch_profiles in
# provider-overrides.json. They are created from live deep-health evidence and
# accepted only after a strict before/after retest. Their provenance still has
# to be verifiable in the final published artifact, so keep an explicit marker
# registry here rather than treating every unknown profile as valid.
GENERATED_RUNTIME_PROFILE_MARKERS = {
    "adaptive_runtime_recovery": "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4",
}


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


def add_provider_reference(protected: set[Path], value: object, base: Path = ROOT) -> None:
    """Protect a provider path still referenced by any authoritative state."""
    if not isinstance(value, str) or not value.strip():
        return
    target = (base / value).resolve()
    try:
        target.relative_to(PROVIDERS.resolve())
    except ValueError:
        return
    protected.add(target)


def transaction_protected_provider_paths(provenance: dict[str, Any]) -> set[Path]:
    """Return the union of provider bundles that may still be live.

    Validation runs before the two-phase manifest transaction is committed. A
    bundle can therefore be absent from ``manifest.next.json`` and still be a
    live dependency of the currently published manifest, a language projection,
    LKG state or provenance. Destructive stale-alias cleanup must never delete
    those files; ``prune_unreferenced_providers.py`` owns final garbage
    collection once the transaction's authoritative references have converged.
    """
    protected: set[Path] = set()
    manifest_paths: list[Path] = []
    for path in (MANIFEST, ROOT / "manifest.json"):
        if path.is_file() and path not in manifest_paths:
            manifest_paths.append(path)
    for path in sorted(ROOT.glob("*/manifest.json")):
        if path.is_file() and path not in manifest_paths:
            manifest_paths.append(path)

    for path in manifest_paths:
        payload = load(path, {})
        for entry in payload.get("scrapers", []):
            if isinstance(entry, dict):
                add_provider_reference(protected, entry.get("filename"), path.parent)

    lkg = load(PROVIDER_LKG, {})
    for record in (lkg.get("providers", {}) if isinstance(lkg, dict) else {}).values():
        if isinstance(record, dict):
            add_provider_reference(protected, record.get("filename"))

    for record in (provenance.get("providers", {}) if isinstance(provenance, dict) else {}).values():
        if not isinstance(record, dict):
            continue
        add_provider_reference(protected, record.get("published_filename"))
        add_provider_reference(protected, record.get("canonical_source_filename"))
    return protected


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

    protected_paths = transaction_protected_provider_paths(provenance)
    errors: list[str] = []
    removed: list[str] = []
    normalized_provenance: list[str] = []
    provenance_changed = False
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
        provider_provenance = provenance_by_id.get(cid) or {}
        records = provider_provenance.get("local_patches") or []
        replacements = dict(global_replacements)
        replacements.update(cfg.get("replacements") or {})
        replacements.update(cfg.get("route_replacements") or {})
        for old, new in replacements.items():
            old, new = str(old), str(new)
            if contains_literal(text, old):
                errors.append(f"{cid}: forbidden value remains in {target.relative_to(ROOT)}: {old}")
            applied = any(
                isinstance(record, dict)
                and record.get("type") == "replace"
                and str(record.get("from")) == old
                and int(record.get("count") or 0) > 0
                for record in records
            )
            if applied and not contains_literal(text, new):
                errors.append(f"{cid}: recorded replacement destination missing: {new}")

        required_values = [str(value) for value in cfg.get("required_values") or []]
        effective_records: list[Any] = []
        for record in records:
            if not isinstance(record, dict) or record.get("type") != "patch_profile":
                effective_records.append(record)
                continue
            profile_name = str(record.get("profile") or "")
            profile = profiles.get(profile_name)
            if isinstance(profile, dict):
                required_values.extend(str(value) for value in profile.get("required_values") or [])
                effective_records.append(record)
                continue

            generated_marker = GENERATED_RUNTIME_PROFILE_MARKERS.get(profile_name)
            if generated_marker and str(record.get("phase") or "") == "runtime":
                if generated_marker in text:
                    required_values.append(generated_marker)
                    effective_records.append(record)
                    continue

                preserved = (
                    str(provider_provenance.get("activation_mode") or "")
                    == "preserved_current_ci_uncertain"
                    and str(provider_provenance.get("preserved_reason") or "")
                    == "ci_uncertain_kept_last_published_artifact"
                )
                if preserved:
                    normalized_provenance.append(f"{cid}:{profile_name}")
                    discarded = provider_provenance.setdefault(
                        "discarded_stale_patch_records", []
                    )
                    audit = {
                        "type": "patch_profile",
                        "profile": profile_name,
                        "phase": "runtime",
                        "reason": "marker_absent_from_preserved_artifact",
                    }
                    if audit not in discarded:
                        discarded.append(audit)
                    provenance_changed = True
                    continue

                required_values.append(generated_marker)
                effective_records.append(record)
                continue

            errors.append(f"{cid}: provenance references unknown profile {profile_name}")
            effective_records.append(record)

        if effective_records != records:
            provider_provenance["local_patches"] = effective_records
            provenance_changed = True

        for required in dict.fromkeys(required_values):
            if bare_host_marker(required):
                continue
            if required not in text:
                errors.append(
                    f"{cid}: required value missing from {target.relative_to(ROOT)}: {required}"
                )

        if replacements:
            exact_prefix = f"{cid}--"
            exact_plain = f"{cid}.js"
            for candidate in PROVIDERS.glob("*.js"):
                candidate_name = candidate.name.casefold()
                if candidate_name != exact_plain and not candidate_name.startswith(exact_prefix):
                    continue
                resolved_candidate = candidate.resolve()
                if resolved_candidate == target or resolved_candidate in protected_paths:
                    continue
                candidate_text = candidate.read_text(encoding="utf-8", errors="ignore")
                if any(contains_literal(candidate_text, str(old)) for old in replacements):
                    candidate.unlink()
                    removed.append(candidate.relative_to(ROOT).as_posix())

    if errors:
        raise SystemExit("published override validation failed:\n- " + "\n- ".join(errors))
    if provenance_changed:
        PROVENANCE.write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    for item in normalized_provenance:
        print(f"discarded stale preserved runtime provenance: {item}")
    for item in removed:
        print(f"removed stale unpatched provider: {item}")
    print("published override validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
