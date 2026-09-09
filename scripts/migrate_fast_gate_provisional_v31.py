#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"

OLD = '''  if(semantic.length&&semantic.indexOf(type)<0){
    if(semantic.indexOf(namespace)>=0)type=namespace;
    else if(semantic.indexOf("anime")>=0&&(namespace==="tv"||namespace==="movie"))type="anime";
    else if(semantic.length===1)type=semantic[0];
    else return null;
  }
'''

NEW = '''  if(semantic.length&&semantic.indexOf(type)<0){
    var hasMovie=semantic.indexOf("movie")>=0,hasTv=semantic.indexOf("tv")>=0,hasAnime=semantic.indexOf("anime")>=0;
    // Explicit anime is a semantic request, not a generic TV alias. A provider
    // without anime capability must be rejected before provider/TMDB network.
    if(raw==="anime"&&!hasAnime)return null;
    // movie <-> tv transport mismatch is already conclusive from provider DATA.
    // Do not rewrite a single declared type just to make the provisional call run.
    if(type==="movie"&&!hasMovie&&!hasAnime)return null;
    if(type==="tv"&&!hasTv&&!hasAnime)return null;
    if(semantic.indexOf(namespace)>=0)type=namespace;
    else if(hasAnime&&(namespace==="tv"||namespace==="movie"))type="anime";
    else return null;
  }
'''

REV_OLD = '"revision": "tmdb-data-contract-launch-gate-v30-unified-60s-budget",'
REV_NEW = '"revision": "tmdb-data-contract-launch-gate-v31-pre-network-semantic-gate",'


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = False
    if OLD in text:
        text = text.replace(OLD, NEW, 1)
        changed = True
    elif NEW not in text:
        raise SystemExit("provisional fast-gate source pattern not found")

    if REV_OLD in text:
        text = text.replace(REV_OLD, REV_NEW, 1)
        changed = True
    elif REV_NEW not in text:
        raise SystemExit("media-type revision marker not found")

    if changed:
        TARGET.write_text(text, encoding="utf-8")
        print("FAST_GATE_MIGRATION changed=true revision=v31")
    else:
        print("FAST_GATE_MIGRATION changed=false revision=v31")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
