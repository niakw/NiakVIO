#!/usr/bin/env python3
"""Close artificial movie lanes for anime-only providers with proven anime evidence.

V35 is intentionally narrow in provider scope but generic in the declaration
surfaces it normalizes: publication, repair disposition, route authority and
live-route gate must all agree that Anime-Sama and MugiwaraStream are anime
providers. Historical wrong-content evidence is retained in laneStatuses.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
TARGETS = ("anime-sama", "mugiwarastream")
MARKER = "ANIME_ONLY_CAPABILITY_CLOSURE_V35"


def without_movie(values):
    if not isinstance(values, list):
        return values
    return [v for v in values if str(v).lower() != "movie"]


def ratio(required, validated):
    req = {str(x).lower() for x in required or []}
    val = {str(x).lower() for x in validated or []}
    return 1.0 if not req else len(req & val) / len(req)


def close_patch(patch: dict) -> None:
    patch["published_types"] = without_movie(patch.get("published_types", []))
    if "anime" not in patch["published_types"]:
        patch["published_types"].append("anime")
    notes = patch.setdefault("notes", [])
    note = f"{MARKER}: anime-only publication; movie wrong-content/unproven evidence cannot declare a movie lane."
    if note not in notes:
        notes.append(note)

    disposition = patch.get("repair_disposition")
    if isinstance(disposition, dict):
        disposition["requiredLanes"] = without_movie(disposition.get("requiredLanes", []))
        if "anime" not in disposition["requiredLanes"]:
            disposition["requiredLanes"].append("anime")
        disposition["missingLanes"] = without_movie(disposition.get("missingLanes", []))
        proven = {str(x).lower() for x in disposition.get("provenLanes", [])}
        required = {str(x).lower() for x in disposition.get("requiredLanes", [])}
        disposition["completeCapabilityProof"] = bool(required) and required.issubset(proven)
        # laneStatuses.movie is evidence (often wrong_content), not a declaration; preserve it.

    route_proof = patch.get("route_proof")
    if isinstance(route_proof, dict):
        authority = route_proof.get("canonicalExecutionAuthority")
        if isinstance(authority, dict):
            authority["supportedLanes"] = without_movie(authority.get("supportedLanes", []))
            authority["coveredLanes"] = without_movie(authority.get("coveredLanes", []))
            authority["missingLanes"] = without_movie(authority.get("missingLanes", []))
        prefs = route_proof.get("canonicalExecutionPreference")
        if isinstance(prefs, list):
            kept = []
            for item in prefs:
                if not isinstance(item, dict):
                    continue
                item["lanes"] = without_movie(item.get("lanes", []))
                if item["lanes"]:
                    kept.append(item)
            route_proof["canonicalExecutionPreference"] = kept
        route_proof["runtimePlanSemanticLanes"] = without_movie(route_proof.get("runtimePlanSemanticLanes", []))
        if "anime" not in route_proof["runtimePlanSemanticLanes"]:
            route_proof["runtimePlanSemanticLanes"].append("anime")

    gate = patch.get("live_route_gate")
    if isinstance(gate, dict):
        gate["required_types"] = without_movie(gate.get("required_types", []))
        if "anime" not in gate["required_types"]:
            gate["required_types"].append("anime")
        gate["validated_types"] = without_movie(gate.get("validated_types", []))
        gate["missing_types"] = without_movie(gate.get("missing_types", []))
        r = ratio(gate.get("required_types"), gate.get("validated_types"))
        gate["declared_type_coverage_ratio"] = r
        gate["effective_coverage_ratio"] = r
        gate["required_coverage_ratio"] = 1.0
        gate["completion_state"] = "declared-types-qualified" if r >= 1.0 else "declared-types-incomplete"


def main() -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = data.get("provider_patches") or {}
    missing = [pid for pid in TARGETS if pid not in patches]
    if missing:
        raise SystemExit(f"missing target provider patches: {missing}")
    for pid in TARGETS:
        close_patch(patches[pid])
    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{MARKER} providers={','.join(TARGETS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
