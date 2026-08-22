#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Purify native-reader Brain sandbox candidates before official-client retest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from provider_purification import purify_file, sha256

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "native-reader-repair")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    report_path = output_dir / "repair-report.json"
    manifest_path = output_dir / "manifest.json"
    report = load_json(report_path)
    manifest = load_json(manifest_path)
    manifest_rows = {
        str(row.get("id") or "").casefold(): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }

    applied = 0
    bytes_saved = 0
    for proposal in report.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        provider = str(proposal.get("provider") or "").casefold().strip()
        candidate_file = str(proposal.get("candidateFile") or "").strip()
        if not provider or not candidate_file:
            continue
        path = (ROOT / candidate_file).resolve()
        path.relative_to(output_dir)
        before = path.read_bytes()
        expected = str(proposal.get("candidateSha256") or "")
        if expected and sha256(before) != expected:
            raise ValueError(f"reader repair hash mismatch before purification: {provider}")

        purification = purify_file(path)
        after = path.read_bytes()
        if purification["applied"]:
            applied += 1
            bytes_saved += int(purification["bytesSaved"])
            new_sha = sha256(after)
            new_path = path.with_name(f"{path.stem.split('--brain-reader--', 1)[0]}--brain-reader--{new_sha[:16]}.js")
            if new_path != path:
                if new_path.exists() and new_path.read_bytes() != after:
                    raise ValueError(f"reader repair purified filename collision: {new_path}")
                path.replace(new_path)
            relative = new_path.relative_to(ROOT).as_posix()
            proposal["candidateFile"] = relative
            proposal["candidateSha256"] = new_sha
            manifest_row = manifest_rows.get(provider)
            if manifest_row is not None:
                manifest_row["filename"] = relative
        proposal["purification"] = purification
        proposal["requiresFreshNativeReaderProof"] = True

    report["schemaVersion"] = max(4, int(report.get("schemaVersion") or 0))
    report["purification"] = {
        "phase": "provider-purification-v1",
        "tool": "terser",
        "toolVersion": "5.50.0",
        "mangle": False,
        "proposalCount": int(report.get("proposalCount") or 0),
        "appliedCount": applied,
        "bytesSaved": bytes_saved,
        "officialClientRetestRequired": True,
    }
    policy = report.setdefault("policy", {})
    if isinstance(policy, dict):
        policy["providerPurificationRequiredBeforeRetest"] = True
        policy["purificationMangleAllowed"] = False

    write_json(manifest_path, manifest)
    write_json(report_path, report)
    print(
        "FIELD_NATIVE_READER_REPAIR_PURIFICATION "
        f"proposals={report.get('proposalCount', 0)} applied={applied} bytes_saved={bytes_saved} "
        "mangle=false fresh_reader_retest_required=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
