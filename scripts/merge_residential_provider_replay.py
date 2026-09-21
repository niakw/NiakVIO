#!/usr/bin/env python3
"""Attach a privacy-safe summary of full provider replay through residential egress."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(path)
    return value


def summarize(replay: dict[str, Any]) -> dict[str, Any]:
    providers=sorted({str(v).strip().casefold() for v in replay.get("providers") or [] if str(v).strip()})
    rows=[]
    for row in replay.get("rows") or []:
        if not isinstance(row,dict):
            continue
        provider=str(row.get("provider_id") or row.get("provider") or "").strip().casefold()
        if not provider:
            continue
        rows.append({
            "provider":provider,
            "lane":str(row.get("semantic_type") or row.get("lane") or "").strip().casefold(),
            "status":str(row.get("status") or ""),
            "debugStage":str(row.get("debug_stage") or ""),
            "raw":int(row.get("raw") or 0),
            "playable":int(row.get("playable") or 0),
            "verified":int(row.get("verified") or 0),
            "contradictions":int(row.get("contradictions") or 0),
            "identitySafe":row.get("identity_safe") is True,
        })
    return {
        "available":True,
        "profile":"tailscale-residential-exit",
        "providerCount":len(providers),
        "providers":providers,
        "rawProviders":sorted({str(v).strip().casefold() for v in replay.get("raw_providers") or [] if str(v).strip()}),
        "playableProviders":sorted({str(v).strip().casefold() for v in replay.get("playable_providers") or [] if str(v).strip()}),
        "verifiedProviders":sorted({str(v).strip().casefold() for v in replay.get("verified_providers") or [] if str(v).strip()}),
        "wrongContentProviders":sorted({str(v).strip().casefold() for v in replay.get("wrong_content_providers") or [] if str(v).strip()}),
        "rows":rows,
        "privacy":{
            "exitNodeNamePersisted":False,
            "tailscaleAddressPersisted":False,
            "residentialPublicIpPersisted":False,
            "responseBodiesPersisted":False,
            "cookiesPersisted":False,
        },
    }


def merge(waf: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    out=copy.deepcopy(waf)
    out["residentialProviderReplay"]=summarize(replay)
    return out


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--waf",type=Path,required=True)
    ap.add_argument("--replay",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    out=merge(load(args.waf),load(args.replay))
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary=out["residentialProviderReplay"]
    print(
        "FIELD_RESIDENTIAL_PROVIDER_REPLAY "
        f"providers={summary['providerCount']} playable={len(summary['playableProviders'])} "
        f"verified={len(summary['verifiedProviders'])} wrong={len(summary['wrongContentProviders'])}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
