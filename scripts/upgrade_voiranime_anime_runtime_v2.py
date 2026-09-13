#!/usr/bin/env python3
"""Stage current VoirAnime anime resolver on top of the existing movie resolver.

Script order is deliberate: movie V1 registers first, anime V2 captures/delegates
that resolver and then becomes the single provider hook seen by Core.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
MOVIE = "scripts/provider_patches/voiranime_homes_runtime_v1.py"
ANIME = "scripts/provider_patches/voiranime_anime_runtime_v2.py"


def uniq(values: list[str]) -> list[str]:
    out=[]
    for value in values:
        value=str(value or "").strip()
        if value and value not in out: out.append(value)
    return out


def main() -> int:
    data=json.loads(PATH.read_text(encoding="utf-8")); row=(data.get("provider_patches") or {}).get("voiranime")
    if not isinstance(row,dict): raise SystemExit("voiranime patch missing")
    scripts=[str(v) for v in (row.get("provider_lego_scripts") or []) if str(v)]
    scripts=[v for v in scripts if v not in {MOVIE,ANIME}]+[MOVIE,ANIME]
    row["provider_lego_scripts"]=uniq(scripts)
    opts=row.get("provider_lego_options") if isinstance(row.get("provider_lego_options"),dict) else {}
    opts.setdefault(MOVIE,{"movie_site":"https://voir-anime.to","max_streams":4})
    opts[ANIME]={"base":"https://voir-anime.to","maxStreams":4}
    row["provider_lego_options"]=opts
    routes=["/?s={query}","/anime/{slug}/","/anime/{slug}/{episode}/","/anime/{slug}/{episode}/?host={reader}"]
    row["learned_routes"]=uniq(list(row.get("learned_routes") or [])+routes)
    row["candidate_learned_routes"]=uniq(list(row.get("candidate_learned_routes") or [])+routes)
    row["route_data_state"]="repair"; row["route_proof_version"]=max(5,int(row.get("route_proof_version") or 0))
    notes=[str(v) for v in (row.get("notes") or []) if str(v)]
    note="VoirAnime anime V2 uses the current voir-anime.to series/chapter/LECTEUR contract and delegates non-anime requests to the existing movie resolver; Core owns terminal validation."
    if note not in notes: notes.append(note)
    row["notes"]=notes
    disp=row.get("repair_disposition")
    if not isinstance(disp,dict): disp={};row["repair_disposition"]=disp
    disp.update({"routeDataState":"repair","currentVerifiedLanes":[],"provenLanes":[],"missingLanes":["anime"],"completeCapabilityProof":False,"recoveryStatus":"current-anime-v2-staged","terminalState":None,"reasonCodes":["certain_full32_regression","current_anime_runtime_staged"]})
    PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("VOIRANIME_ANIME_V2_STAGED order="+",".join(row["provider_lego_scripts"]))
    return 0

if __name__=="__main__": raise SystemExit(main())
