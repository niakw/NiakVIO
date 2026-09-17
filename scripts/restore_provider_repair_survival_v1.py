#!/usr/bin/env python3
"""Restore provider repair authority that was proven on #122 but lost before publication.

This transaction restores only durable Provider Lego/config authority. Historical
positive lane evidence is NOT copied forward: every restored provider is marked
for exact-bundle re-proof after rematerialization.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
OVERRIDES=ROOT/"provider-overrides.json"

LOST={
    "allanime":{"scripts":["scripts/provider_patches/allanime_current_runtime_v1.py"]},
    "allwish":{"scripts":["scripts/provider_patches/allwish_current_runtime_v1.py"],"published_types":["anime"]},
    "anikototv":{
        "replace":{"scripts/provider_patches/anikototv_runtime_v2.py":"scripts/provider_patches/anikototv_runtime_v3.py"},
        "scripts":["scripts/provider_patches/anikototv_runtime_v3.py"],
        "options":{"scripts/provider_patches/anikototv_runtime_v3.py":{"mirrors":["https://anikototv.to","https://anikoto.cz","https://anikoto.me","https://anikoto.net","https://anikototv.se"]}}
    },
    "flemmix":{"scripts":["scripts/provider_patches/flemmix_current_runtime_v1.py"]},
    "moviebox":{"scripts":["scripts/provider_patches/moviebox_current_embed_v2.py"]},
    "vidfast":{"scripts":["scripts/provider_patches/vidfast_current_embed_v1.py"]},
    "vidlove":{"scripts":["scripts/provider_patches/vidlove_current_api_v1.py"]},
    "wookafr":{
        "scripts":[
            "scripts/provider_patches/wookafr_lecteurvideo_priority_v1.py",
            "scripts/provider_patches/wookafr_showvideo_base64_v1.py",
            "scripts/provider_patches/wookafr_current_runtime_v2.py"
        ],
        "options":{
            "scripts/provider_patches/wookafr_lecteurvideo_priority_v1.py":{"priority_host":"lecteurvideo.com"},
            "scripts/provider_patches/wookafr_current_runtime_v2.py":{}
        }
    },
    "yflix":{"scripts":["scripts/provider_patches/yflix_current_runtime_v2.py"],"options":{"scripts/provider_patches/yflix_current_runtime_v2.py":{}}}
}
NONDISPLAY_PROVIDERS={
    "animesama-co": {
        "script": "scripts/provider_patches/animesamaco_nondisplay_runtime_v1.py",
        "provider": "animesama-co",
        "base": "https://animesama.co",
        "max_streams": 4
    },
    "animevostfr": {
        "script": "scripts/provider_patches/animevostfr_nondisplay_runtime_v1.py",
        "provider": "animevostfr",
        "base": "https://v2.animevostfr.org",
        "max_streams": 4
    },
    "coflix": {
        "script": "scripts/provider_patches/coflix_nondisplay_runtime_v1.py",
        "provider": "coflix",
        "base": "https://coflix.wiki",
        "max_streams": 4
    },
    "neko-sama": {
        "script": "scripts/provider_patches/neko_sama_nondisplay_runtime_v1.py",
        "provider": "neko-sama",
        "base": "https://animes-sama.su",
        "max_streams": 4
    },
    "sekai": {
        "script": "scripts/provider_patches/sekai_nondisplay_runtime_v1.py",
        "provider": "sekai",
        "base": "https://sekai.one",
        "max_streams": 4
    },
    "voiranime-rip": {
        "script": "scripts/provider_patches/voiranime_rip_nondisplay_runtime_v1.py",
        "provider": "voiranime-rip",
        "base": "https://voiranime.rip",
        "max_streams": 4
    }
}

def unique(values):
    out=[]
    for v in values:
        if v and v not in out: out.append(v)
    return out

def mark_reproof(row:dict[str,Any])->None:
    disp=row.setdefault("repair_disposition",{})
    required=list(row.get("published_types") or disp.get("requiredLanes") or [])
    disp["requiredLanes"]=required
    disp["currentVerifiedLanes"]=[]
    disp["provenLanes"]=[]
    disp["missingLanes"]=required
    disp["completeCapabilityProof"]=False
    disp["recoveryStatus"]="repair-reproof-required"
    reasons=[str(x) for x in disp.get("reasonCodes") or [] if str(x)]
    reasons=[x for x in reasons if not x.startswith("v3") and not x.startswith("v4") and "live_terminal_proven" not in x and "playback_proven" not in x]
    reasons.append("repair_survival_restored_requires_exact_bundle_reproof")
    disp["reasonCodes"]=unique(reasons)
    disp["evidenceDestructive"]=False

def main()->int:
    doc=json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches=doc.setdefault("provider_patches",{})
    changed=[]
    for provider,cfg in NONDISPLAY_PROVIDERS.items():
        row=patches.get(provider)
        if not isinstance(row,dict): raise SystemExit(f"missing provider patch row: {provider}")
        script=str(cfg["script"])
        scripts=[x for x in (row.get("provider_lego_scripts") or []) if x!="scripts/provider_patches/non_display_recovery_runtime_v1.py"]
        if script not in scripts:
            scripts.append(script); changed.append(provider)
        row["provider_lego_scripts"]=unique(scripts)
        options=row.setdefault("provider_lego_options",{})
        options.pop("scripts/provider_patches/non_display_recovery_runtime_v1.py",None)
        options[script]={"provider":provider,"base":cfg["base"],"max_streams":int(cfg.get("max_streams") or 4)}
        if provider=="coflix":
            row["official_site"]="https://coflix.wiki"
            row["published_types"]=["movie","tv"]
        if provider=="sekai": row["official_site"]="https://sekai.one"
        mark_reproof(row)

    for provider,cfg in LOST.items():
        row=patches.get(provider)
        if not isinstance(row,dict): raise SystemExit(f"missing provider patch row: {provider}")
        scripts=list(row.get("provider_lego_scripts") or [])
        for old,new in (cfg.get("replace") or {}).items():
            scripts=[new if x==old else x for x in scripts]
        for script in cfg.get("scripts") or []:
            if script not in scripts: scripts.append(script)
        row["provider_lego_scripts"]=unique(scripts)
        if cfg.get("published_types"): row["published_types"]=list(cfg["published_types"])
        options=row.setdefault("provider_lego_options",{})
        for script,value in (cfg.get("options") or {}).items():
            options[script]=value
        mark_reproof(row)
        changed.append(provider)

    coflix=patches["coflix"]
    for key in ("domain_substitutions","replacements","runtime_domain_replacements"):
        mapping=coflix.get(key)
        if isinstance(mapping,dict):
            mapping.pop("coflix.wiki",None)
            for host in list(mapping):
                if host.startswith("coflix.") and host!="coflix.wiki":
                    mapping[host]="coflix.wiki"

    OVERRIDES.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PROVIDER_REPAIR_SURVIVAL_RESTORED providers="+",".join(sorted(set(changed)|set(NONDISPLAY_PROVIDERS))))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
