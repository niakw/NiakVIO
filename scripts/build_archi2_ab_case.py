#!/usr/bin/env python3
"""Build one identical native-client fixture for pre/post ARCHI2 roots.

Provider selection is expanded independently from each manifest using the exact
same current selection helper: every enabled provider compatible with the
fixture category is exercised. The fixture, policy, timeouts and client list are
otherwise identical.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_nuvio_client_lab_matrix import expand_push_source  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def one_case(source: dict[str, Any], manifest: dict[str, Any], slug: str) -> dict[str, Any]:
    expanded = expand_push_source(source, manifest)
    row = next((item for item in expanded.get("fixtures") or [] if item.get("slug") == slug), None)
    if row is None:
        raise SystemExit(f"fixture not found: {slug}")
    common = {key: value for key, value in source.items() if key != "fixtures"}
    case = dict(common)
    case.update({key: value for key, value in row.items() if key != "slug"})
    case["audit_slug"] = slug
    case["provider_selection"] = "all_enabled_compatible"
    case["manifest_enabled_compatible_count"] = len(case.get("providers") or [])
    case["enforce_policy"] = False
    return case


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    source = load(args.source)
    baseline_manifest = load(args.baseline_manifest)
    candidate_manifest = load(args.candidate_manifest)
    baseline = one_case(source, baseline_manifest, args.slug)
    candidate = one_case(source, candidate_manifest, args.slug)
    baseline["audit_generation"] = "pre_archi2"
    candidate["audit_generation"] = "archi2"

    out = args.output_dir.resolve()
    write(out / "baseline-config.json", baseline)
    write(out / "candidate-config.json", candidate)
    write(
        out / "selection.json",
        {
            "slug": args.slug,
            "baseline_manifest_version": baseline_manifest.get("version"),
            "candidate_manifest_version": candidate_manifest.get("version"),
            "baseline_enabled_compatible": len(baseline.get("providers") or []),
            "candidate_enabled_compatible": len(candidate.get("providers") or []),
            "baseline_provider_ids": baseline.get("providers") or [],
            "candidate_provider_ids": candidate.get("providers") or [],
        },
    )
    print(
        f"ARCHI2 A/B case {args.slug}: "
        f"baseline={len(baseline.get('providers') or [])} candidate={len(candidate.get('providers') or [])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
