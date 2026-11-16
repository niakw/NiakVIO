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

from build_published_provider_stage import projection_rows

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


def targeted_projection_entries(
    included_ids: set[str],
    *,
    manifest_path: Path,
    france_manifest_path: Path,
) -> list[dict[str, Any]]:
    """Resolve explicit Brain targets from the executable Global+France union.

    The census/Brain queue is projection-union aware. Targeted staging must use
    the same identity authority or France-only providers can be selected and
    then silently disappear before the Brain sees their exact published bytes.
    """
    by_id = projection_rows(manifest_path, france_manifest_path)
    missing = sorted(included_ids - set(by_id))
    if missing:
        raise SystemExit(
            "targeted published stage missing requested projection ids: "
            + ",".join(missing)
        )
    entries: list[dict[str, Any]] = []
    for provider in sorted(included_ids):
        row = dict(by_id[provider])
        filename = str(row.get("filename") or "").strip()
        if row.get("enabled") is False or not filename.startswith("providers/"):
            raise SystemExit(
                f"{provider}: requested provider is not active published Provider v3"
            )
        entries.append(row)
    return entries


def is_niakvio_owned_v3(data: bytes) -> bool:
    """Return whether this provider is a NiakVIO-owned ProviderBase v3 bundle.

    ProviderBase intentionally contains generic P2P rejection code (for example
    ``infoHash``/``magnet`` guards) in every generated provider. Those shared
    safety markers must never make the availability stager classify the entire
    catalogue as P2P. Provider identity/metadata exclusions remain authoritative;
    script scanning is retained for legacy/non-owned provider code.
    """
    head = data[:256_000].decode("utf-8", errors="ignore")
    return "NIAKVIO_PROVIDER_BASE_OWNED_V3" in head


def exclusion_reason(entry: dict[str, Any], data: bytes, exclusions: dict[str, Any]) -> str | None:
    cid = canonical_id(str(entry.get("id") or entry.get("name") or ""))
    if cid in {canonical_id(str(x)) for x in exclusions.get("provider_ids", [])}:
        return "explicitly excluded P2P/torrent provider id"
    metadata = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    for pattern in exclusions.get("metadata_patterns", []):
        if str(pattern).casefold() in metadata:
            return f"metadata contains excluded marker: {pattern}"
    if not is_niakvio_owned_v3(data):
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
    parser.add_argument(
        "--projection-union",
        action="store_true",
        help="Stage every active Global + France-only provider instead of the legacy Global-only default.",
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
    if included_ids is not None:
        entries = targeted_projection_entries(
            included_ids,
            manifest_path=MANIFEST_PATH,
            france_manifest_path=ROOT / "vf" / "manifest.json",
        )
    elif args.projection_union:
        entries = [
            row
            for row in projection_rows(MANIFEST_PATH, ROOT / "vf" / "manifest.json").values()
            if isinstance(row, dict) and row.get("enabled") is not False
        ]
    else:
        entries = [row for row in manifest.get("scrapers", []) if isinstance(row, dict)]
    for entry in entries:
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

    if included_ids is not None:
        staged_ids = {canonical_id(str(row.get("canonical_id") or "")) for row in candidates}
        missing_staged = sorted(included_ids - staged_ids)
        if missing_staged:
            raise SystemExit(
                "targeted published stage failed to materialize requested ids: "
                + ",".join(missing_staged)
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
    scope = "targeted" if included_ids is not None else ("projection-union" if args.projection_union else "all published")
    print(f"Staged {len(candidates)} {scope} providers; excluded {len(excluded)} P2P/torrent entries.")
    return 0 if candidates or included_ids is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
