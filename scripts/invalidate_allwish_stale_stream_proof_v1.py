#!/usr/bin/env python3
"""Invalidate stale AllWish playable-lane claims without deleting route evidence.

Current runner evidence is zero across the full global corpus, while historical
manual evidence showed fixture-invariant short wrong-content output. Keep the
provider catalogued/enabled by scope policy, but mark live capability unproven so
runtime remains fail-closed until a fresh identity-safe positive exists.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    row = (data.get("provider_patches") or {}).get("allwish")
    if not isinstance(row, dict):
        raise SystemExit("allwish patch missing")

    row["route_data_state"] = "repair"
    notes = row.get("notes") if isinstance(row.get("notes"), list) else []
    for note in [
        "Fresh 2026-09-13 adaptive corpus proof is zero on all declared lanes; previous playable_verified lane claims are invalidated.",
        "Historical manual cross-fixture evidence returned the same very short media for unrelated works, so it is wrong-content/fixture-invariant evidence, not a valid stream proof.",
        "Route knowledge is retained for diagnosis, but activation does not imply live capability proof; runtime must fail closed until fresh identity-safe media proof exists.",
    ]:
        if note not in notes:
            notes.append(note)
    row["notes"] = notes

    disp = row.get("repair_disposition")
    if not isinstance(disp, dict):
        disp = {}
        row["repair_disposition"] = disp
    disp.update({
        "routeDataState": "repair",
        "currentVerifiedLanes": [],
        "provenLanes": [],
        "missingLanes": ["movie", "tv"],
        "completeCapabilityProof": False,
        "recoveryStatus": "stale-stream-proof-invalidated",
        "terminalState": None,
        "quarantined": False,
        "reasonCodes": [
            "fresh_full_corpus_zero",
            "historical_wrong_content",
            "fixture_invariant_short_media",
            "stale_playable_verified_invalidated",
        ],
        "laneStatuses": {
            "movie": ["unproven", "fresh_corpus_zero", "historical_wrong_content"],
            "tv": ["unproven", "fresh_corpus_zero", "historical_wrong_content"],
        },
        "evidenceDestructive": False,
    })

    gate = row.get("live_route_gate")
    if isinstance(gate, dict):
        gate.update({
            "completion_state": "stream-capability-unproven",
            "effective_coverage_ratio": 0.0,
            "declared_type_coverage_ratio": 0.0,
            "validated_types": [],
            "missing_types": ["movie", "tv"],
        })

    row["current_stream_proof"] = {
        "schemaVersion": 1,
        "authority": "zero15-adaptive-2026-09-13",
        "streamPositive": False,
        "testedLanes": ["movie", "tv"],
        "globalCorpusExhausted": True,
        "historicalWrongContent": True,
        "requiresFreshIdentitySafePositive": True,
    }

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ALLWISH_STALE_STREAM_PROOF_INVALIDATED state=repair proven=0 missing=movie,tv route_evidence_preserved=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
