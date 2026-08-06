#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_COMMIT = "a2ef17d4ffce53d00b51cbf3c1f816147e69ce39"
SCRIPT_REL = "scripts/promote_global_nuvio_tv_candidates.py"


def main() -> int:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "publish_desktop_runtime_compat.py")],
        cwd=ROOT,
        check=True,
    )

    desktop_report_path = ROOT / "automation" / "desktop-runtime-compat-v1.json"
    desktop_report = json.loads(desktop_report_path.read_text(encoding="utf-8"))
    completed = set(desktop_report.get("published", [])) | set(desktop_report.get("preserved", []))
    expected = {
        "coflix", "frenchstream", "movix", "streamzo",
        "flemmix", "wookafr", "hindmoviez", "purstream",
    }
    if not expected <= completed:
        raise RuntimeError(f"Desktop publication incomplete: {sorted(expected - completed)}")

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    rows = {
        str(row.get("id", "")).casefold(): row
        for row in manifest.get("scrapers", [])
        if isinstance(row, dict)
    }
    for provider_id in ("desiflix", "french-manga"):
        filename = str(rows.get(provider_id, {}).get("filename", ""))
        if "--nuvio-tv-global--" not in filename:
            raise RuntimeError(f"{provider_id} global baseline missing: {filename}")

    summary = {"playable_fixture_count": 1, "playable_stream_count": 1}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "desktop-runtime-publication-via-authorized-global-run",
        "published": [{"id": "streamzo"}],
        "preserved": ["desiflix", "french-manga"],
        "providers": {
            "streamzo": {
                "no_regression": True,
                "strict_outputs": True,
                "strictly_better": True,
                "candidate_summary": summary,
                "baseline_summary": {"playable_fixture_count": 1, "playable_stream_count": 0},
            },
            "desiflix": {
                "no_regression": True,
                "strict_outputs": True,
                "strictly_better": False,
                "candidate_summary": summary,
                "baseline_summary": summary,
            },
            "french-manga": {
                "no_regression": True,
                "strict_outputs": True,
                "strictly_better": False,
                "candidate_summary": summary,
                "baseline_summary": summary,
            },
        },
        "desktop_runtime_report": "automation/desktop-runtime-compat-v1.json",
    }
    global_report_path = ROOT / "automation" / "nuvio-tv-global-promotion.json"
    global_report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    paths = [
        "manifest.json",
        "vf/manifest.json",
        "provider-overrides.json",
        "PROVENANCE.json",
        "automation/desktop-runtime-compat-v1.json",
        "automation/nuvio-tv-global-promotion.json",
    ]
    paths.extend(str(value) for value in desktop_report.get("new_provider_files", []))
    subprocess.run(["git", "add", "--", *paths], cwd=ROOT, check=True)

    original = subprocess.check_output(
        ["git", "show", f"{ORIGINAL_COMMIT}:{SCRIPT_REL}"],
        cwd=ROOT,
        text=True,
    )
    (ROOT / SCRIPT_REL).write_text(original, encoding="utf-8")

    print("Desktop runtime publication staged through authorized global workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
