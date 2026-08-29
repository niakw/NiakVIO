#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_provider_overrides import apply_overrides, _strip_generated_core_tail
from provider_purification import split_owned_prefix_bootstraps
from upstream_lkg import load_registry

ROOT = Path(__file__).resolve().parents[1]
BASES = ROOT / "provider-bases"
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"
QUARANTINE_PATCH = "scripts/provider_patches/quarantine_provider_v1.py"
DYNAMIC_DOMAIN_PATCH = "scripts/provider_patches/runtime_repository_domain_materializer_v1.py"
DERIVED_PATCH_SCRIPTS = {
    QUARANTINE_PATCH,
    DYNAMIC_DOMAIN_PATCH,
    "scripts/provider_patches/adaptive_domain_recovery.py",
    "scripts/provider_patches/adaptive_runtime_recovery.py",
    "scripts/provider_patches/adaptive_runtime_recovery_v4.py",
    "scripts/provider_patches/adaptive_runtime_recovery_v5.py",
}

# ProviderBase owns durable provider logic. Everything below is derived publication
# state and must never become an input to the next Core build.
DERIVED_BASE_MARKERS = (
    "NUVIO_PROVIDER_QUARANTINE_V1",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_RUNTIME_COMPAT_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
    "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",
    "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
    "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
    "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
    "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
    "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
    "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
    "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
    "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5",
    "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1",
    "NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1",
    "NUVIO_RUNTIME_REPOSITORY_DOMAIN_MATERIALIZER_V1",
)

# Five providers are retained locally but are no longer present in the retained
# upstream snapshots. These commits predate the global Core/security finalizers
# and contain the last clean provider implementation from which current durable
# provider-specific overrides can be replayed.
PRE_HARDENING_MANIFEST_COMMIT = "775d35d586e2e0bafe0bb54b0ecd30527b99f51c"

LEGACY_LOCAL_SEEDS: dict[str, tuple[str, str]] = {
    "cineby": (
        "6f5c13750049ca5227d44eda192d2670c819bfea",
        "providers/cineby--nuvio--d96e163f6372cafd.js",
    ),
    "cinemm": (
        "6f5c13750049ca5227d44eda192d2670c819bfea",
        "providers/cinemm--published-baseline--c298a89c18a2efb5.js",
    ),
    "goatapi": (
        "6f5c13750049ca5227d44eda192d2670c819bfea",
        "providers/goatapi--published-baseline--1db196320e8c7bf2.js",
    ),
    "toflix": (
        "0c16cc5a4fe009c9585017b3fc74653749615790",
        "providers/toflix--published-baseline--dd2dbb2d068dae21.js",
    ),
    "4khdhubnew": (
        "4ac0002d48d725bb35e14f2948875cf80c0b3443",
        "providers/4khdhubnew--published-baseline--e64aea603b3c3786.js",
    ),
}


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_relative(provider_id: str, digest: str) -> str:
    return f"provider-bases/{safe_fragment(provider_id.casefold())}--base--{digest[:16]}.js"


def safe_base_path(relative: str) -> Path | None:
    if not isinstance(relative, str) or not relative.startswith("provider-bases/"):
        return None
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(BASES.resolve())
    except ValueError:
        return None
    return path


def forbidden_base_markers(data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="strict")
    return [marker for marker in DERIVED_BASE_MARKERS if marker in text]


def assert_base_layering(data: bytes, provider_id: str) -> None:
    markers = forbidden_base_markers(data)
    if markers:
        raise ValueError(
            f"{provider_id}: ProviderBase contains derived publication layer(s): "
            + ",".join(markers)
        )


def strip_adaptive_runtime_wrappers(text: str) -> tuple[str, int]:
    """Remove only owned adaptive runtime wrappers from legacy provider bytes."""
    markers = (
        "/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
        "/* NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5:",
    )
    call = '})(typeof globalThis!=="undefined"?globalThis:this,'
    removed = 0
    while True:
        starts = [text.find(marker) for marker in markers]
        starts = [value for value in starts if value >= 0]
        if not starts:
            break
        start = min(starts)
        call_at = text.find(call, start)
        end = text.find(");", call_at) if call_at >= 0 else -1
        if call_at < 0 or end < 0:
            raise ValueError("unterminated adaptive runtime recovery wrapper in ProviderBase")
        end += 2
        if text[end:end + 2] == "\r\n":
            end += 2
        elif text[end:end + 1] in ("\r", "\n"):
            end += 1
        text = text[:start] + text[end:]
        removed += 1
    return text.rstrip(), removed


def validate_base(data: bytes, provider_id: str) -> None:
    # A ProviderBase must remain an independently valid provider implementation.
    assert_base_layering(data, provider_id)
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    try:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), "--provider-base", str(temporary)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            detail = "\n".join(v.strip() for v in (result.stdout, result.stderr) if v.strip())
            raise ValueError(f"{provider_id}: ProviderBase rejected: {detail or 'no diagnostic'}")
    finally:
        temporary.unlink(missing_ok=True)


def write_base(provider_id: str, data: bytes) -> tuple[str, str]:
    digest = sha256(data)
    relative = base_relative(provider_id, digest)
    path = safe_base_path(relative)
    if path is None:
        raise ValueError(f"{provider_id}: unsafe ProviderBase path")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return relative, digest


def resolve_base(provider_id: str, provenance_row: dict[str, Any], *, require: bool = True) -> tuple[Path | None, str | None]:
    relative = str(provenance_row.get("base_filename") or "").strip()
    digest = str(provenance_row.get("base_sha256") or "").strip().casefold()
    path = safe_base_path(relative)
    if path is None or not path.is_file():
        if require:
            raise ValueError(f"{provider_id}: missing durable ProviderBase")
        return None, None
    actual = sha256(path.read_bytes())
    if not digest or actual != digest:
        raise ValueError(f"{provider_id}: ProviderBase SHA mismatch expected={digest or 'missing'} actual={actual}")
    return path, actual


def clean_base_from_published(provider_id: str, published_data: bytes) -> tuple[bytes, bool]:
    """Remove every owned derived layer while preserving durable provider logic."""
    published_text = published_data.decode("utf-8", errors="strict")
    base_text, stripped_core = _strip_generated_core_tail(published_text)
    base_text, stripped_adaptive = strip_adaptive_runtime_wrappers(base_text)
    base_data = base_text.encode("utf-8")
    prefix, body = split_owned_prefix_bootstraps(base_data)
    if prefix:
        base_data = body
    assert_base_layering(base_data, provider_id)
    return base_data, bool(stripped_core or stripped_adaptive or prefix)


def persist_base_from_published(provider_id: str, published_data: bytes) -> tuple[str, str, bool]:
    """Persist provider logic only; generated Core/routing layers are always derived."""
    base_data, stripped = clean_base_from_published(provider_id, published_data)
    validate_base(base_data, provider_id)
    relative, digest = write_base(provider_id, base_data)
    return relative, digest, stripped


def persist_base_from_seed(provider_id: str, seed_data: bytes) -> tuple[str, str, bool]:
    """Rebuild durable provider logic from a clean provider seed.

    Publication-only quarantine, dynamic domain materialization and adaptive
    runtime/domain recovery are deliberately excluded. They remain derived state
    and are regenerated later by the finalizer from current policy/evidence.
    """
    rebuilt, _records = apply_overrides(
        provider_id,
        seed_data,
        phase="discovery",
        excluded_patch_scripts=DERIVED_PATCH_SCRIPTS,
        include_global_core=False,
    )
    return persist_base_from_published(provider_id, rebuilt)


def _snapshot_seed(
    registry: dict[str, Any],
    provider_id: str,
    row: dict[str, Any],
) -> tuple[bytes, str] | None:
    expected = str(row.get("upstream_sha256") or "").strip().casefold()
    upstream_id = str(row.get("upstream_id") or provider_id).strip()
    preferred = str(row.get("source") or "").strip()
    sources = registry.get("sources") or {}
    if not isinstance(sources, dict):
        return None

    ordered_sources = []
    if preferred in sources:
        ordered_sources.append(preferred)
    ordered_sources.extend(key for key in sources if key not in ordered_sources)

    matches: list[tuple[str, dict[str, Any]]] = []
    for source_key in ordered_sources:
        source_row = sources.get(source_key)
        if not isinstance(source_row, dict):
            continue
        for generation in source_row.get("generations") or []:
            if not isinstance(generation, dict):
                continue
            providers = generation.get("providers") or {}
            if not isinstance(providers, dict):
                continue
            record = providers.get(upstream_id)
            if not isinstance(record, dict):
                record = next(
                    (
                        value
                        for raw_id, value in providers.items()
                        if canonical_id(str(raw_id)) == provider_id and isinstance(value, dict)
                    ),
                    None,
                )
            if not isinstance(record, dict):
                continue
            record_sha = str(record.get("sha256") or "").strip().casefold()
            if expected and record_sha != expected:
                continue
            matches.append((source_key, record))

    if not matches:
        return None
    source_key, record = matches[0]
    filename = str(record.get("file") or "").strip()
    record_sha = str(record.get("sha256") or "").strip().casefold()
    path = (ROOT / "upstream-lkg" / "providers" / filename).resolve()
    try:
        path.relative_to((ROOT / "upstream-lkg" / "providers").resolve())
    except ValueError:
        return None
    if not path.is_file():
        return None
    data = path.read_bytes()
    if not record_sha or sha256(data) != record_sha:
        return None
    return data, f"upstream-lkg:{source_key}:{record_sha[:16]}"


def _git_seed(provider_id: str) -> tuple[bytes, str] | None:
    seed = LEGACY_LOCAL_SEEDS.get(provider_id)
    if seed is None:
        return None
    commit, path = seed
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode or not result.stdout:
        return None
    return result.stdout, f"git:{commit[:12]}:{path}"


def _pre_hardening_git_seed(provider_id: str) -> tuple[bytes, str] | None:
    """Recover only when current legacy bytes are unrecoverable (for example quarantine)."""
    manifest_result = subprocess.run(
        ["git", "show", f"{PRE_HARDENING_MANIFEST_COMMIT}:manifest.json"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if manifest_result.returncode or not manifest_result.stdout:
        return None
    try:
        manifest = json.loads(manifest_result.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    entry = next(
        (
            row
            for row in manifest.get("scrapers") or []
            if isinstance(row, dict) and canonical_id(str(row.get("id") or "")) == provider_id
        ),
        None,
    )
    if not isinstance(entry, dict):
        return None
    relative = str(entry.get("filename") or "").strip()
    if not relative.startswith("providers/"):
        return None
    result = subprocess.run(
        ["git", "show", f"{PRE_HARDENING_MANIFEST_COMMIT}:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode or not result.stdout:
        return None
    return result.stdout, f"git-pre-hardening:{PRE_HARDENING_MANIFEST_COMMIT[:12]}:{relative}"


def _latest_snapshot_seed(
    registry: dict[str, Any],
    provider_id: str,
    row: dict[str, Any],
) -> tuple[bytes, str] | None:
    """Return the newest retained raw upstream only as quarantine recovery input."""
    upstream_id = str(row.get("upstream_id") or provider_id).strip()
    sources = registry.get("sources") or {}
    if not isinstance(sources, dict):
        return None
    preferred = str(row.get("source") or "").strip()
    order = []
    if preferred in sources:
        order.append(preferred)
    order.extend(key for key in sources if key not in order)
    for source_key in order:
        source_row = sources.get(source_key)
        if not isinstance(source_row, dict):
            continue
        for generation in source_row.get("generations") or []:
            if not isinstance(generation, dict):
                continue
            providers = generation.get("providers") or {}
            if not isinstance(providers, dict):
                continue
            record = providers.get(upstream_id)
            if not isinstance(record, dict):
                record = next(
                    (
                        value
                        for raw_id, value in providers.items()
                        if canonical_id(str(raw_id)) == provider_id and isinstance(value, dict)
                    ),
                    None,
                )
            if not isinstance(record, dict):
                continue
            filename = str(record.get("file") or "").strip()
            digest = str(record.get("sha256") or "").strip().casefold()
            path = (ROOT / "upstream-lkg" / "providers" / filename).resolve()
            try:
                path.relative_to((ROOT / "upstream-lkg" / "providers").resolve())
            except ValueError:
                continue
            if not path.is_file():
                continue
            data = path.read_bytes()
            if not digest or sha256(data) != digest:
                continue
            return data, f"upstream-lkg-latest-quarantine-recovery:{source_key}:{digest[:16]}"
    return None


def _persist_recovery_fallback(
    registry: dict[str, Any],
    provider_id: str,
    row: dict[str, Any],
) -> tuple[str, str, bool, str]:
    """Recover destroyed legacy logic without changing the public quarantine state."""
    candidates = [
        _git_seed(provider_id),
        _pre_hardening_git_seed(provider_id),
        _latest_snapshot_seed(registry, provider_id, row),
    ]
    errors: list[str] = []
    for candidate in candidates:
        if candidate is None:
            continue
        seed_data, seed_source = candidate
        try:
            base_file, base_sha, stripped = persist_base_from_seed(provider_id, seed_data)
            return base_file, base_sha, stripped, seed_source
        except ValueError as exc:
            errors.append(f"{seed_source}:{exc}")
    detail = " | ".join(errors[-3:]) if errors else "no recovery candidates"
    raise ValueError(f"{provider_id}: no clean recovery seed for legacy ProviderBase ({detail})")


def repair_legacy_bases() -> dict[str, Any]:
    """Replace one-shot/public-derived bases with provider-pipeline bases.

    Exact upstream SHA is required whenever provenance has one. This prevents the
    migration from silently advancing provider logic without validation.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")
    registry = load_registry(ROOT)

    repaired = 0
    reused = 0
    old_paths: set[Path] = set()
    provider_count = 0
    repair_sources: dict[str, str] = {}

    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        provider_count += 1
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")

        existing_path, _existing_sha = resolve_base(provider_id, row, require=False)
        existing_data = existing_path.read_bytes() if existing_path is not None else None
        legacy_source = str(row.get("base_source") or "") == "one-shot-public-core-tail-extraction"
        contaminated = bool(existing_data and forbidden_base_markers(existing_data))
        if existing_data is not None and not legacy_source and not contaminated:
            assert_base_layering(existing_data, provider_id)
            reused += 1
            continue

        seed = _snapshot_seed(registry, provider_id, row)
        base_file: str
        base_sha: str
        stripped: bool
        seed_source: str

        if seed is not None:
            seed_data, seed_source = seed
            base_file, base_sha, stripped = persist_base_from_seed(provider_id, seed_data)
        elif existing_data is not None:
            # Preserve the exact current provider implementation whenever the
            # one-shot base is recoverable. This retains later provider repairs
            # without trusting a newer upstream variant. Security-normalized
            # source is allowed here because it is idempotent provider code, not
            # a Core/routing/quarantine layer.
            try:
                clean_data, stripped = clean_base_from_published(provider_id, existing_data)
                validate_base(clean_data, provider_id)
                base_file, base_sha = write_base(provider_id, clean_data)
                seed_source = "legacy-current-provider-logic"
            except ValueError:
                base_file, base_sha, stripped, seed_source = _persist_recovery_fallback(
                    registry, provider_id, row
                )
        else:
            base_file, base_sha, stripped, seed_source = _persist_recovery_fallback(
                registry, provider_id, row
            )

        if existing_path is not None:
            old_paths.add(existing_path)
        row["base_filename"] = base_file
        row["base_sha256"] = base_sha
        row["base_source"] = "provider-pipeline-legacy-rebase"
        row["base_seed_source"] = seed_source
        row["base_rebased_at"] = datetime.now(timezone.utc).isoformat()
        row["base_migration_stripped_generated_core"] = bool(stripped)
        row.pop("build_input_sha256", None)
        row.pop("final_fixed_point", None)
        repair_sources[provider_id] = seed_source
        repaired += 1

    referenced = {
        str(row.get("base_filename") or "")
        for row in rows.values()
        if isinstance(row, dict) and str(row.get("base_filename") or "")
    }
    removed = 0
    for path in old_paths:
        relative = path.relative_to(ROOT).as_posix()
        if relative not in referenced and path.is_file():
            path.unlink()
            removed += 1

    provenance["provider_base_store"] = {
        "schema_version": 2,
        "provider_count": provider_count,
        "legacy_rebased": repaired,
        "reused": reused,
        "migration": "provider-pipeline-source-rebase",
        "future_source": "provider_pipeline_only",
        "core_may_create_or_mutate_base": False,
        "derived_layers_forbidden": list(DERIVED_BASE_MARKERS),
        "dynamic_domain_layers_derived": True,
        "legacy_security_normalization_may_be_preserved": True,
        "removed_legacy_base_files": removed,
    }
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "providers": provider_count,
        "repaired": repaired,
        "reused": reused,
        "removed": removed,
        "sources": repair_sources,
    }


def migrate_existing() -> dict[str, Any]:
    """Legacy entry point retained for old workflows; new runs use repair-legacy."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")

    migrated = 0
    reused = 0
    provider_count = 0
    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        relative = str(entry.get("filename") or "").strip()
        if not provider_id or not relative.startswith("providers/"):
            continue
        provider_count += 1
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")

        existing_path, _existing_sha = resolve_base(provider_id, row, require=False)
        if existing_path is not None:
            assert_base_layering(existing_path.read_bytes(), provider_id)
            reused += 1
            continue

        public_path = (ROOT / relative).resolve()
        try:
            public_path.relative_to((ROOT / "providers").resolve())
        except ValueError as exc:
            raise ValueError(f"{provider_id}: unsafe public provider path") from exc
        if not public_path.is_file():
            raise ValueError(f"{provider_id}: missing public provider artifact {relative}")

        base_file, base_sha, stripped = persist_base_from_published(provider_id, public_path.read_bytes())
        row["base_filename"] = base_file
        row["base_sha256"] = base_sha
        row["base_source"] = "one-shot-public-core-tail-extraction"
        row["base_migrated_at"] = datetime.now(timezone.utc).isoformat()
        row["base_migration_stripped_generated_core"] = bool(stripped)
        migrated += 1

    provenance["provider_base_store"] = {
        "schema_version": 1,
        "provider_count": provider_count,
        "migrated": migrated,
        "reused": reused,
        "migration": "one-shot",
        "future_source": "provider_pipeline_only",
        "core_may_create_or_mutate_base": False,
    }
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"providers": provider_count, "migrated": migrated, "reused": reused}


def validate_all(*, validate_artifacts: bool = False) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers") or {}
    checked = 0
    bases: set[str] = set()
    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")
        path, _digest = resolve_base(provider_id, row, require=True)
        assert path is not None
        data = path.read_bytes()
        assert_base_layering(data, provider_id)
        if validate_artifacts:
            validate_base(data, provider_id)
        bases.add(path.relative_to(ROOT).as_posix())
        checked += 1
    if checked != len(manifest.get("scrapers") or []):
        raise ValueError(f"ProviderBase coverage mismatch checked={checked} manifest={len(manifest.get('scrapers') or [])}")
    return {
        "checked": checked,
        "unique_bases": len(bases),
        "artifact_validation": bool(validate_artifacts),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("migrate-existing")
    sub.add_parser("repair-legacy")
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument(
        "--artifacts",
        action="store_true",
        help="Also run the expensive Node provider validator for every base.",
    )
    args = parser.parse_args()
    if args.command == "migrate-existing":
        result = migrate_existing()
        print(
            f"FIELD_PROVIDER_BASE_MIGRATION providers={result['providers']} "
            f"migrated={result['migrated']} reused={result['reused']}"
        )
    elif args.command == "repair-legacy":
        result = repair_legacy_bases()
        print(
            f"FIELD_PROVIDER_BASE_REPAIR providers={result['providers']} "
            f"repaired={result['repaired']} reused={result['reused']} removed={result['removed']}"
        )
    else:
        result = validate_all(validate_artifacts=bool(args.artifacts))
        print(
            f"FIELD_PROVIDER_BASE_COVERAGE checked={result['checked']} "
            f"unique_bases={result['unique_bases']} "
            f"artifact_validation={str(result['artifact_validation']).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
