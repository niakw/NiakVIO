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
from provider_purification import TERSER_VERSION, purify_bytes
from provider_security_hardening import assert_hardened, harden_bytes
from provider_engine_normalizer import (
    _host,
    _host_belongs,
    _provider_api_hosts,
    sanitize_provider_hooks,
    strip_foreign_provider_wrappers,
)
from provider_base_store import resolve_base

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "manifest.json"
SECONDARY = (ROOT / "vf" / "manifest.json", ROOT / "vostfr" / "manifest.json")
PROVENANCE = ROOT / "PROVENANCE.json"
PROVIDERS = ROOT / "providers"
OVERRIDES = ROOT / "provider-overrides.json"
ADAPTIVE_MARKER = "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V"
ADAPTIVE_MARKER_V5 = "/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5"
ADAPTIVE_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
ADAPTIVE_SCRIPT = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py"
ADAPTIVE_SCRIPT_V5 = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v5.py"
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
    if not isinstance(provenance_row, dict):
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

    current = accepted[-1]
    revision = int(current.get("revision") or 0)
    # A published V5 bundle must never be downgraded through the historical V4
    # migrator just because older provenance has no explicit revision field.
    if ADAPTIVE_MARKER_V5.encode("utf-8") in data:
        return data, []

    marker_present = (
        ADAPTIVE_MARKER_V5.encode("utf-8") in data
        if revision >= 5
        else ADAPTIVE_MARKER.encode("utf-8") in data
    )
    preserved_ci_uncertain = (
        str(provenance_row.get("activation_mode") or "") == "preserved_current_ci_uncertain"
        and str(provenance_row.get("preserved_reason") or "")
        == "ci_uncertain_kept_last_published_artifact"
    )
    if not marker_present and preserved_ci_uncertain:
        return data, []

    options = dict(current["options"])
    script = ADAPTIVE_SCRIPT_V5 if revision >= 5 else ADAPTIVE_SCRIPT
    module_name = "nuvio_reapply_adaptive_runtime_v5" if revision >= 5 else "nuvio_reapply_adaptive_runtime"
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adaptive runtime patcher: {script}")
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
        "runtime_revision": "generic-core-v3" if revision >= 5 else "generic-core-v2",
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
        if isinstance(decoded, list):
            candidate = decoded
        elif isinstance(decoded, dict):
            candidate = decoded.get("groups")
        else:
            candidate = None
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


def _origin_belongs_to_other_provider(
    provider_id: str,
    origin_host: str,
    api_hosts: dict[str, set[str]],
) -> bool:
    provider_key = str(provider_id).casefold()
    return any(
        owner != provider_key
        and any(_host_belongs(origin_host, owner_host) for owner_host in hosts)
        for owner, hosts in api_hosts.items()
    )


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
            origin_host = _host(value)
            if origin_host and _origin_belongs_to_other_provider(provider_id, origin_host, api_hosts):
                removed += 1
                continue
            kept.append(value)
        row["observed_origins"] = kept
    meta = config.setdefault("provider_engine_normalization", {})
    if isinstance(meta, dict):
        meta["removed_cross_provider_capability_origins"] = removed
    return config, removed


def validate_artifact(data: bytes, provider_id: str) -> None:
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
            raise ValueError(f"patched published provider rejected provider={provider_id}:\n{detail or 'no diagnostic'}")
    finally:
        temporary.unlink(missing_ok=True)


def published_name(provider_id: str, old_path: Path, digest: str) -> str:
    parts = old_path.stem.split("--")
    source = parts[-2] if len(parts) >= 3 else "nuvio"
    return f"{safe_fragment(provider_id.casefold())}--{safe_fragment(source)}--{digest[:16]}.js"


def merge_patch_records(existing: Any, records: list[dict[str, Any]]) -> list[Any]:
    merged = list(existing) if isinstance(existing, list) else []
    for record in records:
        if record not in merged:
            merged.append(record)
    return merged


PUBLICATION_CONTRACT_SCHEMA = 2
PUBLICATION_CONTRACT_FILES = (
    "scripts/reapply_published_overrides.py",
    "scripts/apply_provider_overrides.py",
    "scripts/override_text_utils.py",
    "scripts/provider_engine_normalizer.py",
    "scripts/provider_security_hardening.py",
    "scripts/provider_purification.py",
    "scripts/validate_provider_artifact.cjs",
    "engine_v2/scripts/purify-provider.mjs",
    "package-lock.json",
)


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _publication_file_sha(relative: str, path: Path) -> str:
    """Hash build inputs while excluding release-only metadata.

    package-lock.json participates because dependency/integrity drift can change
    the build environment. Its root package version is synchronized to the Nuvio
    release *after* provider reconstruction, however, and cannot affect provider
    bytes. Excluding only those two release fields prevents a self-invalidating
    publication fingerprint while keeping the entire dependency graph locked.
    """
    if relative != "package-lock.json":
        return hashlib.sha256(path.read_bytes()).hexdigest()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("package-lock.json must be an object")
    normalized = json.loads(json.dumps(payload))
    normalized.pop("version", None)
    packages = normalized.get("packages")
    if isinstance(packages, dict) and isinstance(packages.get(""), dict):
        packages[""].pop("version", None)
    return _canonical_sha(normalized)


def publication_contract_sha(config: dict[str, Any]) -> str:
    """Hash every deterministic input that can change derived provider bytes.

    This deliberately includes the complete sanitized override/capability policy.
    A real policy change may rebuild more providers than strictly necessary, but a
    Core invocation with unchanged inputs performs no provider reconstruction at all.
    Release-only version metadata is canonicalized out of package-lock.json so
    version synchronization cannot invalidate the provider build it follows.
    """
    files: dict[str, str] = {}
    relatives = set(PUBLICATION_CONTRACT_FILES)
    patch_dir = ROOT / "scripts" / "provider_patches"
    if patch_dir.is_dir():
        relatives.update(
            path.relative_to(ROOT).as_posix()
            for path in patch_dir.rglob("*.py")
            if path.is_file()
        )
    for relative in sorted(relatives):
        path = (ROOT / relative).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"unsafe publication contract input: {relative}") from exc
        if not path.is_file():
            raise ValueError(f"missing publication contract input: {relative}")
        files[relative] = _publication_file_sha(relative, path)
    return _canonical_sha({
        "schema_version": PUBLICATION_CONTRACT_SCHEMA,
        "config": config,
        "files": files,
    })


def _adaptive_runtime_contract(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "profile": record.get("profile"),
            "phase": record.get("phase"),
            "revision": record.get("revision"),
            "options": record.get("options"),
        }
        for record in (row.get("local_patches") or [])
        if isinstance(record, dict)
        and record.get("type") == "patch_profile"
        and record.get("profile") == "adaptive_runtime_recovery"
        and record.get("phase") == "runtime"
    ]


def provider_build_input_sha(
    provider_id: str,
    base_sha256: str,
    contract_sha256: str,
    provenance_row: dict[str, Any],
) -> str:
    return _canonical_sha({
        "schema_version": PUBLICATION_CONTRACT_SCHEMA,
        "provider_id": str(provider_id).casefold(),
        "base_sha256": str(base_sha256).casefold(),
        "publication_contract_sha256": str(contract_sha256).casefold(),
        "adaptive_runtime": _adaptive_runtime_contract(provenance_row),
        "preservation": {
            "activation_mode": provenance_row.get("activation_mode"),
            "preserved_reason": provenance_row.get("preserved_reason"),
        },
    })


def fast_fixed_point_check(
    primary: dict[str, Any],
    primary_path: Path,
    secondary_paths: tuple[Path, ...],
    config: dict[str, Any],
    provenance: dict[str, Any] | None,
    *,
    removed_hooks: list[Any],
    removed_origins: int,
) -> tuple[bool, str]:
    """Verify immutable inputs/references without rebuilding provider JavaScript."""
    if provenance is None or not isinstance(provenance.get("providers"), dict):
        return False, "missing-provenance"
    if removed_hooks or removed_origins:
        return False, "sanitized-config-stale"

    rows = provenance["providers"]
    contract_sha = publication_contract_sha(config)
    contract_meta = provenance.get("provider_publication_contract")
    if not isinstance(contract_meta, dict):
        return False, "missing-publication-contract"
    if int(contract_meta.get("schema_version") or 0) != PUBLICATION_CONTRACT_SCHEMA:
        return False, "publication-contract-schema-changed"
    if str(contract_meta.get("sha256") or "").casefold() != contract_sha:
        return False, "publication-contract-changed"

    primary_by_id: dict[str, dict[str, Any]] = {}
    for entry in primary.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        relative = str(entry.get("filename") or "").strip()
        if not provider_id or not relative.startswith("providers/"):
            return False, f"invalid-primary-row:{provider_id or 'missing-id'}"
        primary_by_id[provider_id] = entry
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            return False, f"missing-provenance:{provider_id}"
        base_path, base_sha = resolve_base(provider_id, row, require=True)
        assert base_path is not None and base_sha is not None
        expected_input = provider_build_input_sha(provider_id, base_sha, contract_sha, row)
        if str(row.get("build_input_sha256") or "").casefold() != expected_input:
            return False, f"provider-input-changed:{provider_id}"
        if str(row.get("published_filename") or "") != relative:
            return False, f"published-reference-drift:{provider_id}"
        public_path = (ROOT / relative).resolve()
        try:
            public_path.relative_to(PROVIDERS.resolve())
        except ValueError:
            return False, f"unsafe-public-path:{provider_id}"
        if not public_path.is_file():
            return False, f"missing-public-bundle:{provider_id}"
        actual_public_sha = hashlib.sha256(public_path.read_bytes()).hexdigest()
        if actual_public_sha != str(row.get("sha256") or "").casefold():
            return False, f"public-sha-drift:{provider_id}"
        proof = row.get("final_fixed_point")
        if not isinstance(proof, dict):
            return False, f"missing-fixed-point-proof:{provider_id}"
        if proof.get("verified") is not True or proof.get("mangle") is not False:
            return False, f"invalid-fixed-point-proof:{provider_id}"
        if str(proof.get("tool_version") or "") != TERSER_VERSION:
            return False, f"fixed-point-tool-changed:{provider_id}"
        if str(proof.get("sha256") or "").casefold() != actual_public_sha:
            return False, f"fixed-point-proof-sha-drift:{provider_id}"

        authoritative_types = configured_authoritative_types(config, provider_id)
        if authoritative_types and entry.get("supportedTypes") != authoritative_types:
            return False, f"supported-types-drift:{provider_id}"
        for key, value in configured_manifest_overrides(config, provider_id).items():
            if entry.get(key) != value:
                return False, f"manifest-override-drift:{provider_id}"

    if len(primary_by_id) != len(rows):
        return False, "manifest-provenance-provider-count-drift"

    for path in secondary_paths:
        payload = load_manifest(path)
        if payload is None:
            continue
        for entry in payload.get("scrapers") or []:
            if not isinstance(entry, dict):
                continue
            provider_id = str(entry.get("id") or "").strip().casefold()
            primary_entry = primary_by_id.get(provider_id)
            if primary_entry is None:
                continue
            if entry.get("filename") != "../" + str(primary_entry.get("filename") or ""):
                return False, f"secondary-reference-drift:{path.name}:{provider_id}"
            if primary_entry.get("version") and entry.get("version") != primary_entry.get("version"):
                return False, f"secondary-version-drift:{path.name}:{provider_id}"
            if isinstance(primary_entry.get("supportedTypes"), list):
                if entry.get("supportedTypes") != primary_entry.get("supportedTypes"):
                    return False, f"secondary-types-drift:{path.name}:{provider_id}"
            for key, value in configured_manifest_overrides(config, provider_id).items():
                if entry.get(key) != value:
                    return False, f"secondary-override-drift:{path.name}:{provider_id}"

    return True, (
        f"fixed-point inputs={len(primary_by_id)} contract={contract_sha[:16]} "
        f"primary={primary_path.relative_to(ROOT).as_posix()}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--primary",
        default=None,
        help="Repository-relative manifest transaction to update (default: pending manifest.next.json when present, otherwise manifest.json)",
    )
    parser.add_argument(
        "--skip-secondary",
        action="store_true",
        help="Do not rewrite language projection manifests for a pending transaction",
    )
    args = parser.parse_args()

    primary_arg = (
        Path(args.primary)
        if args.primary
        else Path("manifest.next.json" if (ROOT / "manifest.next.json").is_file() else "manifest.json")
    )
    if primary_arg.is_absolute():
        raise ValueError("--primary must be repository-relative")
    primary_path = (ROOT / primary_arg).resolve()
    try:
        primary_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("--primary escapes repository root") from exc
    pending_transaction = primary_arg.as_posix() == "manifest.next.json"
    secondary_paths = () if args.skip_secondary or pending_transaction else SECONDARY

    primary = load_manifest(primary_path)
    if primary is None:
        raise ValueError(f"{primary_arg.as_posix()} is missing")

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

    if args.check:
        fast_ok, fast_reason = fast_fixed_point_check(
            primary,
            primary_path,
            secondary_paths,
            override_config,
            provenance,
            removed_hooks=removed_hooks,
            removed_origins=removed_origins,
        )
        if fast_ok:
            print(f"FIELD_PROVIDER_FAST_FIXED_POINT status=hit {fast_reason}")
            print("published provider overrides are current")
            return 0
        print(f"FIELD_PROVIDER_FAST_FIXED_POINT status=miss reason={fast_reason}")

    publication_contract = publication_contract_sha(override_config)
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

        # The published bundle is only a derived artifact. Provider logic always
        # starts from the durable ProviderBase captured by the provider pipeline.
        original = path.read_bytes()
        provider_provenance = provenance_rows.get(provider_id) if provenance_rows else None
        if not isinstance(provider_provenance, dict):
            raise ValueError(f"{provider_id}: missing provenance required for durable ProviderBase")
        provider_base_path, provider_base_sha = resolve_base(
            provider_id,
            provider_provenance,
            require=True,
        )
        assert provider_base_path is not None and provider_base_sha is not None
        provider_base = provider_base_path.read_bytes()
        terminal_quarantine = (
            AUDIT_QUARANTINE_MARKER.encode("utf-8") in original
        )
        audit_terminal_quarantine = (
            terminal_quarantine
            and "--nuvio-audit-quarantine--" in relative
        )
        if terminal_quarantine:
            patched = original
            records = []
        else:
            isolated_text, removed_wrappers = strip_foreign_provider_wrappers(
                provider_base.decode("utf-8", errors="strict"), provider_id, override_config
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
        # all-published-provider-security-finalization-v1
        # Security is independent from activation/quarantine state. Run this after
        # either branch above so disabled and terminal-quarantined bundles receive
        # the same mandatory global hardening as active providers.
        security_hardened, security_report = harden_bytes(patched)
        if security_hardened != patched:
            records = list(records) + [{
                "type": "provider_security_hardening",
                "phase": "final-post-transform",
                "revision": 1,
                "scope": "all-published-providers",
                "structured_parse_changes": int(security_report.get("structuredParseChanges") or 0),
                "literal_decode_changes": int(security_report.get("literalDecodeChanges") or 0),
                "hostname_changes": int(security_report.get("hostnameChanges") or 0),
                "percent_decode_changes": int(security_report.get("percentDecodeChanges") or 0),
                "html_entity_decode_reorders": int(security_report.get("htmlEntityDecodeReorders") or 0),
                "console_sink_changes": int(security_report.get("consoleSinkChanges") or 0),
                "console_shadow": bool(security_report.get("consoleShadow")),
            }]
        patched = security_hardened
        assert_hardened(patched.decode("utf-8", errors="strict"))
        # Final provider bytes are purified only after every Core/provider/runtime
        # transform. These exact validated bytes are content-addressed and later
        # proved by Deep and native Labs.
        purified, purification = purify_bytes(patched)
        # Provenance describes net published-byte changes, not transient
        # intermediate normalization. A provider may already be the canonical
        # purified fixed point even when an earlier hardening pass temporarily
        # rewrites formatting before purification restores the exact original
        # bytes. Recording that transient pass would mutate PROVENANCE.json on
        # every verification run and break publication idempotence.
        if purification["applied"] and purified != original:
            records = list(records) + [{
                "type": "provider_purification",
                "phase": "final-post-transform",
                "revision": 2,
                "tool": "terser",
                "tool_version": str(purification.get("toolVersion") or ""),
                "mode": str(purification.get("mode") or ""),
                "mangle": False,
                "fixed_point_verified": bool(purification.get("fixedPointVerified")),
                "conservative_compression": bool(purification.get("conservativeCompression")),
                "risk_flags": list(purification.get("riskFlags") or []),
                "source_sha256": purification["sourceSha256"],
                "output_sha256": purification["candidateSha256"],
                "bytes_before": purification["bytesBefore"],
                "bytes_after": purification["bytesAfter"],
            }]
        patched = purified
        assert_hardened(patched.decode("utf-8", errors="strict"))
        changed = patched != original
        # Validate every final published artifact, not only bundles whose bytes changed.
        # This makes new publication/security policies retroactive across the full catalogue.
        validate_artifact(patched, provider_id)
        if changed:
            applied_count += 1
        digest = hashlib.sha256(patched).hexdigest()
        new_relative = f"providers/{published_name(provider_id, path, digest)}"
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
            "base_sha256": provider_base_sha,
            "final_fixed_point": {
                "schema_version": 1,
                "verified": bool(purification.get("fixedPointVerified", True)),
                "tool": "terser",
                "tool_version": str(purification.get("toolVersion") or TERSER_VERSION),
                "mangle": False,
                "sha256": digest,
            },
            "records": records,
            "terminal_quarantine": terminal_quarantine,
            "audit_terminal_quarantine": audit_terminal_quarantine,
        }

    secondary_payloads: list[tuple[Path, dict[str, Any]]] = []
    for path in secondary_paths:
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
            if str(row.get("base_sha256") or "").casefold() != str(update["base_sha256"]).casefold():
                raise ValueError(f"{provider_id}: ProviderBase changed outside provider pipeline")
            if update.get("terminal_quarantine") or "patched_sha256" in row or update["records"]:
                row["patched_sha256"] = update["sha256"]
            if update["records"]:
                row["local_patches"] = merge_patch_records(row.get("local_patches"), update["records"])
            row["final_fixed_point"] = dict(update["final_fixed_point"])
            row["build_contract_schema"] = PUBLICATION_CONTRACT_SCHEMA
            row["build_input_sha256"] = provider_build_input_sha(
                provider_id,
                str(update["base_sha256"]),
                publication_contract,
                row,
            )
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
                    if str(value) and str(value) not in {"configured_safety_quarantine", AUDIT_QUARANTINE_BLOCKER}
                ]
                row["activation_blockers"] = blockers + ["configured_safety_quarantine"]

    if provenance is not None:
        provenance["provider_publication_contract"] = {
            "schema_version": PUBLICATION_CONTRACT_SCHEMA,
            "sha256": publication_contract,
            "provider_count": len(provenance_updates),
            "mode": "provider_base_plus_deterministic_core",
        }

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
        if json.loads(primary_path.read_text(encoding="utf-8")) != primary:
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
    write_manifest(primary_path, primary)
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
    changed_provider_rows = sorted(
        (provider_id, old, new)
        for provider_id, (old, new) in updates.items()
        if old != new
    )
    if changed_provider_rows and len(changed_provider_rows) <= 20:
        from apply_provider_overrides import _provider_export_floor, _strip_generated_core_tail

        def _fixed_point_diff(left: str, right: str) -> tuple[int, int]:
            prefix = 0
            limit = min(len(left), len(right))
            while prefix < limit and left[prefix] == right[prefix]:
                prefix += 1
            suffix = 0
            remaining = limit - prefix
            while suffix < remaining and left[len(left) - 1 - suffix] == right[len(right) - 1 - suffix]:
                suffix += 1
            return prefix, suffix

        for provider_id, old_relative, new_relative in changed_provider_rows:
            old_path = ROOT / old_relative
            new_path = ROOT / new_relative
            if not old_path.is_file() or not new_path.is_file():
                continue
            before_text = old_path.read_text(encoding="utf-8", errors="replace")
            after_text = new_path.read_text(encoding="utf-8", errors="replace")
            before_base, before_stripped = _strip_generated_core_tail(before_text)
            after_base, after_stripped = _strip_generated_core_tail(after_text)
            prefix, suffix = _fixed_point_diff(before_text, after_text)
            base_prefix, base_suffix = _fixed_point_diff(before_base, after_base)
            markers = (
                "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
                "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
                "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
                "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
                "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
                "NUVIO_GLOBAL_STREAM_FACTS_V1",
                "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
                "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
                "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",
                "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
            )
            marker_state = ";".join(
                f"{marker.replace('NUVIO_', '')}:{before_text.find(marker)}>{after_text.find(marker)}"
                for marker in markers
            )
            print(
                "FIELD_PROVIDER_FIXED_POINT_ROOT "
                f"provider={provider_id} "
                f"len={len(before_text)}>{len(after_text)} first_diff={prefix} common_suffix={suffix} "
                f"floor={_provider_export_floor(before_text)}>{_provider_export_floor(after_text)} "
                f"stripped={str(before_stripped).lower()}>{str(after_stripped).lower()} "
                f"base_len={len(before_base)}>{len(after_base)} "
                f"base_sha={hashlib.sha256(before_base.encode('utf-8')).hexdigest()[:16]}>"
                f"{hashlib.sha256(after_base.encode('utf-8')).hexdigest()[:16]} "
                f"base_equal={str(before_base == after_base).lower()} "
                f"base_first_diff={base_prefix} base_common_suffix={base_suffix} markers={marker_state}"
            )
            if before_base != after_base:
                left = before_base[max(0, base_prefix - 100): base_prefix + 220]
                right = after_base[max(0, base_prefix - 100): base_prefix + 220]
                print(
                    "FIELD_PROVIDER_FIXED_POINT_BASE_DIFF "
                    f"provider={provider_id} before={json.dumps(left, ensure_ascii=True)} "
                    f"after={json.dumps(right, ensure_ascii=True)}"
                )

    if changed_provider_rows:
        print(
            "FIELD_PROVIDER_REF_CHANGES "
            f"count={len(changed_provider_rows)} ids={','.join(row[0] for row in changed_provider_rows)}"
        )
        print(
            "FIELD_PROVIDER_REF_TRANSITIONS values="
            + ",".join(
                f"{provider_id}:{Path(old).stem.rsplit('--', 1)[-1][:16]}>"
                f"{Path(new).stem.rsplit('--', 1)[-1][:16]}"
                for provider_id, old, new in changed_provider_rows
            )
        )
    print(
        f"published overrides reapplied: patched={applied_count}, "
        f"manifest_refs={changed_refs}, provenance_refs={provenance_refs}, "
        f"superseded_deferred_to_prune={deferred}, isolated_hooks={len(removed_hooks)}, "
        f"isolated_wrappers={removed_wrappers_total}, isolated_origins={removed_origins}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
