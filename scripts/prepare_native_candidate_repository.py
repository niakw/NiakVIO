#!/usr/bin/env python3
"""Materialize an isolated repository root for native candidate device testing.

The repair Brain writes candidate manifests/providers inside the working checkout.
Official Nuvio clients expect repository files to be reachable relative to a manifest
URL, so a device lab cannot simply point at a local filesystem path. This script
copies the candidate manifest to <serve-root>/manifest.json and copies exactly every
referenced provider file under the same relative path. A loopback-only HTTP server
can then expose the result to Nuvio without publishing the candidate first.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def safe_repo_path(raw: object) -> Path:
    value = str(raw or "").strip().replace("\\", "/")
    if not value:
        raise SystemExit("candidate repository provider has empty filename")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise SystemExit(f"unsafe candidate repository filename: {value}")
    return candidate


def materialize(manifest_path: Path, serve_root: Path) -> int:
    manifest_path = manifest_path.resolve()
    try:
        manifest_path.relative_to(ROOT)
    except ValueError as error:
        raise SystemExit(f"candidate manifest must live inside NiakVIO checkout: {manifest_path}") from error

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    scrapers = data.get("scrapers")
    if not isinstance(scrapers, list) or not scrapers:
        raise SystemExit(f"candidate manifest has no scrapers: {manifest_path}")

    serve_root = serve_root.resolve()
    if serve_root == ROOT or ROOT in serve_root.parents:
        # A nested temporary directory inside the checkout is fine, but never delete
        # the checkout root itself. The condition above catches the root exactly;
        # nested roots are intentionally allowed and cleaned below.
        if serve_root == ROOT:
            raise SystemExit("serve root must not be the NiakVIO repository root")
    shutil.rmtree(serve_root, ignore_errors=True)
    serve_root.mkdir(parents=True, exist_ok=True)

    copied = 0
    seen: set[str] = set()
    for row in scrapers:
        if not isinstance(row, dict):
            raise SystemExit("candidate manifest contains a non-object scraper")
        provider_id = str(row.get("id") or "").strip()
        key = provider_id.casefold()
        if not provider_id:
            raise SystemExit("candidate manifest contains provider without id")
        if key in seen:
            raise SystemExit(f"candidate manifest contains duplicate provider id: {provider_id}")
        seen.add(key)
        relative = safe_repo_path(row.get("filename"))
        source = (ROOT / relative).resolve()
        try:
            source.relative_to(ROOT)
        except ValueError as error:
            raise SystemExit(f"provider escapes repository root: {provider_id} -> {relative}") from error
        if not source.is_file():
            raise SystemExit(f"candidate provider file missing: {provider_id} -> {relative}")
        destination = serve_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1

    shutil.copy2(manifest_path, serve_root / "manifest.json")
    print(
        f"FIELD_NATIVE_CANDIDATE_REPOSITORY_READY manifest={manifest_path.relative_to(ROOT)} "
        f"providers={len(scrapers)} copied={copied} serve_root={serve_root}"
    )
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--serve-root", required=True)
    args = parser.parse_args()
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = ROOT / manifest
    copied = materialize(manifest, Path(args.serve_root))
    return 0 if copied > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
