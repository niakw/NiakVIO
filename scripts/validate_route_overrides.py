#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate route override schema and detect provider route regressions in health output."""
from __future__ import annotations
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]

def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise SystemExit(f'{path}: expected JSON object')
    return value

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--config',type=Path,default=ROOT/'provider-overrides.json')
    ap.add_argument('--results',type=Path,default=ROOT/'health-output/health-results.json')
    ap.add_argument('--report',type=Path,default=ROOT/'health-output/route-regressions.json')
    ap.add_argument('--strict',action='store_true',help='deprecated compatibility flag; route regressions are reported per provider and never block the whole workflow')
    args=ap.parse_args()
    cfg=load(args.config)
    defaults=cfg.get('route_override_defaults') or {}
    min_requests=max(1,int(defaults.get('minimum_requests',3)))
    obsolete={int(x) for x in defaults.get('obsolete_statuses',[404,410])}
    ratio=float(defaults.get('obsolete_ratio',0.75))
    patches=cfg.get('provider_patches') or {}
    failures=[]
    for pid,patch in patches.items():
        if not isinstance(patch,dict): failures.append(f'{pid}: patch must be an object'); continue
        for key in ('route_replacements','replacements'):
            values=patch.get(key) or {}
            if not isinstance(values,dict): failures.append(f'{pid}: {key} must be an object'); continue
            for old,new in values.items():
                if not isinstance(old,str) or not old: failures.append(f'{pid}: empty {key} source')
                if not isinstance(new,str) or not new: failures.append(f'{pid}: empty {key} destination')
                if old==new: failures.append(f'{pid}: no-op {key}: {old}')
    if failures: raise SystemExit('\n'.join(failures))
    if not args.results.exists():
        print('route override schema validation passed (health results absent)'); return
    payload=load(args.results)
    regressions=[]
    instrumentation_gaps=[]
    for item in payload.get('results',[]):
        pid=str(item.get('canonical_id') or item.get('id') or '')
        grouped=defaultdict(list)
        origin_success=defaultdict(bool)
        for test in item.get('tests') or []:
            for obs in test.get('network_observations') or []:
                if obs.get('infrastructure') or not obs.get('host'): continue
                host=str(obs['host'])
                stage=str(obs.get('stage') or 'unknown')
                status=obs.get('status')
                if stage=='origin_probe' and isinstance(status,int) and 200 <= status < 400: origin_success[host]=True
                if stage in {'search','content_lookup','episode'} and isinstance(status,int): grouped[(host,stage)].append(obs)
        successful_origins=sorted(host for host,ok in origin_success.items() if ok)
        route_row_count=sum(len(rows) for rows in grouped.values())
        if successful_origins and route_row_count == 0:
            instrumentation_gaps.append({
                'provider':pid,
                'hosts':successful_origins,
                'reason':'origin_reachable_but_no_search_or_content_routes_observed',
                'action':'inspect provider lookup prerequisites and ensure every provider request uses the guarded global fetch'
            })
        for (host,stage),rows in grouped.items():
            bad=[r for r in rows if r.get('status') in obsolete]
            if len(rows) < min_requests or len(bad)/len(rows) < ratio or not origin_success.get(host): continue
            patterns=Counter(str(r.get('path_pattern') or '') for r in bad)
            regressions.append({
                'provider':pid,'host':host,'stage':stage,'requests':len(rows),
                'obsolete_responses':len(bad),'obsolete_ratio':round(len(bad)/len(rows),3),
                'path_patterns':[{'pattern':p,'count':n} for p,n in patterns.most_common(12)],
                'configured_route_replacements':(patches.get(pid) or {}).get('route_replacements') or {},
                'action':'the bounded deep-repair loop should try every structurally compatible runtime profile; add a reusable profile only when no generic strategy matches'
            })
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps({'schema_version':3,'regressions':regressions,'instrumentation_gaps':instrumentation_gaps,'provider_specific_rules':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.strict:
        print('warning: --strict is deprecated; provider route regressions are reported and scored but do not block the global workflow')
    print(f'route override validation passed ({len(regressions)} route regression signature(s) reported)')
if __name__=='__main__': main()
