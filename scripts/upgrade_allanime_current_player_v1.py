#!/usr/bin/env python3
"""Align AllAnime with the current 9animes/megaplay HTML embed contract."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PATH=ROOT/'provider-overrides.json'

def main()->int:
 data=json.loads(PATH.read_text(encoding='utf-8')); row=data['provider_patches']['allanime']; before=json.dumps(row,sort_keys=True,ensure_ascii=False)
 row['capability']='mixed_embed_resolver'; row['official_site']='https://9animes.me.uk'; row['published_types']=['anime']
 row.setdefault('manifest_overrides',{})['enabled']=True
 subs=row.setdefault('domain_substitutions',{}); subs['aniwatchtv.watch']='9animes.me.uk'; subs['ww2.aniwatch.fit']='9animes.me.uk'
 runtime=row.setdefault('runtime_domain_replacements',{}); runtime['aniwatchtv.watch']='9animes.me.uk'; runtime['ww2.aniwatch.fit']='9animes.me.uk'
 routes=[str(x) for x in row.get('learned_routes') or []]; preferred=['/?s={query}','/wp-admin/admin-ajax.php']
 row['learned_routes']=preferred+[x for x in routes if x not in preferred]
 row['identity_input']={'mode':'catalog_search','requires_tmdb_before_run':True,'required_fields':['title','mediaType']}
 notes=[str(x) for x in row.get('notes') or []]
 note='2026-09-16 live proof: 9animes.me.uk search and episode pages return 200 and expose a current megaplay.buzz iframe; this is an embed-resolver contract, not direct-media.'
 if note not in notes: notes.append(note)
 row['notes']=notes
 caps=data.setdefault('provider_capabilities',{}).setdefault('allanime',{})
 caps['strategy']='mixed_embed_resolver'; caps['validation']='provider_native'; caps['allow_html_url']=True; caps['requires_direct_media']=False
 origins=[str(x) for x in caps.get('observed_origins') or []]
 for x in ['https://9animes.me.uk','https://megaplay.buzz']:
  if x not in origins: origins.append(x)
 caps['observed_origins']=origins
 changed=before!=json.dumps(row,sort_keys=True,ensure_ascii=False)
 if changed: PATH.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert row['official_site']=='https://9animes.me.uk' and row['published_types']==['anime']
 assert caps['allow_html_url'] is True and caps['requires_direct_media'] is False
 print(f'ALLANIME_CURRENT_PLAYER_V1_OK changed={str(changed).lower()}');return 0
if __name__=='__main__':raise SystemExit(main())