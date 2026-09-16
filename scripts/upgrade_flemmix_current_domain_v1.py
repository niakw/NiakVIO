#!/usr/bin/env python3
"""Restore Flemmix to the live 2026-09-16 authority proven by max-repair probes."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'provider-overrides.json'
LIVE='flemmix.me'
OLD=(
 'flemmix.cloud','flemmix.casa','flemmix.gold','flemmix.voto','flemmix.garden','wiflix.name',
 'wiflix-hd.vip','ww1.wiflix-adresses.fun','flemmix.menn','ww547.wiflix-hd.vip','flemmix.wales',
 'flemmix.vip','flemmix.prof','wiflix.re','flemmix.cafe','flemmix.men','flemmix.kim'
)

def main()->int:
 data=json.loads(PATH.read_text(encoding='utf-8')); row=data['provider_patches']['flemmix']
 before=json.dumps(row,sort_keys=True,ensure_ascii=False)
 row['official_site']='https://flemmix.me'
 row.setdefault('manifest_overrides',{})['enabled']=True
 row['manifest_overrides']['supportsExternalPlayer']=True
 row['manifest_overrides']['logo']='https://flemmix.me/favicon.ico'
 for key in ('domain_substitutions','replacements','runtime_domain_replacements'):
  mapping=row.setdefault(key,{})
  for host in OLD: mapping[host]=LIVE
  mapping.pop(LIVE,None)
 routes=[str(x) for x in row.get('learned_routes') or []]
 preferred=['/search?q={query}','/index.php?do=search&subaction=search&story={query}','/?do=search&subaction=search&story={query}','/?s={query}','/sitemap.xml','/sitemap-movies-1.xml']
 row['learned_routes']=preferred+[x for x in routes if x not in preferred]
 candidates=[str(x) for x in row.get('candidate_learned_routes') or []]
 row['candidate_learned_routes']=preferred+[x for x in candidates if x not in preferred]
 notes=[str(x) for x in row.get('notes') or [] if 'active domain is flemmix.kim' not in str(x) and 'flemmix.cloud' not in str(x)]
 note='2026-09-16 live proof: flemmix.me serves current catalogue/detail pages and signed /embed/video players; flemmix.cloud returns Cloudflare 403. Working .me must never be rewritten to .cloud.'
 if note not in notes: notes.append(note)
 row['notes']=notes
 changed=before!=json.dumps(row,sort_keys=True,ensure_ascii=False)
 if changed: PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert row['official_site']=='https://flemmix.me'
 assert row['domain_substitutions'].get('flemmix.cloud')==LIVE and LIVE not in row['domain_substitutions']
 assert row['learned_routes'][0]=='/search?q={query}'
 print(f'FLEMMIX_CURRENT_DOMAIN_V1_OK changed={str(changed).lower()}')
 return 0
if __name__=='__main__': raise SystemExit(main())