#!/usr/bin/env python3
"""Make AnimeVOSTFR anime-only and season/episode identity-safe.

The full32 comparator exposed a fake movie-positive: current upstream resolves
Superman (2025) through Neon Genesis Evangelion. NiakVIO must not preserve that
wrong-content lane. AnimeVOSTFR therefore publishes semantic anime only (TV is
transport alias at the provider edge), and the provider Lego rejects an explicit
season number that disagrees with the requested season.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
RUNTIME = ROOT / "scripts" / "provider_patches" / "animevostfr_runtime_v1.py"
SCRIPT = "scripts/provider_patches/animevostfr_runtime_v1.py"


def patch_runtime(text: str) -> str:
    old_req = 'if(raw==="series")raw="tv";if(raw!=="movie"&&raw!=="tv"&&raw!=="anime")return null;var id=txt((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||(typeof first==="string"?first:"")||ctx.tmdbId);if(!/^\\d+$/.test(id))return null;return{type:raw,transport:raw==="movie"?"movie":"tv",tmdbId:id,season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1}}'
    new_req = 'if(raw==="series"||raw==="tv")raw="anime";if(raw!=="anime")return null;var id=txt((obj&&(obj.tmdbId||obj.tmdb_id||obj.id))||(typeof first==="string"?first:"")||ctx.tmdbId);if(!/^\\d+$/.test(id))return null;return{type:"anime",transport:"tv",tmdbId:id,season:Number((obj&&obj.season)!=null?obj.season:args[2])||1,episode:Number((obj&&obj.episode)!=null?obj.episode:args[3])||1}}'
    if new_req not in text:
        if old_req not in text:
            raise SystemExit("AnimeVOSTFR request-lane anchor not found")
        text = text.replace(old_req, new_req, 1)

    old_score = 'function episodeScore(url,q){var s=String(q.season),e=String(q.episode),p=String(q.episode).padStart(2,"0"),u=txt(url).toLowerCase();if(new RegExp("-(?:saison-)?"+s+"-episode-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 300;if(new RegExp("-episode-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 180;if(new RegExp("-ep-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 120;return 0}'
    new_score = 'function episodeScore(url,q){var wantS=Number(q.season)||1,wantE=Number(q.episode)||1,u=txt(url).toLowerCase(),m=u.match(/-(\\d+)x(\\d+)(?:-|\\/|$)/i);if(m){var gotS=Number(m[1]),gotE=Number(m[2]);return gotS===wantS&&gotE===wantE?360:0}m=u.match(/-(?:saison-)?(\\d+)-episode-(\\d+)(?:-|\\/|$)/i);if(m){var gotS2=Number(m[1]),gotE2=Number(m[2]);return gotS2===wantS&&gotE2===wantE?340:0}var e=String(wantE),p=String(wantE).padStart(2,"0");if(new RegExp("-episode-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 180;if(new RegExp("-ep-(?:"+e+"|"+p+")(?:-|/|$)","i").test(u))return 120;return 0}'
    if new_score not in text:
        if old_score not in text:
            raise SystemExit("AnimeVOSTFR episode-score anchor not found")
        text = text.replace(old_score, new_score, 1)

    text = text.replace('"semanticLanes": ["movie", "anime"]', '"semanticLanes": ["anime"]')
    text = text.replace('"runtimeFamily": "wordpress-toroplay-trembed-v1"', '"runtimeFamily": "wordpress-toroplay-trembed-identity-v2"')
    return text


def main() -> int:
    before = RUNTIME.read_text(encoding="utf-8")
    after = patch_runtime(before)
    RUNTIME.write_text(after, encoding="utf-8")

    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    row = (data.get("provider_patches") or {}).get("animevostfr")
    if not isinstance(row, dict):
        raise SystemExit("animevostfr patch missing")

    row["published_types"] = ["anime"]
    scripts = [str(v) for v in (row.get("provider_lego_scripts") or []) if str(v)]
    if SCRIPT not in scripts:
        scripts.append(SCRIPT)
    row["provider_lego_scripts"] = scripts
    opts = row.get("provider_lego_options") if isinstance(row.get("provider_lego_options"), dict) else {}
    opts[SCRIPT] = {"base": "https://v2.animevostfr.org", "targetStreams": 3}
    row["provider_lego_options"] = opts
    row["route_data_state"] = "repair"
    row["route_proof_version"] = max(5, int(row.get("route_proof_version") or 0))
    notes = [str(v) for v in (row.get("notes") or []) if str(v)]
    additions = [
        "AnimeVOSTFR publishes semantic anime only; TV is transport alias. Movie support is intentionally not published after upstream Superman resolved through Neon Genesis Evangelion (identity contradiction).",
        "Episode identity V2 accepts explicit {season}x{episode} / {season}-episode-{episode} only when the season and episode both match; conflicting seasons fail closed.",
    ]
    for note in additions:
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
        "missingLanes": ["anime"],
        "completeCapabilityProof": False,
        "recoveryStatus": "anime-identity-v2-staged",
        "terminalState": None,
        "reasonCodes": ["anime_regression", "movie_identity_contradiction_removed", "season_identity_v2_staged"],
    })
    row["current_stream_proof"] = {
        "schemaVersion": 1,
        "movieLane": "identity_contradiction_not_capability",
        "animeLane": "repair_pending_exact_positive",
        "authority": "2026-09-13-upstream-output-integrity",
    }
    OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ANIMEVOSTFR_IDENTITY_V2_STAGED runtime_changed={after != before} published=anime movie=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
