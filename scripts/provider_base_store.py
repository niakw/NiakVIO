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

CLEAN_RECONSTRUCTION_SOURCE = "niakvio-clean-reconstruction-v2"
CLEAN_RECONSTRUCTION_AUTHORING_VERSION = 2


def is_clean_reconstructed(provenance_row: dict[str, Any] | None) -> bool:
    row = provenance_row if isinstance(provenance_row, dict) else {}
    return (
        str(row.get("base_source") or "") == CLEAN_RECONSTRUCTION_SOURCE
        and row.get("clean_reconstruction_verified") is True
        and int(row.get("clean_reconstruction_authoring_version") or 0)
        >= CLEAN_RECONSTRUCTION_AUTHORING_VERSION
    )


def requires_clean_reconstruction(provenance_row: dict[str, Any] | None) -> bool:
    return not is_clean_reconstructed(provenance_row)


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


def build_clean_provider_seed(
    provider_id: str,
    manifest_entry: dict[str, Any] | None = None,
    *,
    known_site: str | None = None,
) -> bytes:
    """Create NiakVIO-owned provider code without importing upstream JavaScript.

    Upstream manifests/code may contribute metadata and route knowledge, but
    executable ProviderBase bytes always start from NiakVIO-owned source.
    A brand-new provider is intentionally inert until Learning/Deep reconstructs
    and proves a provider-specific resolver.
    """
    entry = manifest_entry if isinstance(manifest_entry, dict) else {}
    supported = [
        str(value).strip().casefold()
        for value in entry.get("supportedTypes") or []
        if str(value).strip().casefold() in {"movie", "tv", "anime"}
    ]
    supported = list(dict.fromkeys(supported))
    display_name = str(entry.get("name") or provider_id).strip() or provider_id
    metadata = {
        "providerId": canonical_id(provider_id),
        "displayName": display_name,
        "knownSite": str(known_site or "").strip() or None,
        "supportedTypes": supported,
        "reconstructionState": "needs-learning-repair",
        "authoring": "niakvio-owned",
        "upstreamCodeEmbedded": False,
    }
    payload = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    source = (
        '"use strict";\n\n'
        '/* NIAKVIO_PROVIDER_BASE_OWNED_V1 */\n'
        f'const NIAKVIO_PROVIDER_META = Object.freeze({payload});\n'
        'async function getStreams(_tmdbId, _mediaType, _season, _episode) { return []; }\n'
        'module.exports = { getStreams, __niakvioProviderBase: NIAKVIO_PROVIDER_META };\n'
    )
    return source.encode("utf-8")


def persist_clean_provider_seed(
    provider_id: str,
    manifest_entry: dict[str, Any] | None = None,
    *,
    known_site: str | None = None,
) -> tuple[str, str, bool]:
    return persist_base_from_seed(
        provider_id,
        build_clean_provider_seed(provider_id, manifest_entry, known_site=known_site),
    )


def repair_legacy_bases() -> dict[str, Any]:
    """Mark every pre-v2 ProviderBase as compatibility-only legacy state.

    This command deliberately does *not* reconstruct ProviderBase bytes. The
    currently published implementation may remain available to existing clients
    and may be observed as LKG evidence, but it is never an executable seed for
    the new NiakVIO-owned ProviderBase.

    A provider leaves this queue only after a clean NiakVIO seed has been
    reconstructed independently, validated in Learning/Lab, materialized as a
    ProviderBase, and recorded with CLEAN_RECONSTRUCTION_SOURCE.
    """
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    rows = provenance.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("PROVENANCE.providers must be an object")

    provider_count = 0
    reconstruction_required = 0
    clean_reconstructed = 0
    marked_at = datetime.now(timezone.utc).isoformat()

    for entry in manifest.get("scrapers") or []:
        if not isinstance(entry, dict):
            continue
        provider_id = canonical_id(str(entry.get("id") or ""))
        if not provider_id:
            continue
        provider_count += 1
        row = rows.get(provider_id)
        if not isinstance(row, dict):
            raise ValueError(f"{provider_id}: missing provenance row")

        path, _digest = resolve_base(provider_id, row, require=True)
        assert path is not None
        assert_base_layering(path.read_bytes(), provider_id)

        if requires_clean_reconstruction(row):
            reconstruction_required += 1
            row["clean_reconstruction_required"] = True
            row["legacy_provider_base_role"] = "compatibility-lkg-only"
            row["legacy_provider_js_role"] = "knowledge-only-for-reconstruction"
            row["legacy_provider_js_executed_for_reconstruction"] = False
            row["clean_reconstruction_marked_at"] = marked_at
        else:
            clean_reconstructed += 1
            row["clean_reconstruction_required"] = False
            row.pop("legacy_provider_base_role", None)
            row.pop("legacy_provider_js_role", None)
            row.pop("legacy_provider_js_executed_for_reconstruction", None)

    provenance["provider_base_store"] = {
        "schema_version": 4,
        "provider_count": provider_count,
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": reconstruction_required,
        "authoring_version": CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
        "authoring_policy": "niakvio-owned-clean-reconstruction-only",
        "clean_source": CLEAN_RECONSTRUCTION_SOURCE,
        "legacy_provider_role": "compatibility-lkg-and-knowledge-only",
        "upstream_code_role": "knowledge-only",
        "upstream_code_executed": False,
        "published_legacy_code_may_seed_new_base": False,
        "upstream_code_may_seed_new_base": False,
        "git_history_code_may_seed_new_base": False,
        "core_may_create_or_mutate_base": False,
        "derived_layers_forbidden": list(DERIVED_BASE_MARKERS),
    }
    PROVENANCE.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "providers": provider_count,
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": reconstruction_required,
    }

def migrate_existing() -> dict[str, Any]:
    """Disabled legacy migration entry point.

    Published, upstream, snapshot and Git-history JavaScript are knowledge only;
    none of them may be transformed into a durable ProviderBase.
    """
    raise ValueError(
        "migrate-existing is disabled: legacy/upstream/public JavaScript may not seed ProviderBase; "
        "use NiakVIO clean reconstruction through Learning"
    )

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
    clean_reconstructed = sum(
        1
        for entry in manifest.get("scrapers") or []
        if isinstance(entry, dict)
        and is_clean_reconstructed(rows.get(canonical_id(str(entry.get("id") or ""))))
    )
    return {
        "checked": checked,
        "unique_bases": len(bases),
        "artifact_validation": bool(validate_artifacts),
        "clean_reconstructed": clean_reconstructed,
        "reconstruction_required": checked - clean_reconstructed,
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
            f"clean={result['clean_reconstructed']} required={result['reconstruction_required']}"
        )
    else:
        result = validate_all(validate_artifacts=bool(args.artifacts))
        print(
            f"FIELD_PROVIDER_BASE_COVERAGE checked={result['checked']} "
            f"unique_bases={result['unique_bases']} "
            f"clean={result['clean_reconstructed']} required={result['reconstruction_required']} "
            f"artifact_validation={str(result['artifact_validation']).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
