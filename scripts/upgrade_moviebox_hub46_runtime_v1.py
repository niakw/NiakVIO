#!/usr/bin/env python3
"""Install the Hub-46 MovieBox official H5 runtime without inventing proof.

The provider keeps TMDB as its public identity. The runtime obtains factual
metadata from Core when present, otherwise from the public TMDB title page, then
uses MovieBox's official H5 bootstrap/search/domain/play chain. Evidence stays
in repair until a live movie+TV proof promotes it separately.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
PATCH_SCRIPT = "scripts/provider_patches/moviebox_h5_runtime_v1.py"
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
            "apiBase": "https://h5-api.aoneroom.com/wefeed-h5api-bff",
            "siteOrigin": "https://moviebox.ph",
            "siteHost": "moviebox.ph",
            "requestTimeoutMs": 7000,
            "maxStreams": 8,
        }
    }
    p.setdefault("manifest_overrides", {})["enabled"] = True
    p.pop("quarantine_reason", None)
    p["route_data_state"] = "repair"

    old_notes = p.get("notes")
    if isinstance(old_notes, str):
        notes = [old_notes]
    elif isinstance(old_notes, list):
        notes = [x for x in old_notes if "Peach /moviebox" not in str(x)]
    else:
        notes = []
    note = (
        f"{MARKER}: official MovieBox H5 movie+TV runtime; TMDB input resolves "
        "through Core metadata or public TMDB title fallback; no embedded credential; "
        "live evidence required before promotion."
    )
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
    proof["lastRepairProbe"] = {
        "positiveExecutionEvidence": False,
        "status": "runtime-proof-required",
        "fixtureHardcodes": False,
        "embeddedCredential": False,
    }
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
        "route": "TMDB id -> Core/public TMDB title -> MovieBox official H5 BFF",
    }]

    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(MARKER, "installed=1 runtime=official-h5 proof=fresh-required lanes=movie,tv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
