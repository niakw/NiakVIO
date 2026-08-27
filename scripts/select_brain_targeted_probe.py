#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

FIXTURES = {
    "movie": {"slug":"sinners-2025","tmdb_id":"1233413","media_type":"movie","title":"Sinners","year":"2025","season":"","episode":""},
    "tv": {"slug":"breaking-bad-s01e01","tmdb_id":"1396","media_type":"tv","title":"Breaking Bad","year":"2008","season":"1","episode":"1"},
    "anime": {"slug":"jujutsu-kaisen-s01e01","tmdb_id":"95479","media_type":"tv","title":"Jujutsu Kaisen","year":"2020","season":"1","episode":"1"},
}

def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def find_provider(value, valid):
    if isinstance(value, dict):
        for key in ('provider_id','providerId','provider','id'):
            candidate=str(value.get(key) or '').strip()
            if candidate.casefold() in valid: return candidate
        for child in value.values():
            found=find_provider(child, valid)
            if found: return found
    elif isinstance(value, list):
        for child in value:
            found=find_provider(child, valid)
            if found: return found
    return ''

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest', default='manifest.json')
    p.add_argument('--repair-report', default='')
    p.add_argument('--provider', default='')
    p.add_argument('--client', choices=('desktop','mobile','tv'), default='desktop')
    p.add_argument('--github-output', default='')
    p.add_argument('--json-out', default='')
    a=p.parse_args()
    manifest=load(a.manifest)
    rows={str(r.get('id') or '').casefold():r for r in manifest.get('scrapers',[]) if isinstance(r,dict) and str(r.get('id') or '').strip()}
    provider=a.provider.strip()
    if provider and provider.casefold() not in rows: raise SystemExit(f'unknown targeted provider: {provider}')
    if not provider and a.repair_report and Path(a.repair_report).is_file(): provider=find_provider(load(a.repair_report), rows)
    if not provider:
        result={'provider':'','client':a.client,'selected':False}
    else:
        row=rows[provider.casefold()]
        types=row.get('supportedTypes') or []
        if isinstance(types,str): types=[types]
        first=str(types[0] if types else 'movie').strip().casefold()
        declared=first if first in FIXTURES else 'movie'
        result={'provider':str(row.get('id') or provider),'client':a.client,'selected':True,'declared_type':declared,**FIXTURES[declared]}
    if a.json_out:
        Path(a.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json_out).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if a.github_output:
        with open(a.github_output,'a',encoding='utf-8') as fh:
            for key in ('provider','client','declared_type','slug','tmdb_id','media_type','title','year','season','episode'): fh.write(f'{key}={result.get(key, "")}\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
