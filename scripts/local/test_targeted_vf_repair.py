#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "local-output" / "targeted-vf-repair"
STAGE = BASE / "staging"
OUT = BASE / "health-output"
TARGETS = BASE / "targets.json"
IDS = [
    "coflix",
    "dulourd",
    "french-manga",
    "frenchstream",
    "movix",
    "sekai",
    "streamzo",
]


def run(*args: object) -> None:
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run([str(value) for value in args], cwd=ROOT, check=True)


def main() -> int:
    if BASE.exists():
        shutil.rmtree(BASE)
    BASE.mkdir(parents=True)
    TARGETS.write_text(json.dumps({"targets": IDS}, indent=2) + "\n", encoding="utf-8")

    run(sys.executable, ROOT / "scripts" / "stage_published.py", "--stage", STAGE, "--include-file", TARGETS)
    run(sys.executable, ROOT / "scripts" / "build_provider_runtime_profiles.py", "--stage", STAGE, "--apply-stage")
    run(sys.executable, ROOT / "scripts" / "validate_override_pipeline.py", "--stage", STAGE)
    run(sys.executable, ROOT / "scripts" / "deep_repair_loop.py", "--stage", STAGE, "--output", OUT, "--mode", "deep")

    repair = json.loads((OUT / "repair-report.json").read_text(encoding="utf-8"))
    health_path = OUT / "health-results.json"
    health = json.loads(health_path.read_text(encoding="utf-8")) if health_path.exists() else {}
    summary = {
        "targets": IDS,
        "generated_candidates": repair.get("generated_candidates", 0),
        "accepted_repairs": repair.get("accepted_repairs", 0),
        "status_counts": health.get("counts", {}),
        "rounds": repair.get("rounds", []),
        "publication_performed": False,
    }
    (BASE / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Targeted VF repair complete: {summary['accepted_repairs']} accepted repair(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
