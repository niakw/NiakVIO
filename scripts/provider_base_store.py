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

from apply_provider_overrides import _strip_generated_core_tail

ROOT = Path(__file__).resolve().parents[1]
BASES = ROOT / "provider-bases"
MANIFEST = ROOT / "manifest.json"
PROVENANCE = ROOT / "PROVENANCE.json"


def safe_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")[:120] or "provider"


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


def validate_base(data: bytes, provider_id: str) -> None:
    # A ProviderBase must remain an independently valid provider implementation.
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, dir=ROOT) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    try:
        result = subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(temporary)],
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


def persist_base_from_published(provider_id: str, published_data: bytes) -> tuple[str, str, bool]:
    """Persist provider logic only; generated Core layers are always derived."""
    published_text = published_data.decode("utf-8", errors="strict")
    base_text, stripped = _strip_generated_core_tail(published_text)
    base_data = base_text.encode("utf-8")
    validate_base(base_data, provider_id)
    relative, digest = write_base(provider_id, base_data)
    return relative, digest, bool(stripped)


def migrate_existing() -> dict[str, Any]:
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

        existing_path, existing_sha = resolve_base(provider_id, row, require=False)
        if existing_path is not None:
            validate_base(existing_path.read_bytes(), provider_id)
            reused += 1
            continue

        public_path = (ROOT / relative).resolve()
        try:
            public_path.relative_to((ROOT / "providers").resolve())
        except ValueError as exc:
            raise ValueError(f"{provider_id}: unsafe public provider path") from exc
        if not public_path.is_file():
            raise ValueError(f"{provider_id}: missing public provider artifact {relative}")

        public_data = public_path.read_bytes()
        # This is the only allowed legacy extraction path. Once persisted,
        # production Core/compiler code must consume ProviderBase directly.
        base_file, base_sha, stripped = persist_base_from_published(provider_id, public_data)
        row["base_filename"] = base_file
        row["base_sha256"] = base_sha
        row["base_source"] = "one-shot-public-core-tail-extraction"
        row["base_migrated_at"] = datetime.now(timezone.utc).isoformat()
        row["base_migration_stripped_generated_core"] = bool(stripped)
        migrated += 1

    if provider_count != len(rows):
        missing_manifest = sorted(set(rows) - {
            str(row.get("id") or "").strip().casefold()
            for row in manifest.get("scrapers") or []
            if isinstance(row, dict)
        })
        if missing_manifest:
            raise ValueError("provenance-only providers during base migration: " + ",".join(missing_manifest[:20]))

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
        if validate_artifacts:
            validate_base(path.read_bytes(), provider_id)
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
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument(
        "--artifacts",
        action="store_true",
        help="Also run the expensive Node provider validator for every base.",
    )
    args = parser.parse_args()
    if args.command == "migrate-existing":
        result = migrate_existing()
        print(f"FIELD_PROVIDER_BASE_MIGRATION providers={result['providers']} migrated={result['migrated']} reused={result['reused']}")
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
