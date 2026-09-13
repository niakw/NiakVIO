#!/usr/bin/env python3
"""Bind existing CDN/player runtimes that were authored but not materialized."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"

BINDINGS = {
    "animepahe": "scripts/provider_patches/animepahe_runtime_v1.py",
    "animevostfr": "scripts/provider_patches/animevostfr_runtime_v1.py",
}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    patches = data.setdefault("provider_patches", {})
    for provider_id, script in BINDINGS.items():
        row = patches.setdefault(provider_id, {})
        scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v)]
        if script not in scripts:
            scripts.append(script)
        row["provider_lego_scripts"] = scripts
        notes = [str(v) for v in (row.get("notes") or []) if str(v)]
        note = f"Durable runtime Lego bound after CDN transport audit: {script}."
        if note not in notes:
            notes.append(note)
        row["notes"] = notes

    vost = patches["animevostfr"]
    vost["published_types"] = ["anime"]
    disp = vost.get("repair_disposition")
    if isinstance(disp, dict):
        disp["requiredLanes"] = ["anime"]
        for key in ("currentVerifiedLanes", "exactLockedLanes", "provenLanes", "missingLanes"):
            values = disp.get(key)
            if isinstance(values, list):
                disp[key] = [v for v in values if str(v).lower() == "anime"]
        lane_statuses = disp.get("laneStatuses")
        if isinstance(lane_statuses, dict):
            disp["laneStatuses"] = {"anime": lane_statuses.get("anime", [])}

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CDN_RUNTIME_LEGO_BINDINGS_V1 animepahe=bound animevostfr=bound animevostfr_movie=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
