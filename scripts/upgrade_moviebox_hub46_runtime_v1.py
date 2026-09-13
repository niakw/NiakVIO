#!/usr/bin/env python3
"""Install the Hub-46 MovieBox TMDB-direct runtime without inventing proof.

The migration removes the stale HTML-player quarantine and replaces it with a
single attributable MovieBox Peach runtime. Evidence fields stay in repair
until the live movie+TV probe promotes them in a separate evidence step.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
PATCH_SCRIPT = "scripts/provider_patches/moviebox_peach_runtime_v1.py"
MARKER = "MOVIEBOX_HUB46_RUNTIME_V1"


def main() -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = data.setdefault("provider_patches", {})
    p = patches.get("moviebox")
    if not isinstance(p, dict):
        raise SystemExit("moviebox patch missing")

    p["capability"] = "direct_media"
    p["published_types"] = ["movie", "tv"]
    p["provider_lego_scripts"] = [PATCH_SCRIPT]
    p["provider_lego_options"] = {
        PATCH_SCRIPT: {
            "origin": "https://peachify.top",
            "referer": "https://peachify.top/",
            "servers": [
                {"label": "MovieBox", "base": "https://uwu.eat-peach.sbs", "path": "moviebox"}
            ],
        }
    }
    p.setdefault("manifest_overrides", {})["enabled"] = True
    p.pop("quarantine_reason", None)
    p["route_data_state"] = "repair"

    old_notes = p.get("notes")
    if isinstance(old_notes, str):
        notes = [old_notes]
    elif isinstance(old_notes, list):
        notes = list(old_notes)
    else:
        notes = []
    note = f"{MARKER}: use attributable Peach /moviebox TMDB-direct movie+TV runtime; live evidence required before promotion."
    if note not in notes:
        notes.append(note)
    p["notes"] = notes

    disp = p.setdefault("repair_disposition", {})
    disp.update({
        "activationAuthority": "hub-lab-matrix-46",
        "activationState": "enabled",
        "forcedEnabled": True,
        "quarantined": False,
        "requiredLanes": ["movie", "tv"],
        "currentVerifiedLanes": [],
        "provenLanes": [],
        "missingLanes": ["movie", "tv"],
        "completeCapabilityProof": False,
        "routeDataState": "repair",
        "recoveryStatus": "runtime-proof-required",
    })
    reasons = [x for x in disp.get("reasonCodes", []) if x not in {"explicit_quarantine", "recovery_no-proven-route"}]
    if "runtime-proof-required" not in reasons:
        reasons.append("runtime-proof-required")
    disp["reasonCodes"] = reasons

    gate = p.setdefault("live_route_gate", {})
    gate.update({
        "required_types": ["movie", "tv"],
        "validated_types": [],
        "missing_types": ["movie", "tv"],
        "declared_type_coverage_ratio": 0.0,
        "effective_coverage_ratio": 0.0,
        "required_coverage_ratio": 1.0,
        "completion_state": "runtime-proof-required",
        "declared_types_are_gate_denominator": True,
    })

    proof = p.setdefault("route_proof", {})
    proof["runtimePlanSemanticLanes"] = ["movie", "tv"]
    proof["lastRepairProbe"] = {"positiveExecutionEvidence": False, "status": "runtime-proof-required"}
    authority = proof.setdefault("canonicalExecutionAuthority", {})
    authority.update({
        "supportedLanes": ["movie", "tv"],
        "coveredLanes": [],
        "missingLanes": ["movie", "tv"],
        "owners": ["provider_lego"],
        "preferredOwners": ["provider_lego"],
    })
    proof["canonicalExecutionPreference"] = [{
        "index": 0,
        "lanes": ["movie", "tv"],
        "owner": "provider_lego",
        "route": "https://uwu.eat-peach.sbs/moviebox/{type}/{tmdbId}",
    }]

    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(MARKER, "installed=1 proof=fresh-required lanes=movie,tv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
