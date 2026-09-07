#!/usr/bin/env python3
"""Inspect targeted materialized bundles for structured repair-plan projection.

Diagnostic only. This does not alter provider DATA or publication state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    args = parser.parse_args()

    manifest = load(MANIFEST)
    rows = {
        cid(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    }
    overrides = load(OVERRIDES)
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    failed: list[str] = []

    for raw in args.provider:
        provider = cid(raw)
        row = rows.get(provider) or {}
        patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
        filename = str(row.get("filename") or "")
        path = ROOT / filename
        if not filename or not path.exists():
            failed.append(provider + ":bundle-missing")
            continue
        text = path.read_text(encoding="utf-8")
        plans = patch.get("search_request_plan") if isinstance(patch.get("search_request_plan"), list) else []
        expected_bases = [str(plan.get("base") or "").strip() for plan in plans if isinstance(plan, dict) and str(plan.get("base") or "").strip()]
        marker = '"searchRequestPlan"' in text
        projected_bases = [base for base in expected_bases if base in text]
        print(
            "FIELD_PROVIDER_FAST_BUNDLE_PLAN "
            f"provider={provider} file={filename} expected_search_plan={len(plans)} "
            f"marker={str(marker).lower()} projected_bases={len(projected_bases)}/{len(expected_bases)} "
            f"bases={','.join(expected_bases)}",
            flush=True,
        )
        if plans and (not marker or len(projected_bases) != len(expected_bases)):
            failed.append(provider + ":search-plan-not-projected")

    if failed:
        raise SystemExit("materialized structured-plan projection failed: " + ",".join(failed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
