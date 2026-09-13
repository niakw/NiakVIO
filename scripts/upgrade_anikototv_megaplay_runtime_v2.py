#!/usr/bin/env python3
"""Switch AniKotoTV to the current AJAX + MegaPlay extraction contract.

Proof state stays `repair` until the workflow demonstrates a terminal playable media
URL. This migration changes provider-specific DATA/Lego only; Core ownership is
untouched.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
V1 = "scripts/provider_patches/anikototv_runtime_v1.py"
V2 = "scripts/provider_patches/anikototv_runtime_v2.py"


def unique(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        value = str(value or "").strip()
        if value and value not in out:
            out.append(value)
    return out


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("anikototv"), dict):
        raise SystemExit("anikototv provider patch missing")
    row = patches["anikototv"]

    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v)]
    scripts = [v for v in scripts if v != V1]
    if V2 not in scripts:
        scripts.append(V2)
    row["provider_lego_scripts"] = unique(scripts)

    opts = row.get("provider_lego_options") if isinstance(row.get("provider_lego_options"), dict) else {}
    old = opts.get(V1) if isinstance(opts.get(V1), dict) else {}
    mirrors = old.get("mirrors") if isinstance(old.get("mirrors"), list) else [
        "https://anikototv.to",
        "https://anikoto.cz",
        "https://anikoto.me",
        "https://anikoto.net",
        "https://anikototv.se",
    ]
    opts.pop(V1, None)
    opts[V2] = {"mirrors": mirrors}
    row["provider_lego_options"] = opts

    row["route_data_state"] = "repair"
    row["route_proof_version"] = max(5, int(row.get("route_proof_version") or 0))
    row["learned_routes"] = [
        "/ajax/anime/search?keyword={query}",
        "/watch/{slug}",
        "/ajax/episode/list/{id}",
        "/ajax/server/list?servers={id}",
        "/ajax/server?get={id}",
        "https://megaplay.buzz/stream/getSources?id={id}",
    ]
    row["candidate_learned_routes"] = unique(
        list(row["learned_routes"])
        + [str(v) for v in (row.get("candidate_learned_routes") or []) if str(v) and "/search?keyword=" not in str(v)]
    )
    notes = row.get("notes") if isinstance(row.get("notes"), list) else []
    notes = [str(v) for v in notes if str(v)]
    notes.extend([
        "Current AniKotoTV search is /ajax/anime/search?keyword={query}; response JSON result.html is the candidate catalogue.",
        "Current terminal player path resolves MegaPlay embed title File {id} then /stream/getSources?id={id}; only its final media source may be emitted.",
        "Provider-specific extraction lives in AniKoto V2; Core remains owner of timeout/cancellation, identity and terminal media fail-closed validation.",
    ])
    row["notes"] = unique(notes)

    disp = row.get("repair_disposition")
    if isinstance(disp, dict):
        disp.update({
            "routeDataState": "repair",
            "completeCapabilityProof": False,
            "recoveryStatus": "anikoto-megaplay-v2-staged",
            "currentVerifiedLanes": [],
            "provenLanes": [],
            "missingLanes": ["anime"],
            "reasonCodes": ["current_contract_staged", "terminal_player_resolution_required"],
        })

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "ANIKOTOTV_MEGAPLAY_RUNTIME_V2_STAGED "
        f"scripts={','.join(row['provider_lego_scripts'])} routes={len(row['learned_routes'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
