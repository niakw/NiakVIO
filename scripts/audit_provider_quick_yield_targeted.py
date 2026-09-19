#!/usr/bin/env python3
"""Retry quick-yield only for providers lost by a before/after preservation comparison."""
from __future__ import annotations

import argparse
import importlib.util
import json
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
            "raw_providers": [],
            "playable_providers": [],
            "verified_providers": [],
            "wrong_content_providers": [],
            "rows": [],
        }, indent=2) + "\n", encoding="utf-8")
        print("TARGETED_YIELD_RETRY skipped=no_losses")
        return 0

    spec = importlib.util.spec_from_file_location("niakvio_quick_yield", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import quick-yield audit")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    original_build = mod.build_tasks

    def filtered_build_tasks():
        tasks, _provider_count = original_build()
        filtered = [row for row in tasks if str(row.get("provider_id") or "").casefold() in selected]
        present = {str(row.get("provider_id") or "").casefold() for row in filtered}
        missing = sorted(selected - present)
        if missing:
            raise RuntimeError("selected providers missing from current manifest: " + ",".join(missing))
        return filtered, len(present)

    mod.build_tasks = filtered_build_tasks
    attempts = max(1, min(int(args.attempts), 3))
    reports: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for attempt in range(1, attempts + 1):
            path = root / f"attempt-{attempt}.json"
            mod.OUTPUT = path
            print(f"TARGETED_YIELD_RETRY attempt={attempt}/{attempts} providers={','.join(sorted(selected))}")
            rc = mod.main()
            if rc != 0:
                raise SystemExit(rc)
            reports.append(load(path))

    def union(key: str) -> list[str]:
        values: set[str] = set()
        for report in reports:
            values.update(str(v).strip().casefold() for v in report.get(key) or [] if str(v).strip())
        return sorted(values)

    merged = {
        "schema_version": 1,
        "environment": "targeted-retry-union-of-quick-yield-attempts",
        "provider_count": len(selected),
        "attempts": attempts,
        "providers": sorted(selected),
        "raw_providers": union("raw_providers"),
        "playable_providers": union("playable_providers"),
        "verified_providers": union("verified_providers"),
        "wrong_content_providers": union("wrong_content_providers"),
        "rows": [row for report in reports for row in report.get("rows") or [] if isinstance(row, dict)],
    }
    Path(args.output).write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "TARGETED_YIELD_RETRY_DONE "
        f"providers={len(selected)} attempts={attempts} raw={len(merged['raw_providers'])} "
        f"playable={len(merged['playable_providers'])} verified={len(merged['verified_providers'])} "
        f"wrong={len(merged['wrong_content_providers'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
