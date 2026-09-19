#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,os,re,shutil,subprocess,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'local-output'/'global-provider-repair'; STAGE=BASE/'staging'; OUT=BASE/'health-output'
CATS=('movie','tv','anime'); FR_AUDIO={'fr','fra','fre','french','vf','vfq','fr-fr'}; FR_SUB={'fr','fra','fre','french','vostfr','fr-fr'}

def load(p:Path): return json.loads(p.read_text(encoding='utf-8'))
def dump(p:Path,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvdump(p:Path,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    if not rows: p.write_text('',encoding='utf-8'); return
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def run(*args,env=None):
    e=os.environ.copy(); e.update(env or {}); print('+',' '.join(map(str,args)),flush=True); subprocess.run([str(x) for x in args],cwd=ROOT,env=e,check=True)
def manifest(path):
    d=load(path); return [r for r in (d.get('scrapers') or d.get('providers') or []) if isinstance(r,dict)]
def states():
    out={}
    for k,p in [('general',ROOT/'manifest.json'),('vf',ROOT/'vf'/'manifest.json')]:
        rows=manifest(p); ids=[]; enabled={}
        for r in rows:
            i=str(r.get('id') or r.get('name') or '').strip().casefold()
            if i: ids.append(i); enabled[i]=r.get('enabled') is True
        out[k]={'ids':ids,'enabled':enabled}
    return out
def norm(v): return ''.join(c for c in str(v or '').casefold() if c.isalnum())
def langs(v):
    s=set()
    for x in v or []:
        t=str(x).strip().casefold().replace('_','-')
        if t: s.add(t); s.add('fr' if t.startswith('fr-') else t); s.add('french' if t.startswith('french') else t)
    return s
def category(t):
    f=t.get('fixture') or {}; c=str(f.get('category') or f.get('mediaType') or '').casefold(); return c if c in CATS else 'unknown'
def foreign_routes(test,pid,known):
    own=norm(pid); aliases={norm(x):x for x in known if len(norm(x))>=5}; found=set()
    for o in test.get('network_observations') or []:
        if not isinstance(o,dict) or o.get('infrastructure') or o.get('stage')!='player': continue
        st=o.get('status')
        if not isinstance(st,int) or not 200<=st<400: continue
        for seg in re.split(r'[/?.=&:_-]+',str(o.get('path_pattern') or '')):
            n=norm(seg); owner=aliases.get(n)
            if owner and n!=own: found.add(owner)
    return sorted(found)
def metrics(result,known):
    pid=str(result.get('canonical_id') or result.get('upstream_id') or '').casefold(); out={}
    for c in CATS:
        for k in ('returned','playable','verified','vf','vostfr','height'): out[f'{c}_{k}']=0
    foreign=set()
    for t in result.get('tests') or []:
        if not isinstance(t,dict): continue
        c=category(t)
        if c not in CATS: continue
        fr=foreign_routes(t,pid,known); foreign.update(fr)
        ret=int(t.get('streams_returned') or t.get('stream_count') or 0); play=int(t.get('streams_playable') or 0); ver=int(t.get('payload_verified_streams') or 0)
        a=langs(t.get('accepted_audio_languages') or t.get('audio_languages')); s=langs(t.get('accepted_subtitle_languages') or t.get('subtitle_languages'))
        strict=play>0 and ver>0 and not fr; vf=strict and bool(a&FR_AUDIO); vost=strict and not vf and bool(s&FR_SUB)
        out[f'{c}_returned']+=ret; out[f'{c}_playable']+=play if not fr else 0; out[f'{c}_verified']+=ver if not fr else 0
        out[f'{c}_vf']+=int(vf); out[f'{c}_vostfr']+=int(vost); out[f'{c}_height']=max(out[f'{c}_height'],int(t.get('effective_max_height') or t.get('verified_max_height') or 0))
    out['foreign_provider_routes']=','.join(sorted(foreign)); return out
def row(result,candidate,known):
    ev=result.get('evidence') or {}; m=metrics(result,known); foreign=m['foreign_provider_routes']; playable=int(ev.get('streams_playable') or 0); verified=int(ev.get('payload_verified_streams') or 0)
    strict=result.get('status')=='healthy' and playable>0 and verified>0 and not foreign
    vf=sum(m[f'{c}_vf']+m[f'{c}_vostfr'] for c in CATS)>0
    return {'provider':str(result.get('canonical_id') or result.get('upstream_id') or '').casefold(),'variant_key':str(result.get('key') or ''),'source':str(candidate.get('source') or result.get('source') or ''),'status':str(result.get('status') or ''),'score':int(result.get('score') or 0),'streams_returned':max([int(t.get('streams_returned') or t.get('stream_count') or 0) for t in result.get('tests') or []] or [0]),'streams_playable':playable,'payload_verified':verified,'verified_max_height':int(result.get('verified_max_height') or 0),'strictly_playable':strict,'vf_eligible':strict and vf,**m}
def rank(r,vf=False):
    if vf: return (int(r['movie_vf']),int(r['movie_vostfr']),int(r['vf_eligible']),int(r['movie_verified']),int(r['movie_height']),int(r['score']))
    return (int(r['strictly_playable']),int(r['payload_verified']),int(r['streams_playable']),int(r['verified_max_height']),int(r['score']))
def build(state):
    health=load(OUT/'health-results.json'); reg=load(STAGE/'candidates.json'); candidates={str(x.get('key')):x for x in reg.get('candidates') or [] if isinstance(x,dict)}
    known={str(x.get('canonical_id') or x.get('upstream_id') or '').casefold() for x in candidates.values()}
    variants=[row(r,candidates.get(str(r.get('key')),{}),known) for r in health.get('results') or [] if isinstance(r,dict)]
    by=defaultdict(list)
    for r in variants: by[r['provider']].append(r)
    def select(kind):
        rows=[]
        for pid in state[kind]['ids']:
            if pid not in by: continue
            best=max(by[pid],key=lambda x:rank(x,kind=='vf')); rec=bool(best['vf_eligible'] if kind=='vf' else best['strictly_playable'])
            rows.append({**best,'currently_enabled':bool(state[kind]['enabled'].get(pid)),'recommended_enabled':rec,'variant_count':len(by[pid])})
        return sorted(rows,key=lambda x:(not x['recommended_enabled'],x['provider']))
    general=select('general'); vf=select('vf'); movies=sorted([r for r in variants if r['movie_returned'] or 'movie' in str(candidates.get(r['variant_key'],{}).get('supported_types') or '')],key=lambda x:(-x['movie_vf'],-x['movie_vostfr'],-x['movie_verified'],-x['movie_height'],x['provider']))
    for name,rows in [('variant-matrix',variants),('provider-matrix',general),('vf-provider-matrix',vf),('vf-movie-matrix',movies)]: dump(BASE/f'{name}.json',rows); csvdump(BASE/f'{name}.csv',rows)
    plan={k:{'enable':[r['provider'] for r in rows if r['recommended_enabled'] and not r['currently_enabled']],'disable':[r['provider'] for r in rows if not r['recommended_enabled'] and r['currently_enabled']]} for k,rows in [('general',general),('vf',vf)]}; plan['publication_performed']=False; dump(BASE/'activation-plan.json',plan)
    summary={'tested_variant_count':len(variants),'general_strictly_healthy':sum(r['recommended_enabled'] for r in general),'vf_strictly_healthy':sum(r['recommended_enabled'] for r in vf),'vf_movie_vf_proven':[r['provider'] for r in vf if r['movie_vf']>0],'vf_movie_vf_proven_count':sum(r['movie_vf']>0 for r in vf),'cross_provider_route_rule':'successful player routes owned by another provider invalidate health and VF proof','publication_performed':False}; dump(BASE/'SUMMARY.json',summary); return summary
def main():
    p=argparse.ArgumentParser(); p.add_argument('--scope',choices=['all','vf'],default='all'); p.add_argument('--reprocess-from',type=Path); a=p.parse_args(); state=states(); ids=set(state['vf']['ids'] if a.scope=='vf' else state['general']['ids']+state['vf']['ids'])
    if a.reprocess_from:
        src=a.reprocess_from.expanduser().resolve()
        if src==BASE.resolve(): raise ValueError('--reprocess-from must point to a different directory')
        if BASE.exists(): shutil.rmtree(BASE)
        shutil.copytree(src,BASE)
    else:
        if BASE.exists(): shutil.rmtree(BASE)
        BASE.mkdir(parents=True); run(sys.executable,ROOT/'scripts'/'resolve_provider_hubs.py','--output',BASE/'provider-hub-resolution.json','--mode','deep','--include-disabled','--apply'); run(sys.executable,ROOT/'scripts'/'discover_candidates.py','--stage',STAGE)
        reg=load(STAGE/'candidates.json'); reg['candidates']=[x for x in reg.get('candidates') or [] if str(x.get('canonical_id') or x.get('upstream_id') or '').casefold() in ids]; dump(STAGE/'candidates.json',reg)
        run('node',ROOT/'scripts'/'provider_dns_preflight.mjs','--stage',STAGE,'--output',BASE/'dns-preflight-report.json'); run(sys.executable,ROOT/'scripts'/'apply_dns_migration_overrides.py','--stage',STAGE,'--report',BASE/'dns-preflight-report.json'); run(sys.executable,ROOT/'scripts'/'build_provider_runtime_profiles.py','--stage',STAGE,'--apply-stage'); run(sys.executable,ROOT/'scripts'/'validate_override_pipeline.py','--stage',STAGE); run(sys.executable,ROOT/'scripts'/'deep_repair_loop.py','--stage',STAGE,'--output',OUT,'--mode','deep',env={'NUVIO_DNS_PREFLIGHT_RESULTS':str(BASE/'dns-preflight-report.json')})
    s=build(state); print(json.dumps(s,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
