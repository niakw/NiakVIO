#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations
import argparse, html, json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def route_summary(test):
    rows=[]
    for item in test.get('network_observations') or []:
        if item.get('infrastructure') or not item.get('host'):
            continue
        rows.append({
            'stage': item.get('stage') or 'unknown',
            'host': item.get('host'),
            'method': item.get('method') or 'GET',
            'path_pattern': item.get('path_pattern'),
            'status': item.get('status'),
        })
    return rows

def classify(test):
    obs=test.get('network_observations') or []
    statuses=[x.get('status') for x in obs if isinstance(x.get('status'),int) and not x.get('infrastructure')]
    if test.get('status')=='healthy': return 'stream_valid'
    if test.get('streams_returned',0)>0: return 'resolver_failed'
    if statuses and all(s==404 for s in statuses): return 'search_or_route_obsolete'
    if any(200 <= s < 400 for s in statuses): return 'content_not_found_or_parser_failed'
    if statuses: return 'provider_reachable_http_error'
    if test.get('worker_ok'): return 'content_not_found'
    return 'provider_unreachable_or_runtime_error'

def language(test):
    audio=set(test.get('audio_languages') or []); subs=set(test.get('subtitle_languages') or [])
    raw=' '.join(str(x) for x in (test.get('stream_titles') or [])).lower()
    if 'fr' in audio or 'truefrench' in raw or ' vf' in f' {raw}': return {'group':'vf','confidence':'high','evidence':['runtime_audio_or_label']}
    if 'fr' in subs or 'vostfr' in raw: return {'group':'vostfr','confidence':'high','evidence':['runtime_subtitle_or_label']}
    return {'group':'unknown','confidence':'none','evidence':[]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--results',type=Path,default=ROOT/'health-output/health-results.json'); ap.add_argument('--output',type=Path,default=ROOT)
    a=ap.parse_args(); payload=json.loads(a.results.read_text(encoding='utf-8'))
    rows=[]
    for item in payload.get('results',[]):
        tests=item.get('tests') or []
        stages=[classify(t) for t in tests]
        preflight=item.get('dns_preflight') or {}
        decision=preflight.get('decision') or {}
        rows.append({'id':item.get('canonical_id') or item.get('id'),'source':item.get('source'),'status':item.get('status'),'score':item.get('score'), 'dns_preflight_status':decision.get('status'), 'dns_resolver':decision.get('selected_resolver'), 'dns_migration_candidate':(decision.get('migration_candidate') or {}).get('host') if isinstance(decision.get('migration_candidate'),dict) else None, 'diagnostic_stages':stages,'language_evidence':[language(t) for t in tests], 'route_observations':[route_summary(t) for t in tests], 'last_checked':payload.get('generated_at')})
    report={'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),'providers':rows}
    a.output.mkdir(parents=True,exist_ok=True); (a.output/'diagnostics-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=''.join(f"<tr><td>{html.escape(str(r['id']))}</td><td>{html.escape(str(r['source']))}</td><td>{html.escape(str(r['dns_preflight_status'] or 'n/a'))}</td><td>{html.escape(str(r['dns_resolver'] or ''))}</td><td>{html.escape(str(r['status']))}</td><td>{html.escape(', '.join(r['diagnostic_stages']))}</td><td>{html.escape(', '.join(sorted({x['group'] for x in r['language_evidence']})))}</td><td>{html.escape(str(r['score']))}</td></tr>" for r in rows)
    doc=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Nuvio diagnostics</title><style>body{{font-family:system-ui;margin:2rem;line-height:1.4}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:.45rem;text-align:left}}th{{position:sticky;top:0;background:#fff}}code{{font-size:.9em}}</style><h1>Diagnostic des providers Nuvio</h1><p>Généré le {html.escape(report['generated_at'])}. Les URLs finales ne sont jamais publiées.</p><table><thead><tr><th>Provider</th><th>Source</th><th>Préflight DNS</th><th>Résolveur</th><th>Statut</th><th>Étape</th><th>Langue</th><th>Score</th></tr></thead><tbody>{body}</tbody></table></html>'''
    (a.output/'diagnostics-report.html').write_text(doc,encoding='utf-8')
if __name__=='__main__': main()
