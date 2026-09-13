#!/usr/bin/env python3
"""Bind the clean StreamZo suggest runtime to the active Hub46 provider."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OVR=ROOT/'provider-overrides.json'
MATRIX=ROOT/'automation/evidence/hub-lab-matrix-46.json'
LEGO='scripts/provider_patches/streamzo_runtime_v1.py'

def cid(v): return str(v or '').strip().casefold().replace('_','-')

def main():
    m=json.loads(MATRIX.read_text())
    active={cid(r.get('registryId')) for r in m.get('rows') or [] if isinstance(r,dict)}
    if 'streamzo' not in active or len(active)!=46: raise SystemExit('invalid Hub46 authority')
    d=json.loads(OVR.read_text()); p=(d.get('provider_patches') or {}).get('streamzo')
    if not isinstance(p,dict): raise SystemExit('streamzo missing from active overrides')
    scripts=[str(x) for x in p.get('provider_lego_scripts') or [] if str(x)]
    scripts=[x for x in scripts if '/streamzo_' not in x or x==LEGO]
    if LEGO not in scripts:scripts.append(LEGO)
    p['provider_lego_scripts']=scripts
    p['published_types']=['movie','tv','anime']
    p['route_data_state']='repair'
    notes=[str(x) for x in p.get('notes') or [] if str(x)]
    note='NIAKVIO_STREAMZO_SUGGEST_AUTHORITY_V1: /api/web/suggest exact href replaces stale generated-slug execution.'
    if note not in notes:notes.append(note)
    p['notes']=notes
    OVR.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print('STREAMZO_RUNTIME_V1_BOUND types=movie,tv,anime search=/api/web/suggest')
    return 0
if __name__=='__main__': raise SystemExit(main())
