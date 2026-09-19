#!/usr/bin/env python3
"""Remove disproven semantic movie lanes from anime-first providers.

Anime-Sama and Mugiwara were declaring movie support while repair evidence
classified that lane as wrong-content/unproven.  Keep Nuvio's tv/series aliases
only as transport aliases for semantic anime; never advertise a movie lane that
cannot pass identity-safe proof.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.json"
TARGETS = {"anime-sama", "mugiwarastream"}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def uniq(values):
    out=[]
    for value in values or []:
        s=str(value or "").strip()
        if s and s not in out: out.append(s)
    return out


def main() -> int:
    data=json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches=data.get("provider_patches") or {}
    for provider_id in sorted(TARGETS):
        row=patches.get(provider_id)
        if not isinstance(row,dict):
            raise SystemExit(f"missing provider patch: {provider_id}")
        row["published_types"]=["anime"]
        notes=uniq(row.get("notes") or [])
        note="Semantic movie support removed: current repair evidence did not prove identity-safe movie output; TV/series remain transport aliases for anime only."
        if note not in notes: notes.append(note)
        row["notes"]=notes
        disp=row.get("repair_disposition")
        if not isinstance(disp,dict):
            disp={};row["repair_disposition"]=disp
        verified=[x for x in uniq(disp.get("currentVerifiedLanes") or []) if x!="movie"]
        proven=[x for x in uniq(disp.get("provenLanes") or []) if x!="movie"]
        disp["requiredLanes"]=["anime"]
        disp["currentVerifiedLanes"]=verified
        disp["provenLanes"]=proven
        disp["missingLanes"]=[] if "anime" in set(verified+proven) else ["anime"]
        disp["completeCapabilityProof"]=not disp["missingLanes"]
        disp["routeDataState"]="on" if disp["completeCapabilityProof"] else "repair"
        row["route_data_state"]=disp["routeDataState"]
        reasons=[x for x in uniq(disp.get("reasonCodes") or []) if x not in {"declared_lane_unproven","movie_wrong_content"}]
        if "movie_overdeclaration_removed" not in reasons: reasons.append("movie_overdeclaration_removed")
        disp["reasonCodes"]=reasons
        lane_statuses=disp.get("laneStatuses")
        if isinstance(lane_statuses,dict): lane_statuses.pop("movie",None)

    OVERRIDES.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    seen=set()
    for row in manifest.get("scrapers") or []:
        if not isinstance(row,dict): continue
        provider_id=cid(row.get("id"))
        if provider_id not in TARGETS: continue
        row["canonicalSupportedTypes"]=["anime"]
        row["supportedTypes"]=["anime","tv","series"]
        seen.add(provider_id)
    missing=TARGETS-seen
    if missing: raise SystemExit("manifest rows missing: "+",".join(sorted(missing)))
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ANIME_CAPABILITY_OVERDECLARATION_V1_OK targets=anime-sama,mugiwarastream semantic=anime movie=false")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
