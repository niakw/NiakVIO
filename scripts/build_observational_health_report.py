#!/usr/bin/env python3
"""Convert raw health observations into a non-mutating published-provider report."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def language_group(evidence:dict)->str:
    audio={str(v).casefold() for v in evidence.get("audio_languages") or []}
    subs={str(v).casefold() for v in evidence.get("subtitle_languages") or []}
    declared={str(v).casefold() for v in evidence.get("manifest_accepted_languages") or []}
    if "fr" in audio: return "vf"
    if "fr" in subs: return "vostfr"
    if "fr" in declared: return "fr_unspecified"
    return "other"

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--results",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=ROOT/"manifest.json")
    p.add_argument("--output",type=Path,default=ROOT/"health-report.json")
    args=p.parse_args()
    raw=json.loads(args.results.read_text(encoding="utf-8"))
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    manifest_by={str(r.get("id") or "").casefold():r for r in manifest.get("scrapers") or [] if isinstance(r,dict)}
    providers=[]
    for item in raw.get("results") or []:
        pid=str(item.get("canonical_id") or "").casefold()
        row=manifest_by.get(pid,{})
        ev=item.get("evidence") if isinstance(item.get("evidence"),dict) else {}
        providers.append({
            "id":pid,
            "enabled":bool(row.get("enabled",True)),
            "action":"observed-published-v3-no-mutation",
            "status":item.get("status"),
            "score":item.get("score"),
            "health":{
                "status":item.get("status"),
                "score":item.get("score"),
                "evidence":ev,
            },
            "manifest_ordering":{
                "language_group":language_group(ev),
                "quality_height":ev.get("effective_max_height"),
            },
            "repair_attempted":False,
            "provider_mutation_allowed":False,
        })
    report={
        "schema_version":68,
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "test_environment":"github-actions-node",
        "test_mode":raw.get("mode"),
        "published_providers":len(providers),
        "candidate_variants_checked":len(providers),
        "status_counts":raw.get("counts") or {},
        "policy":{
            "published_provider_observation_only":True,
            "quick_and_deep_repair_allowed":False,
            "provider_fix_mutation_allowed":False,
            "learning_is_exclusive_repair_owner":True,
        },
        "providers":providers,
    }
    if len(providers)!=96:
        raise SystemExit(f"observation report incomplete: {len(providers)} != 96")
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"FIELD_PROVIDER_OBSERVATION_REPORT mode={raw.get('mode')} providers={len(providers)} repair=false")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
