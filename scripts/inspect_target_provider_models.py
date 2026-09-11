#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
overrides=json.loads((ROOT/'provider-overrides.json').read_text(encoding='utf-8'))
knowledge=json.loads((ROOT/'automation/provider-v3-static-knowledge.json').read_text(encoding='utf-8'))
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
patches=overrides.get('provider_patches') or {}
caps=overrides.get('provider_capabilities') or {}
static=knowledge.get('providers') or {}
rows={str(r.get('id','')).strip().casefold():r for r in manifest.get('scrapers',[]) if isinstance(r,dict)}
for pid in ('vidrock','vidfast','anidb','vostfree','playimdb'):
    print('===',pid,'===')
    print('MANIFEST',json.dumps(rows.get(pid),ensure_ascii=False,sort_keys=True))
    print('PATCH',json.dumps(patches.get(pid),ensure_ascii=False,sort_keys=True))
    print('CAP',json.dumps(caps.get(pid),ensure_ascii=False,sort_keys=True))
    print('STATIC',json.dumps(static.get(pid),ensure_ascii=False,sort_keys=True))
