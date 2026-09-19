#!/usr/bin/env python3
"""Persist the authoritative AnimeVOSTFR semantic contract: anime only.

Transport aliases must not recreate a movie lane. This script only reconciles
provider metadata/repair state; it does not claim terminal playback proof.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"


def anime_only(values):
    if not isinstance(values, list):
        return values
    return [v for v in values if str(v).lower() == "anime"]


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    row = (data.get("provider_patches") or {}).get("animevostfr")
    if not isinstance(row, dict):
        raise SystemExit("animevostfr override missing")

    row["published_types"] = ["anime"]
    notes = [str(v) for v in (row.get("notes") or []) if str(v)]
    note = "Authoritative semantic contract is anime-only; movie must never be inferred from TV/transport aliases or historical route evidence."
    if note not in notes:
        notes.append(note)
    row["notes"] = notes

    disp = row.get("repair_disposition")
    if not isinstance(disp, dict):
        disp = {}
        row["repair_disposition"] = disp
    disp["requiredLanes"] = ["anime"]
    disp["currentVerifiedLanes"] = anime_only(disp.get("currentVerifiedLanes")) or []
    disp["exactLockedLanes"] = anime_only(disp.get("exactLockedLanes")) or []
    disp["provenLanes"] = anime_only(disp.get("provenLanes")) or []
    disp["missingLanes"] = [] if "anime" in disp["currentVerifiedLanes"] else ["anime"]
    disp["completeCapabilityProof"] = bool(disp["currentVerifiedLanes"] == ["anime"] and not disp["missingLanes"])
    lane_statuses = disp.get("laneStatuses")
    if isinstance(lane_statuses, dict):
        disp["laneStatuses"] = {"anime": lane_statuses.get("anime", [])}
    reasons = [str(v) for v in (disp.get("reasonCodes") or []) if str(v)]
    reasons = [v for v in reasons if "movie" not in v.lower()]
    if "movie_overdeclaration_removed" not in reasons:
        reasons.append("movie_overdeclaration_removed")
    disp["reasonCodes"] = reasons

    gate = row.get("live_route_gate")
    if isinstance(gate, dict):
        for key in ("required_types", "validated_types", "missing_types"):
            if isinstance(gate.get(key), list):
                gate[key] = anime_only(gate[key])

    proof = row.get("route_proof")
    if isinstance(proof, dict):
        for key in ("runtimePlanSemanticLanes",):
            if isinstance(proof.get(key), list):
                proof[key] = anime_only(proof[key])

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ANIMEVOSTFR_ANIME_ONLY_PERSISTED movie=false terminal_proof_unchanged=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
