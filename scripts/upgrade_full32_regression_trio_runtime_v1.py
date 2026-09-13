#!/usr/bin/env python3
"""Install the final clean-room runtime authority for the remaining full32 trio.

This migration is DATA-only. It wires NiakVIO-owned provider Lego and removes
stale execution authority that masked current proven routes. It never imports or
executes upstream JavaScript.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation/provider-v3-static-knowledge.json"
ANIMEVOST = "scripts/provider_patches/animevostfr_runtime_v1.py"
KURAGE = "scripts/provider_patches/kurage_runtime_v1.py"
OLD_VOIRANIME = "scripts/provider_patches/voiranime_homes_runtime_v1.py"


def uniq(values):
    out=[]
    for value in values or []:
        text=str(value or "").strip()
        if text and text not in out: out.append(text)
    return out


def set_lego(row: dict[str, Any], script: str, options: dict[str, Any]) -> None:
    scripts=uniq(row.get("provider_lego_scripts") or [])
    if script not in scripts: scripts.append(script)
    row["provider_lego_scripts"]=scripts
    opts=row.get("provider_lego_options") if isinstance(row.get("provider_lego_options"),dict) else {}
    opts[script]=options
    row["provider_lego_options"]=opts


def patch() -> bool:
    cfg=json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches=cfg.setdefault("provider_patches",{})
    caps=cfg.setdefault("provider_capabilities",{})
    before=json.dumps(cfg,ensure_ascii=False,sort_keys=True)

    a=patches["animevostfr"]
    a["official_site"]="https://v2.animevostfr.org"
    a["capability"]="mixed_embed_resolver"
    a["identity_input"]={"mode":"catalog_search","requires_tmdb_before_run":True,"required_fields":["title","mediaType"]}
    a["proof_search_bases"]=["https://v2.animevostfr.org"]
    a["learned_routes"]=[
        "https://v2.animevostfr.org/?s={query}",
        "https://v2.animevostfr.org/animes/{slug}/",
        "https://v2.animevostfr.org/episode/{slug}-{season}-episode-{episode}/",
        "https://v2.animevostfr.org/?trembed={id}&trid={id}&trtype=2",
    ]
    a["candidate_learned_routes"]=uniq(list(a.get("candidate_learned_routes") or [])+a["learned_routes"])
    for key in ("api_recipe","search_request_plan","provider_value_plan"):
        a.pop(key,None)
    set_lego(a,ANIMEVOST,{"base":"https://v2.animevostfr.org","targetStreams":3})
    ac=caps.setdefault("animevostfr",{})
    ac["strategy"]="mixed_embed_resolver"; ac["validation"]="provider_native"
    ac["observed_origins"]=uniq(["https://v2.animevostfr.org"]+list(ac.get("observed_origins") or []))

    k=patches["kurage"]
    k["official_site"]="https://kurage.live"
    k["capability"]="api_stream_resolver"
    k["identity_input"]={"mode":"tmdb_direct","requires_tmdb_before_run":True,"required_fields":["tmdbId","mediaType","season","episode"]}
    k["proof_search_bases"]=["https://kurage.live","https://graphql.anilist.co"]
    k["learned_routes"]=["https://graphql.anilist.co","https://kurage.live/api/trpc/catalog.anilistInfo,episodes.source,episodes.source?batch=1&input={input}"]
    k["candidate_learned_routes"]=uniq(list(k.get("candidate_learned_routes") or [])+k["learned_routes"])
    for key in ("api_recipe","search_request_plan","provider_value_plan"):
        k.pop(key,None)
    set_lego(k,KURAGE,{"base":"https://kurage.live","targetStreams":6})
    kc=caps.setdefault("kurage",{})
    kc["strategy"]="api_stream_resolver"; kc["validation"]="provider_native"
    kc["observed_origins"]=uniq(["https://kurage.live","https://graphql.anilist.co"]+list(kc.get("observed_origins") or []))

    v=patches["voiranime"]
    v["official_site"]="https://voir-anime.to"
    v["proof_search_bases"]=["https://voir-anime.to"]
    v["learned_routes"]=["https://voir-anime.to/anime/{slug}/"]
    v["candidate_learned_routes"]=uniq(list(v.get("candidate_learned_routes") or [])+v["learned_routes"])
    for key in ("search_request_plan","provider_value_plan","api_recipe"):
        v.pop(key,None)
    v["provider_lego_scripts"]=[x for x in uniq(v.get("provider_lego_scripts") or []) if OLD_VOIRANIME not in x]
    opts=v.get("provider_lego_options")
    if isinstance(opts,dict): opts.pop(OLD_VOIRANIME,None)
    for key in ("domain_substitutions","runtime_domain_replacements"):
        mapping=v.get(key)
        if isinstance(mapping,dict):
            for old in list(mapping):
                if "voiranime" in str(old).lower() or "voir-anime" in str(old).lower(): mapping[old]="voir-anime.to"
    vc=caps.setdefault("voiranime",{})
    vc["strategy"]="mixed_embed_resolver"; vc["validation"]="provider_native"
    vc["observed_origins"]=uniq(["https://voir-anime.to"]+list(vc.get("observed_origins") or []))

    after=json.dumps(cfg,ensure_ascii=False,sort_keys=True)
    if after!=before: OVERRIDES.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    knowledge=json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    providers=knowledge.setdefault("providers",{})
    specs={
        "animevostfr":("https://v2.animevostfr.org","mixed_embed_resolver",a["learned_routes"]),
        "kurage":("https://kurage.live","api_stream_resolver",k["learned_routes"]),
        "voiranime":("https://voir-anime.to","mixed_embed_resolver",v["learned_routes"]),
    }
    for pid,(site,strategy,routes) in specs.items():
        row=providers.setdefault(pid,{})
        model=row.setdefault("model",{})
        model["knownSite"]=site; model["officialSite"]=site; model["strategy"]=strategy
        model["origins"]=uniq([site]+list(model.get("origins") or []))
        model["routes"]=uniq(routes)
        model.pop("apiRecipe",None)
        if pid=="animevostfr": model["identityInput"]={"mode":"catalog_search","requiresTmdbBeforeRun":True,"requiredFields":["title","mediaType"]}
        elif pid=="kurage": model["identityInput"]={"mode":"tmdb_direct","requiresTmdbBeforeRun":True,"requiredFields":["tmdbId","mediaType","season","episode"]}
        else: model["identityInput"]={"mode":"catalog_search","requiresTmdbBeforeRun":True,"requiredFields":["title","mediaType"]}
    KNOWLEDGE.write_text(json.dumps(knowledge,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return after!=before


def validate() -> None:
    cfg=json.loads(OVERRIDES.read_text(encoding="utf-8")); p=cfg["provider_patches"]
    assert ANIMEVOST in p["animevostfr"].get("provider_lego_scripts",[])
    assert KURAGE in p["kurage"].get("provider_lego_scripts",[])
    assert p["voiranime"].get("official_site")=="https://voir-anime.to"
    assert "api_recipe" not in p["voiranime"]
    assert OLD_VOIRANIME not in p["voiranime"].get("provider_lego_scripts",[])
    assert p["kurage"].get("learned_routes",[])[0]=="https://graphql.anilist.co"


def main() -> int:
    changed=patch(); validate()
    print(f"FULL32_REGRESSION_TRIO_RUNTIME_V1_OK changed={str(changed).lower()} animevostfr=runtime_lego kurage=anilist_trpc voiranime=current_site_authority")
    return 0


if __name__=="__main__": raise SystemExit(main())
