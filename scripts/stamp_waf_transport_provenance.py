#!/usr/bin/env python3
"""Pin fresh WAF/residential observations to exact executed provider JS bytes.

This stamp is evidence-only. The durable WAF ledger retains older lanes by
design, so an unstamped or mismatched lane must not become *current* evidence
for Brain merely because an unrelated lane was refreshed later.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def published_bundle_digests(root: Path) -> dict[str, str]:
    """Resolve only local, owned JS paths, ignoring ambiguous mismatched rows."""
    root = root.resolve()
    digests: dict[str, str] = {}
    conflicts: set[str] = set()
    for manifest in (root / "manifest.json", root / "vf" / "manifest.json"):
        if not manifest.is_file():
            continue
        payload = _load(manifest)
        for row in payload.get("scrapers") or []:
            if not isinstance(row, dict):
                continue
            provider = _canon(row.get("id"))
            filename = str(row.get("filename") or "")
            if not provider or not filename or not filename.endswith(".js"):
                continue
            path = (manifest.parent / filename).resolve()
            if not path.is_relative_to(root):
                continue
            if not path.is_relative_to(root / "providers") and not path.is_relative_to(root / "provider-disabled"):
                continue
            if not path.is_file():
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if provider in digests and digests[provider] != digest:
                conflicts.add(provider)
            else:
                digests[provider] = digest
    for provider in conflicts:
        digests.pop(provider, None)
    return digests


def stamp_fresh(
    report: dict[str, Any],
    digests: dict[str, str],
    *,
    source_sha: str,
    run_id: str,
) -> dict[str, Any]:
    if not SHA40.fullmatch(source_sha) or not run_id.isdigit() or int(run_id) < 1:
        raise ValueError("WAF evidence requires a pinned 40-hex source SHA and positive run ID")
    out = copy.deepcopy(report)
    stamped: set[str] = set()

    def receipt(row: dict[str, Any]) -> dict[str, Any] | None:
        provider = _canon(row.get("provider"))
        digest = digests.get(provider)
        if not digest or not DIGEST.fullmatch(digest):
            return None
        stamped.add(provider)
        return {
            "sourceNiakvioSha": source_sha,
            "providerBundleSha256": digest,
            "runId": run_id,
            "proofAuthority": False,
            "publicationAuthority": False,
        }

    # These are only rows from the present WAF probe. The later durable
    # merge must not re-stamp older residential evidence it carries forward.
    for row in out.get("rows") or []:
        if not isinstance(row, dict):
            continue
        proof = receipt(row)
        if proof is None:
            continue
        row["transportReceipt"] = proof
        if isinstance(row.get("residentialExitNodeProfile"), dict):
            row["residentialReceipt"] = copy.deepcopy(proof)

    replay = out.get("residentialProviderReplay")
    if isinstance(replay, dict):
        for row in replay.get("rows") or []:
            if not isinstance(row, dict):
                continue
            proof = receipt(row)
            if proof is not None:
                row["residentialReplayReceipt"] = proof

    out["freshRunReceipt"] = {
        "sourceNiakvioSha": source_sha,
        "runId": run_id,
        "providerCount": len(stamped),
        "proofAuthority": False,
        "publicationAuthority": False,
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    report = stamp_fresh(
        _load(args.input),
        published_bundle_digests(args.repo_root),
        source_sha=args.source_sha.strip().casefold(),
        run_id=args.run_id.strip(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_WAF_EXACT_PROVIDER_PROVENANCE "
        f"run={args.run_id} providers={report['freshRunReceipt']['providerCount']} "
        "provider_mutation_authority=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
