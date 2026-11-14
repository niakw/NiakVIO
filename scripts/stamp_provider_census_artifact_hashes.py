#!/usr/bin/env python3
"""Stamp a full-scope census status with exact active Provider artifact hashes.

The stamped file is a production-freshness ledger, not the mutable operational
census.  It may be replaced only by another all-scope replay.  A later targeted
or unresolved census can therefore update Repair state without erasing the last
fresh FULL proof for unrelated, byte-identical providers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def artifact_path(root: Path, filename: object) -> Path:
    relative = str(filename or "").strip().replace("\\", "/")
    while relative.startswith("../"):
        relative = relative[3:]
    if not relative.startswith("providers/"):
        raise ValueError(f"active provider artifact must live under providers/: {relative}")
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def active_hashes(root: Path, manifests: list[dict[str, Any]]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for manifest in manifests:
        for row in manifest.get("scrapers") or []:
            if not isinstance(row, dict) or row.get("enabled") is False:
                continue
            pid = canon(row.get("id"))
            if not pid:
                raise ValueError("active provider without id")
            current = digest(artifact_path(root, row.get("filename")))
            prior = hashes.get(pid)
            if prior is not None and prior != current:
                raise ValueError(f"{pid}: conflicting active artifact hashes across projections")
            hashes[pid] = current
    return hashes


def stamp(status: dict[str, Any], hashes: dict[str, str]) -> dict[str, Any]:
    rows = [row for row in status.get("providers") or [] if isinstance(row, dict)]
    by_id = {canon(row.get("provider")): row for row in rows if canon(row.get("provider"))}
    missing = sorted(pid for pid in hashes if pid not in by_id)
    if missing:
        raise ValueError(f"all-scope status missing active providers: {missing}")
    for pid, current in hashes.items():
        by_id[pid]["providerArtifactSha256"] = current
    status["artifactHashSchemaVersion"] = 1
    status["activeArtifactHashCount"] = len(hashes)
    return status


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    ap.add_argument("--vf-manifest", type=Path, default=Path("vf/manifest.json"))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    root = Path.cwd()
    state = stamp(
        load(args.status),
        active_hashes(root, [load(args.manifest), load(args.vf_manifest)]),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"FIELD_CENSUS_ALL_FRESHNESS_HASHES active={state['activeArtifactHashCount']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
