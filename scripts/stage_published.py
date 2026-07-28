#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage the currently published providers for frequent availability checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.json"
SOURCES_PATH = ROOT / "sources.json"
DEFAULT_STAGE = ROOT / "staging"


def safe_fragment(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip(".-")
    return cleaned[:120] or "provider"


def canonical_id(value: str) -> str:
    return safe_fragment(value).casefold().replace("_", "-")


def is_under(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def exclusion_reason(entry: dict[str, Any], data: bytes, exclusions: dict[str, Any]) -> str | None:
    cid = canonical_id(str(entry.get("id") or entry.get("name") or ""))
    if cid in {canonical_id(str(x)) for x in exclusions.get("provider_ids", [])}:
        return "explicitly excluded P2P/torrent provider id"
    metadata = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    for pattern in exclusions.get("metadata_patterns", []):
        if str(pattern).casefold() in metadata:
            return f"metadata contains excluded marker: {pattern}"
    script = data[:2_000_000].decode("utf-8", errors="ignore").casefold()
    for pattern in exclusions.get("script_patterns", []):
        if str(pattern).casefold() in script:
            return f"script contains excluded marker: {pattern}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument(
        "--include-file",
        type=Path,
        help="Optional JSON file containing target ids under a 'targets' array.",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    exclusions = sources.get("exclusions", {})
    included_ids: set[str] | None = None
    if args.include_file:
        include_payload = json.loads(args.include_file.resolve().read_text(encoding="utf-8"))
        raw_targets = include_payload.get("targets", include_payload if isinstance(include_payload, list) else [])
        included_ids = {
            canonical_id(str(item.get("id") if isinstance(item, dict) else item))
            for item in raw_targets
        }
    stage = args.stage.resolve()
    if stage.exists():
        shutil.rmtree(stage)
    providers_dir = stage / "providers" / "published"
    providers_dir.mkdir(parents=True)

    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for entry in manifest.get("scrapers", []):
        if not isinstance(entry, dict) or not entry.get("id") or not entry.get("filename"):
            continue
        source_path = (ROOT / str(entry["filename"])).resolve()
        if not is_under(source_path, ROOT / "providers") or not source_path.exists():
            continue
        data = source_path.read_bytes()
        reason = exclusion_reason(entry, data, exclusions)
        if reason:
            excluded.append({"id": str(entry["id"]), "reason": reason})
            continue
        cid = canonical_id(str(entry["id"]))
        if included_ids is not None and cid not in included_ids:
            continue
        destination = providers_dir / f"{safe_fragment(cid)}.js"
        destination.write_bytes(data)
        candidates.append(
            {
                "key": f"published:{cid}",
                "source": "published",
                "source_name": "Published manifest",
                "source_priority": 0,
                "source_repository": None,
                "source_license": "GPL-3.0-only",
                "upstream_id": str(entry["id"]),
                "canonical_id": cid,
                "local_path": str(destination.relative_to(stage)),
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "metadata": entry,
            }
        )

    registry = {
        "schema_version": 63,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "canonical_provider_count": len(candidates),
        "excluded_count": len(excluded),
        "excluded": excluded,
        "candidates": candidates,
    }
    (stage / "candidates.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    scope = "targeted" if included_ids is not None else "all published"
    print(f"Staged {len(candidates)} {scope} providers; excluded {len(excluded)} P2P/torrent entries.")
    return 0 if candidates or included_ids is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
