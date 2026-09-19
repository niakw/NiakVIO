#!/usr/bin/env python3
"""Bind validation evidence to the exact manifest/provider bytes it validated."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _provider_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = manifest.get("scrapers")
    if not isinstance(rows, list):
        raise ValueError("manifest.scrapers must be an array")
    return [row for row in rows if isinstance(row, dict)]


def fingerprint_manifest(manifest_path: Path, root: Path | None = None) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    base = (root or manifest_path.parent).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    providers: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for row in _provider_rows(manifest):
        provider_id = str(row.get("id") or "").strip()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename:
            raise ValueError("every scraper must contain id and filename")
        target = (manifest_path.parent / filename).resolve()
        if base != target and base not in target.parents:
            raise ValueError(f"provider path escapes root: {filename}")
        if not target.is_file():
            raise FileNotFoundError(target)
        rel = target.relative_to(base).as_posix()
        if rel in seen_paths:
            raise ValueError(f"duplicate provider artifact reference: {rel}")
        seen_paths.add(rel)
        providers.append({"id": provider_id, "path": rel, "sha256": sha256_file(target)})
    providers.sort(key=lambda row: (row["id"].casefold(), row["path"]))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "manifest_path": manifest_path.relative_to(base).as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
        "providers": providers,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["generation_sha256"] = sha256_bytes(canonical)
    return payload


def validate_evidence(evidence: dict[str, Any], manifest_path: Path, root: Path | None = None) -> tuple[bool, str]:
    if not isinstance(evidence, dict) or int(evidence.get("schema_version") or 0) != SCHEMA_VERSION:
        return False, "unsupported_evidence_schema"
    current = fingerprint_manifest(manifest_path, root)
    expected_generation = str(evidence.get("generation_sha256") or "")
    if not expected_generation:
        return False, "missing_generation_sha256"
    if current["generation_sha256"] != expected_generation:
        return False, "release_generation_changed"
    if current.get("manifest_sha256") != evidence.get("manifest_sha256"):
        return False, "manifest_changed"
    if current.get("providers") != evidence.get("providers"):
        return False, "provider_set_changed"
    return True, "exact_release_generation_match"


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    fp = sub.add_parser("fingerprint")
    fp.add_argument("--manifest", default="manifest.json")
    fp.add_argument("--root", default=".")
    fp.add_argument("--output", required=True)
    check = sub.add_parser("validate")
    check.add_argument("--manifest", default="manifest.json")
    check.add_argument("--root", default=".")
    check.add_argument("--evidence", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    manifest = (root / args.manifest).resolve()
    if args.command == "fingerprint":
        payload = fingerprint_manifest(manifest, root)
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"release generation fingerprint: {payload['generation_sha256']}")
        return 0
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    passed, reason = validate_evidence(evidence, manifest, root)
    print(f"release evidence validation: {reason}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
