#!/usr/bin/env python3
"""Stage the two already-owned current-contract Legos for proven regressions.

AnimeVOSTFR and Kurage both have NiakVIO-owned provider-specific runtime Legos in
the repository, but current DATA no longer wires them. This migration restores
only provider-specific composition. Core keeps runtime/client compatibility,
timeout/cancellation, identity and final media fail-closed ownership.

Proof state intentionally remains ``repair`` until the dedicated workflow proves
all exact regression fixtures and recent-corpus parity.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"

PROVIDERS: dict[str, dict[str, Any]] = {
    "animevostfr": {
        "script": "scripts/provider_patches/animevostfr_runtime_v1.py",
        "options": {"base": "https://v2.animevostfr.org", "targetStreams": 3},
        "required": ["movie", "anime"],
        "routes": [
            "/?s={query}",
            "/animes/{slug}/",
            "/episode/{slug}-{season}-episode-{episode}/",
            "/?trembed={reader}&trid={id}&trtype=2",
        ],
        "note": "Current NiakVIO-owned WordPress/ToroPlay Lego restored for movie+anime regression proof; no upstream JavaScript is executed.",
    },
    "kurage": {
        "script": "scripts/provider_patches/kurage_runtime_v1.py",
        "options": {
            "base": "https://kurage.live",
            "anilist": "https://graphql.anilist.co",
            "trpcPath": "/api/trpc/catalog.anilistInfo,episodes.source,episodes.source",
            "targetStreams": 6,
        },
        "required": ["anime"],
        "routes": [
            "https://graphql.anilist.co",
            "/api/trpc/catalog.anilistInfo,episodes.source,episodes.source?batch=1&input={input}",
        ],
        "note": "Current NiakVIO-owned AniList+tRPC Lego restored for anime regression proof; no upstream JavaScript is executed.",
    },
}


def uniq(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        value = str(value or "").strip()
        if value and value not in out:
            out.append(value)
    return out


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    patches = data.get("provider_patches")
    if not isinstance(patches, dict):
        raise SystemExit("provider_patches missing")

    for provider_id, cfg in PROVIDERS.items():
        row = patches.get(provider_id)
        if not isinstance(row, dict):
            raise SystemExit(f"{provider_id}: patch missing")

        scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v)]
        if cfg["script"] not in scripts:
            scripts.append(cfg["script"])
        row["provider_lego_scripts"] = uniq(scripts)

        opts = row.get("provider_lego_options") if isinstance(row.get("provider_lego_options"), dict) else {}
        opts[cfg["script"]] = dict(cfg["options"])
        row["provider_lego_options"] = opts

        row["learned_routes"] = uniq(list(row.get("learned_routes") or []) + list(cfg["routes"]))
        row["candidate_learned_routes"] = uniq(list(row.get("candidate_learned_routes") or []) + list(cfg["routes"]))
        row["route_data_state"] = "repair"
        row["route_proof_version"] = max(5, int(row.get("route_proof_version") or 0))

        notes = [str(v) for v in (row.get("notes") or []) if str(v)]
        if cfg["note"] not in notes:
            notes.append(cfg["note"])
        row["notes"] = notes

        disp = row.get("repair_disposition")
        if not isinstance(disp, dict):
            disp = {}
            row["repair_disposition"] = disp
        disp.update({
            "routeDataState": "repair",
            "currentVerifiedLanes": [],
            "provenLanes": [],
            "missingLanes": list(cfg["required"]),
            "completeCapabilityProof": False,
            "recoveryStatus": "current-provider-lego-staged",
            "terminalState": None,
            "reasonCodes": ["certain_full32_regression", "current_provider_lego_staged"],
        })
        print(
            "REGRESSION_PAIR_LEGO_STAGED "
            f"provider={provider_id} script={cfg['script']} required={','.join(cfg['required'])}"
        )

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
