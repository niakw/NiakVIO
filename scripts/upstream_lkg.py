#!/usr/bin/env python3
"""Content-addressed last-known-good snapshots for configured upstream repositories.

The currently published provider bundles remain the functional fallback used by
runtime promotion. These upstream snapshots protect discovery from a missing,
truncated or corrupted source manifest and from individual provider-download
failures. Snapshots are finalized only after the complete deep workflow reaches
its write-enabled publication job.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "upstream-lkg.json"
STORE_ROOT = ROOT / "upstream-lkg"
MANIFEST_ROOT = STORE_ROOT / "manifests"
PROVIDER_ROOT = STORE_ROOT / "providers"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_fragment(value: str) -> str:
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip(".-")
    return cleaned[:120] or "item"


def load_registry(root: Path = ROOT) -> dict[str, Any]:
    path = root / "upstream-lkg.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("sources"), dict):
            return payload
    except (OSError, json.JSONDecodeError):
        pass
    return {
        "schema_version": 1,
        "description": "Last two syntactically complete snapshots per upstream; current published bundles remain the functional runtime fallback.",
        "sources": {},
    }


def _manifest_path(root: Path, filename: str) -> Path:
    return root / "upstream-lkg" / "manifests" / filename


def _provider_path(root: Path, filename: str) -> Path:
    return root / "upstream-lkg" / "providers" / filename


def current_generation(registry: dict[str, Any], source_key: str) -> dict[str, Any] | None:
    row = (registry.get("sources") or {}).get(source_key)
    if not isinstance(row, dict):
        return None
    generations = row.get("generations") or []
    return generations[0] if generations and isinstance(generations[0], dict) else None


def load_manifest_snapshot(registry: dict[str, Any], source_key: str, root: Path = ROOT) -> tuple[dict[str, Any], str] | None:
    generation = current_generation(registry, source_key)
    if not generation:
        return None
    filename = generation.get("manifest_file")
    if not isinstance(filename, str):
        return None
    path = _manifest_path(root, filename)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("scrapers"), list):
        return None
    return payload, str(generation.get("manifest_url") or f"upstream-lkg:{source_key}")


def load_provider_snapshot(registry: dict[str, Any], source_key: str, upstream_id: str, root: Path = ROOT) -> bytes | None:
    generation = current_generation(registry, source_key)
    if not generation:
        return None
    providers = generation.get("providers") or {}
    record = providers.get(str(upstream_id)) if isinstance(providers, dict) else None
    if not isinstance(record, dict):
        return None
    filename = record.get("file")
    expected = record.get("sha256")
    if not isinstance(filename, str) or not isinstance(expected, str):
        return None
    path = _provider_path(root, filename)
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return data if sha256(data) == expected else None


def validate_manifest_quality(manifest: dict[str, Any], source_key: str, registry: dict[str, Any]) -> dict[str, Any]:
    scrapers = manifest.get("scrapers")
    if not isinstance(scrapers, list) or not scrapers:
        raise ValueError("missing or empty scrapers array")
    identifiers: list[str] = []
    valid_filenames = 0
    for index, entry in enumerate(scrapers):
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id") or entry.get("name") or f"entry-{index}").strip()
        if provider_id:
            identifiers.append(provider_id.casefold())
        filename = entry.get("filename")
        if isinstance(filename, str) and filename.strip() and not filename.lstrip().startswith(("javascript:", "data:")):
            valid_filenames += 1
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate provider identifiers")
    if valid_filenames < max(1, math.ceil(len(scrapers) * 0.8)):
        raise ValueError("too many entries without a valid provider filename")
    previous = current_generation(registry, source_key)
    previous_count = int(previous.get("declared") or 0) if previous else 0
    if previous_count and len(scrapers) < max(3, math.floor(previous_count * 0.60)):
        raise ValueError(f"suspicious manifest shrink: {len(scrapers)} < 60% of previous {previous_count}")
    return {"declared": len(scrapers), "valid_filenames": valid_filenames, "previous_declared": previous_count}


def create_pending(stage: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "sources": {},
        "stage": str(stage),
    }


def record_pending_source(
    pending: dict[str, Any], stage: Path, source_key: str, manifest: dict[str, Any],
    manifest_url: str, raw_provider_records: dict[str, tuple[bytes, str]],
) -> None:
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_digest = sha256(manifest_bytes)
    manifest_name = f"{safe_fragment(source_key)}-{manifest_digest[:16]}.json"
    manifest_dir = stage / "upstream-lkg-pending" / "manifests"
    provider_dir = stage / "upstream-lkg-pending" / "providers"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    provider_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / manifest_name).write_bytes(manifest_bytes)
    providers: dict[str, Any] = {}
    for upstream_id, (data, provider_url) in raw_provider_records.items():
        digest = sha256(data)
        filename = f"{digest}.js"
        path = provider_dir / filename
        if not path.exists():
            path.write_bytes(data)
        providers[str(upstream_id)] = {
            "sha256": digest,
            "file": filename,
            "provider_url": provider_url,
            "bytes": len(data),
        }
    pending["sources"][source_key] = {
        "captured_at": now_iso(),
        "manifest_url": manifest_url,
        "manifest_sha256": manifest_digest,
        "manifest_file": manifest_name,
        "declared": len(manifest.get("scrapers") or []),
        "providers": providers,
    }


def write_pending(pending: dict[str, Any], stage: Path) -> Path:
    path = stage / "upstream-lkg-pending.json"
    path.write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def finalize_pending(pending_path: Path, root: Path = ROOT, keep_generations: int = 2) -> dict[str, Any]:
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    registry = load_registry(root)
    manifest_src = pending_path.parent / "upstream-lkg-pending" / "manifests"
    provider_src = pending_path.parent / "upstream-lkg-pending" / "providers"
    manifest_dst = root / "upstream-lkg" / "manifests"
    provider_dst = root / "upstream-lkg" / "providers"
    manifest_dst.mkdir(parents=True, exist_ok=True)
    provider_dst.mkdir(parents=True, exist_ok=True)
    changed_sources = 0
    for source_key, generation in (pending.get("sources") or {}).items():
        if not isinstance(generation, dict):
            continue
        mf = generation.get("manifest_file")
        if not isinstance(mf, str) or not (manifest_src / mf).is_file():
            continue
        shutil.copy2(manifest_src / mf, manifest_dst / mf)
        for record in (generation.get("providers") or {}).values():
            if not isinstance(record, dict):
                continue
            filename = record.get("file")
            if isinstance(filename, str) and (provider_src / filename).is_file() and not (provider_dst / filename).exists():
                shutil.copy2(provider_src / filename, provider_dst / filename)
        source_row = registry.setdefault("sources", {}).setdefault(source_key, {"generations": []})
        generations = [generation] + [row for row in source_row.get("generations") or [] if row.get("manifest_sha256") != generation.get("manifest_sha256")]
        source_row["generations"] = generations[:max(1, keep_generations)]
        changed_sources += 1
    registry["updated_at"] = now_iso()
    (root / "upstream-lkg.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    referenced_manifests: set[str] = set()
    referenced_providers: set[str] = set()
    for source_row in (registry.get("sources") or {}).values():
        for generation in source_row.get("generations") or []:
            if generation.get("manifest_file"):
                referenced_manifests.add(str(generation["manifest_file"]))
            for record in (generation.get("providers") or {}).values():
                if isinstance(record, dict) and record.get("file"):
                    referenced_providers.add(str(record["file"]))
    for path in manifest_dst.glob("*.json"):
        if path.name not in referenced_manifests:
            path.unlink()
    for path in provider_dst.glob("*.js"):
        if path.name not in referenced_providers:
            path.unlink()
    return {"changed_sources": changed_sources, "manifest_files": len(referenced_manifests), "provider_files": len(referenced_providers)}
