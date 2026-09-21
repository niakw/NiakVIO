#!/usr/bin/env python3
"""Select providers eligible for a full replay through a private residential exit.

Selection requires a provider-owned exact failed-route probe that was NOT
native-reachable on the GitHub network but became native-reachable (OkHttp or
direct HTTP approximation) through the residential exit. This file never stores
the exit-node identity or public IP.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(path)
    return value


def native_reached(prefix: dict[str, Any]) -> bool:
    direct=prefix.get("directHttpProfile") if isinstance(prefix.get("directHttpProfile"),dict) else {}
    okhttp=prefix.get("okHttpJvmProfile") if isinstance(prefix.get("okHttpJvmProfile"),dict) else {}
    return (
        str(direct.get("outcome") or "")=="direct_http_content_reached"
        or str(okhttp.get("outcome") or "")=="okhttp_jvm_content_reached"
    )


def select(report: dict[str, Any]) -> list[str]:
    providers=set()
    for row in report.get("rows") or []:
        if not isinstance(row,dict) or str(row.get("seedKind") or "")!="network-failure-replay":
            continue
        provider=str(row.get("provider") or "").strip().casefold()
        residential=row.get("residentialExitNodeProfile") if isinstance(row.get("residentialExitNodeProfile"),dict) else {}
        if not provider or not residential:
            continue
        if native_reached(row):
            continue
        if native_reached(residential):
            providers.add(provider)
    return sorted(providers)


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--waf",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    providers=select(load(args.waf))
    payload={
        "schemaVersion":1,
        "selection":"github-native-failed-residential-native-reached",
        "providers":providers,
        "providerCount":len(providers),
    }
    args.output.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(f"FIELD_RESIDENTIAL_PROVIDER_REPLAY_SELECTION providers={len(providers)}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
