#!/usr/bin/env python3
"""Bind authored CDN/player runtimes for providers still in the Hub46 catalogue.

Historical providers archived under provider-old/ must never be recreated in
provider-overrides.json by this migration helper.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"

BINDINGS = {
    "animevostfr": "scripts/provider_patches/animevostfr_runtime_v1.py",
}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def active_ids() -> set[str]:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    rows = matrix.get("rows") if isinstance(matrix.get("rows"), list) else []
    ids = {cid(row.get("registryId")) for row in rows if isinstance(row, dict) and cid(row.get("registryId"))}
    if int(matrix.get("hubCount") or 0) != 46 or len(ids) != 46:
        raise SystemExit(f"invalid Hub46 authority: count={matrix.get('hubCount')} ids={len(ids)}")
    return ids


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    patches = data.setdefault("provider_patches", {})
    active = active_ids()

    for provider_id, script in BINDINGS.items():
        if provider_id not in active:
            raise SystemExit(f"refusing to bind archived provider: {provider_id}")
        row = patches.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f"active provider missing from overrides; refusing implicit resurrection: {provider_id}")
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
    # Current clean runtime has proven only the anime semantic path. Keep movie
    # transport out of executable DATA until independent current proof exists.
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
    print("CDN_RUNTIME_LEGO_BINDINGS_V1 animevostfr=bound animevostfr_movie=false archived_resurrection=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
