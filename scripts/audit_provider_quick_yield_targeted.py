#!/usr/bin/env python3
"""Run canonical quick-yield for an explicit provider set, optionally repeatedly."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "audit_provider_quick_yield.py"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--attempts", type=int, default=2)
    args = parser.parse_args()

    selected = {
        str(v).strip().casefold()
        for v in load(Path(args.providers_json)).get("providers") or []
        if str(v).strip()
    }
    if not selected:
        Path(args.output).write_text(json.dumps({
            "provider_count": 0,
            "providers": [],
            "raw_providers": [],
            "playable_providers": [],
            "verified_providers": [],
            "wrong_content_providers": [],
            "rows": [],
        }, indent=2) + "\n", encoding="utf-8")
        print("TARGETED_YIELD_RETRY skipped=no_providers")
        return 0

    spec = importlib.util.spec_from_file_location("niakvio_quick_yield", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import quick-yield audit")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    attempts = max(1, min(int(args.attempts), 3))
    reports: list[dict] = []
    original_argv = list(sys.argv)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for attempt in range(1, attempts + 1):
                path = root / f"attempt-{attempt}.json"
                sys.argv = [str(BASE_PATH), "--scope", "all", "--output", str(path)]
                for provider in sorted(selected):
                    sys.argv.extend(["--provider", provider])
                print(
                    f"TARGETED_YIELD_RETRY attempt={attempt}/{attempts} "
                    f"providers={','.join(sorted(selected))}"
                )
                rc = mod.main()
                if rc != 0:
                    raise SystemExit(rc)
                report = load(path)
                present = {
                    str(row.get("provider_id") or "").strip().casefold()
                    for row in report.get("rows") or []
                    if isinstance(row, dict) and str(row.get("provider_id") or "").strip()
                }
                missing = sorted(selected - present)
                if missing:
                    raise RuntimeError(
                        "selected providers missing from current manifest/replay: " + ",".join(missing)
                    )
                reports.append(report)
    finally:
        sys.argv = original_argv

    def union(key: str) -> list[str]:
        values: set[str] = set()
        for report in reports:
            values.update(
                str(v).strip().casefold()
                for v in report.get(key) or []
                if str(v).strip()
            )
        return sorted(values)

    merged = {
        "schema_version": 2,
        "environment": "targeted-canonical-quick-yield-union",
        "provider_count": len(selected),
        "attempts": attempts,
        "providers": sorted(selected),
        "raw_providers": union("raw_providers"),
        "playable_providers": union("playable_providers"),
        "accepted_playable_providers": union("accepted_playable_providers"),
        "verified_providers": union("verified_providers"),
        "wrong_content_providers": union("wrong_content_providers"),
        "rows": [
            row
            for report in reports
            for row in report.get("rows") or []
            if isinstance(row, dict)
        ],
    }
    Path(args.output).write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "TARGETED_YIELD_RETRY_DONE "
        f"providers={len(selected)} attempts={attempts} raw={len(merged['raw_providers'])} "
        f"playable={len(merged['playable_providers'])} verified={len(merged['verified_providers'])} "
        f"wrong={len(merged['wrong_content_providers'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
