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
import base64
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides, load_overrides
from provider_engine_normalizer import (
    _host,
    _host_belongs,
    _provider_api_hosts,
    sanitize_provider_hooks,
    strip_foreign_provider_wrappers,
)

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "manifest.json"
SECONDARY = (ROOT / "vf" / "manifest.json", ROOT / "vostfr" / "manifest.json")
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"
OVERRIDES = ROOT / "provider-overrides.json"
ADAPTIVE_MARKER = "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V"
ADAPTIVE_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
ADAPTIVE_SCRIPT = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py"
ADAPTIVE_DOMAIN_BEGIN = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN */"
ADAPTIVE_DOMAIN_END = "/* NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:END */"
ADAPTIVE_DOMAIN_SCRIPT = ROOT / "scripts" / "provider_patches" / "adaptive_domain_recovery.py"
AUDIT_QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"
AUDIT_QUARANTINE_MODE = "catalogue_audit_safety_quarantine"
AUDIT_QUARANTINE_BLOCKER = "catalogue_audit_playable_identity_contradiction"


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def bump_provider_version(value: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or "").strip())
    if not match:
        return "1.0.1"
    major, minor, patch = (int(part) for part in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def configured_authoritative_types(config: dict[str, Any], provider_id: str) -> list[str]:
    provider_key = str(provider_id or "").strip().casefold()
    patches = config.get("provider_patches") if isinstance(config, dict) else {}
    patch_row = (patches or {}).get(provider_key, {})
    published = [
        str(value)
        for value in ((patch_row.get("published_types") or []) if isinstance(patch_row, dict) else [])
        if str(value) in {"movie", "tv", "anime"}
    ]
    if published:
        return published
    capabilities = config.get("provider_capabilities") if isinstance(config, dict) else {}
    capability_row = (capabilities or {}).get(provider_key, {})
    return [
        str(value)
        for value in ((capability_row.get("catalogue_types") or []) if isinstance(capability_row, dict) else [])
        if str(value) in {"movie", "tv", "anime"}
    ]


def configured_manifest_overrides(config: dict[str, Any], provider_id: str) -> dict[str, Any]:
    patches = config.get("provider_patches") if isinstance(config, dict) else {}
    patch_row = (patches or {}).get(str(provider_id or "").strip().casefold(), {})
    overrides = patch_row.get("manifest_overrides") if isinstance(patch_row, dict) else {}
    if not isinstance(overrides, dict):
        return {}
    return {"enabled": False} if overrides.get("enabled") is False else {}


def strip_unproven_adaptive_language(data: bytes) -> tuple[bytes, int]:
    text = data.decode("utf-8", errors="strict")
    cursor = 0
    changed = 0
    parts: list[str] = []
    while True:
        start = text.find(ADAPTIVE_MARKER, cursor)
        if start < 0:
            parts.append(text[cursor:])
            break
        parts.append(text[cursor:start])
        call = text.find(ADAPTIVE_CALL, start)
        end = text.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated adaptive runtime recovery wrapper")
        segment = text[start : end + 2]
        cleaned = segment.replace('language:"fr",headers:', 'headers:')
        if cleaned != segment:
            changed += 1
        parts.append(cleaned)
        cursor = end + 2
    if not changed:
        return data, 0
    return "".join(parts).encode("utf-8"), changed


def reapply_adaptive_runtime_revision(data: bytes, provenance_row: dict[str, Any] | None) -> tuple[bytes, list[dict[str, Any]]]:
    if ADAPTIVE_MARKER.encode("utf-8") not in data or not isinstance(provenance_row, dict):
        return data, []
    accepted = [
        record for record in (provenance_row.get("local_patches") or [])
        if isinstance(record, dict)
        and record.get("type") == "patch_profile"
        and record.get("profile") == "adaptive_runtime_recovery"
        and record.get("phase") == "runtime"
        and isinstance(record.get("options"), dict)
    ]
    if not accepted:
        return data, []
    options = dict(accepted[-1]["options"])
    spec = importlib.util.spec_from_file_location("nuvio_reapply_adaptive_runtime", ADAPTIVE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adaptive runtime patcher: {ADAPTIVE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    patched = module.apply(data.decode("utf-8", errors="strict"), options=options).encode("utf-8")
    if patched == data:
        return data, []
    return patched, [{
        "type": "migration",
        "name": "adaptive_runtime_implementation_revision",
        "phase": "runtime",
        "profile": "adaptive_runtime_recovery",
        "runtime_revision": "generic-core-v2",
    }]


def reapply_adaptive_domain_revision(data: bytes) -> tuple[bytes, list[dict[str, Any]]]:
    text = data.decode("utf-8", errors="strict")
    start = text.find(ADAPTIVE_DOMAIN_BEGIN)
    if start < 0:
        return data, []
    end = text.find(ADAPTIVE_DOMAIN_END, start)
    if end < 0:
        raise ValueError("unterminated adaptive domain recovery wrapper")
    segment = text[start : end + len(ADAPTIVE_DOMAIN_END)]
    groups = None
    for encoded in re.findall(r'"([A-Za-z0-9+/=]{16,})"', segment):
        try:
            decoded = json.loads(base64.b64decode(encoded).decode("utf-8"))
        except Exception:
            continue
        candidate = decoded if isinstance(decoded, list) else decoded.get("groups") if isinstance(decoded, dict) else None
        if isinstance(candidate, list) and all(isinstance(row, dict) for row in candidate):
            groups = candidate
    if not groups:
        return data, []
    spec = importlib.util.spec_from_file_location("nuvio_reapply_adaptive_domain", ADAPTIVE_DOMAIN_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adaptive domain patcher: {ADAPTIVE_DOMAIN_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    patched = module.apply(text, options={"groups": groups}).encode("utf-8")
    if patched == data:
        return data, []
    return patched, [{
        "type": "migration",
        "name": "adaptive_domain_implementation_revision",
        "phase": "runtime",
        "profile": "adaptive_domain_recovery",
        "runtime_revision": str(getattr(module, "IMPLEMENTATION_REVISION", "current")),
    }]


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


def sanitize_capability_origins(config: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Drop API origins owned by another provider from generated capability metadata."""
    patches = config.get("provider_patches") if isinstance(config.get("provider_patches"), dict) else {}
    api_hosts = _provider_api_hosts(patches)
    capabilities = config.get("provider_capabilities") if isinstance(config.get("provider_capabilities"), dict) else {}
    removed = 0
    for provider_id, row in capabilities.items():
        if not isinstance(row, dict) or not isinstance(row.get("observed_origins"), list):
            continue
        kept: list[Any] = []
        for value in row["observed_origins"]:
            host = _host(value)
            foreign = False
            if host:
                for owner, hosts in api_hosts.items():
                    if owner == str(provider_id).casefold():
                        continue
                    if any(_host_belongs(host, owner_host) for owner_host in hosts):
                        foreign = True
                        break
            if foreign:
                removed += 1
            else:
                kept.append(value)
        row["observed_origins"] = kept
    meta = config.setdefault("provider_engine_normalization", {})
    if isinstance(meta, dict):
        meta["removed_cross_provider_capability_origins"] = removed
    return config, removed


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
    parts = old_path.stem.split("--")
    source = parts[-2] if len(parts) >= 3 else "nuvio"
    return f"{safe_fragment(provider_id.casefold())}--{safe_fragment(source)}--{digest[:16]}.js"


def merge_patch_records(existing: Any, records: list[dict[str, Any]]) -> list[Any]:
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

    override_config, removed_hooks = sanitize_provider_hooks(load_overrides(), ROOT)
    override_config, removed_origins = sanitize_capability_origins(override_config)
    if not args.check:
        write_json(OVERRIDES, override_config)

    removed_wrappers_total = 0
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

        authoritative_types = configured_authoritative_types(override_config, provider_id)
        types_changed = bool(authoritative_types and entry.get("supportedTypes") != authoritative_types)
        if types_changed:
            entry["supportedTypes"] = authoritative_types
        manifest_overrides = configured_manifest_overrides(override_config, provider_id)
        manifest_changed = any(entry.get(key) != value for key, value in manifest_overrides.items())
        if manifest_overrides:
            entry.update(manifest_overrides)

        original = path.read_bytes()
        provider_provenance = provenance_rows.get(provider_id) if provenance_rows else None
        audit_terminal_quarantine = (
            AUDIT_QUARANTINE_MARKER.encode("utf-8") in original
        )
        if audit_terminal_quarantine:
            patched = original
            records = []
        else:
            isolated_text, removed_wrappers = strip_foreign_provider_wrappers(
                original.decode("utf-8", errors="strict"), provider_id, override_config
            )
            removed_wrappers_total += len(removed_wrappers)
            isolated = isolated_text.encode("utf-8")
            migrated, adaptive_language_repairs = strip_unproven_adaptive_language(isolated)
            migrated, domain_revision_records = reapply_adaptive_domain_revision(migrated)
            patched, records = apply_overrides(provider_id, migrated, phase="discovery")
            if removed_wrappers:
                records = [{
                    "type": "migration",
                    "name": "cross_provider_wrapper_isolation",
                    "count": len(removed_wrappers),
                    "phase": "discovery",
                    "scope": "provider_isolation",
                }] + list(records)
            if domain_revision_records:
                records = list(records) + domain_revision_records
            patched, runtime_revision_records = reapply_adaptive_runtime_revision(patched, provider_provenance)
            if runtime_revision_records:
                records = list(records) + runtime_revision_records
            if adaptive_language_repairs:
                records = [{
                    "type": "migration",
                    "name": "adaptive_language_integrity_v1",
                    "count": adaptive_language_repairs,
                    "phase": "discovery",
                    "scope": "language_integrity",
                }] + list(records)
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
        if relative != new_relative or types_changed or manifest_changed:
            entry["version"] = bump_provider_version(str(entry.get("version") or "1.0.0"))
        provenance_updates[provider_id] = {
            "old": relative,
            "new": new_relative,
            "sha256": digest,
            "records": records,
            "audit_terminal_quarantine": audit_terminal_quarantine,
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
                if isinstance(primary_entry.get("supportedTypes"), list):
                    entry["supportedTypes"] = list(primary_entry["supportedTypes"])
                for key, value in configured_manifest_overrides(override_config, provider_id).items():
                    entry[key] = value
        secondary_payloads.append((path, payload))

    if provenance is not None:
        for provider_id, update in provenance_updates.items():
            row = provenance_rows.get(provider_id)
            if not isinstance(row, dict):
                continue
            row["published_filename"] = update["new"]
            row["sha256"] = update["sha256"]
            if update.get("audit_terminal_quarantine") or "patched_sha256" in row or update["records"]:
                row["patched_sha256"] = update["sha256"]
            if update["records"]:
                row["local_patches"] = merge_patch_records(row.get("local_patches"), update["records"])
            manifest_overrides = configured_manifest_overrides(override_config, provider_id)
            if update.get("audit_terminal_quarantine"):
                row["activation_eligible"] = False
                row["strict_activation_eligible"] = False
                row["strict_grace_eligible"] = False
                row["historical_quality_grace_eligible"] = False
                row["runtime_evidence_eligible"] = False
                row["activation_mode"] = AUDIT_QUARANTINE_MODE
                blockers = [
                    str(value) for value in (row.get("activation_blockers") or [])
                    if str(value) and str(value) not in {AUDIT_QUARANTINE_BLOCKER, "configured_safety_quarantine"}
                ]
                row["activation_blockers"] = blockers + [AUDIT_QUARANTINE_BLOCKER]
            elif manifest_overrides.get("enabled") is False:
                row["activation_eligible"] = False
                row["strict_activation_eligible"] = False
                row["strict_grace_eligible"] = False
                row["historical_quality_grace_eligible"] = False
                row["runtime_evidence_eligible"] = False
                row["activation_mode"] = "configured_safety_quarantine"
                blockers = [
                    str(value) for value in (row.get("activation_blockers") or [])
                    if str(value) and str(value) != "configured_safety_quarantine"
                ]
                row["activation_blockers"] = blockers + ["configured_safety_quarantine"]

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
        if stale or removed_hooks or removed_origins or removed_wrappers_total:
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
        f"superseded_deferred_to_prune={deferred}, isolated_hooks={len(removed_hooks)}, "
        f"isolated_wrappers={removed_wrappers_total}, isolated_origins={removed_origins}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
