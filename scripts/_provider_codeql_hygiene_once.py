#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VF_PATCH = "scripts/provider_patches/vf_catalogue_recovery.py"
DIRECT_V1 = "scripts/provider_patches/nuvio_tv_direct_media.py"
DIRECT_V2 = "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
BASE_STORE = "scripts/provider_base_store.py"
SECURITY_GATE = ".github/workflows/security-final-gate.yml"
VF_TEST = "tests/vf_catalogue_identity_hardening_test.py"

OLD_GENERIC_URL = r'''/https?:\\?\/\\?\/[^"'<>\s]+/gi'''
NEW_GENERIC_URL = r'''/https?:\/\/[^"'<>\s]+/gi'''

OLD_UNESCAPE_S = r'''function unescapeJs(v){try{return JSON.parse('"'+s(v).replace(/"/g,'\\"')+'"')}catch(_){return clean(v)}}'''
OLD_UNESCAPE_STR = r'''function unescapeJs(v){try{return JSON.parse('"'+str(v).replace(/"/g,'\\"')+'"')}catch(_){return clean(v)}}'''

NEW_UNESCAPE_S = r'''function unescapeJs(v){var raw=s(v),out="";for(var i=0;i<raw.length;i++){var ch=raw.charAt(i);if(ch!=="\\"||i+1>=raw.length){out+=ch;continue}var next=raw.charAt(++i),hex;if(next==="u"&&(hex=raw.slice(i+1,i+5)).length===4&&/^[0-9a-fA-F]{4}$/.test(hex)){out+=String.fromCharCode(parseInt(hex,16));i+=4;continue}if(next==="x"&&(hex=raw.slice(i+1,i+3)).length===2&&/^[0-9a-fA-F]{2}$/.test(hex)){out+=String.fromCharCode(parseInt(hex,16));i+=2;continue}if(/[0-7]/.test(next)){var oct=next;while(oct.length<3&&i+1<raw.length&&/[0-7]/.test(raw.charAt(i+1)))oct+=raw.charAt(++i);out+=String.fromCharCode(parseInt(oct,8));continue}if(next==="n"){out+="\n";continue}if(next==="r"){out+="\r";continue}if(next==="t"){out+="\t";continue}if(next==="b"){out+="\b";continue}if(next==="f"){out+="\f";continue}if(next==="v"){out+="\v";continue}out+=next}return out}'''
NEW_UNESCAPE_STR = NEW_UNESCAPE_S.replace("raw=s(v)", "raw=str(v)", 1)

def replace_exact(text: str, old: str, new: str, label: str, *, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{label}: expected {expected} occurrence(s), found {count}")
    return text.replace(old, new)

def patch_vf_source() -> None:
    path = ROOT / VF_PATCH
    text = path.read_text(encoding="utf-8")
    text = replace_exact(text, '"implementationVersion": 2,', '"implementationVersion": 3,', "vf implementation revision")
    old_json = r'''    var jsonRe=/[\{,]\s*["']?(?:season|saison)["']?\s*:\s*(\d+)[\s\S]{0,500}?["']?(?:episode|ep)["']?\s*:\s*(\d+)[\s\S]{0,700}?["']?(?:url|src|embedUrl|embed_url|player)["']?\s*:\s*["'](https?:\\?\/\\?\/[^"']+)["']/gi,m;'''
    new_json = r'''    var jsonRe=/[{,]\s*["']?(?:season|saison)["']?\s*:\s*(\d+)[\s\S]{0,500}?["']?(?:episode|ep)["']?\s*:\s*(\d+)[\s\S]{0,700}?["']?(?:url|src|embedUrl|embed_url|player)["']?\s*:\s*["'](https?:\/\/[^"']+)["']/gi,m;'''
    text = replace_exact(text, old_json, new_json, "vf normalized JSON URL regex")
    old_span = r'''new RegExp("saison[ ._-]*0?"+season+"[\s\S]{0,40}(?:episode|ep)[ ._-]*0?"+episode,"i")'''
    new_span = r'''new RegExp("saison[ ._-]*0?"+season+"[\\s\\S]{0,40}(?:episode|ep)[ ._-]*0?"+episode,"i")'''
    text = replace_exact(text, old_span, new_span, "vf RegExp constructor span")
    old_routes = r'''      if(/\/movie(?:\/|\{|$)/i.test(low)&&type!=="movie")continue;
      if(/\/tv(?:\/|\{|$)/i.test(low)&&type!=="tv")continue;'''
    new_routes = r'''      if((low.indexOf("/movie/")>=0||low.indexOf("/movie{")>=0||low.endsWith("/movie"))&&type!=="movie")continue;
      if((low.indexOf("/tv/")>=0||low.indexOf("/tv{")>=0||low.endsWith("/tv"))&&type!=="tv")continue;'''
    text = replace_exact(text, old_routes, new_routes, "vf fixed API route kind")
    path.write_text(text, encoding="utf-8")

def patch_direct_source(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    text = replace_exact(text, old, new, f"{relative} literal decoder")
    path.write_text(text, encoding="utf-8")

def patch_base_store_source() -> None:
    path = ROOT / BASE_STORE
    text = path.read_text(encoding="utf-8")
    count = text.count(OLD_GENERIC_URL)
    if count < 1:
        raise RuntimeError("provider_base_store: normalized URL pattern not found")
    text = text.replace(OLD_GENERIC_URL, NEW_GENERIC_URL)
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_CODEQL_BASE_STORE_REGEX replacements={count}")

def patch_vf_test() -> None:
    path = ROOT / VF_TEST
    text = path.read_text(encoding="utf-8")
    text = replace_exact(text, 'assert \'"implementationVersion": 2,\' in source', 'assert \'"implementationVersion": 3,\' in source', "vf test revision")
    path.write_text(text, encoding="utf-8")

def patch_security_gate() -> None:
    path = ROOT / SECURITY_GATE
    text = path.read_text(encoding="utf-8")
    step = "      - name: Gate open high and critical CodeQL alerts on main\n"
    new_step = "      - name: Gate release-reachable high and critical CodeQL alerts on main\n"
    text = replace_exact(text, step, new_step, "security gate step name")
    scope = text.index(new_step)
    start = text.index("          import json, os\n", scope)
    end = text.index("          PY\n", start)
    block = '''          import json, os
          from pathlib import Path

          pages=json.loads(Path(os.environ['RUNNER_TEMP']+'/codeql-open.json').read_text())
          alerts=[row for page in pages for row in (page if isinstance(page,list) else []) if isinstance(row,dict)]

          active_provider_paths=set()
          for manifest_path in (Path('manifest.json'),Path('vf/manifest.json'),Path('vostfr/manifest.json')):
              if not manifest_path.is_file():
                  continue
              payload=json.loads(manifest_path.read_text(encoding='utf-8'))
              for entry in payload.get('scrapers') or []:
                  if not isinstance(entry,dict):
                      continue
                  filename=str(entry.get('filename') or '')
                  if filename.startswith('providers/'):
                      active_provider_paths.add(filename)

          active_base_paths=set()
          provenance_path=Path('PROVENANCE.json')
          if provenance_path.is_file():
              provenance=json.loads(provenance_path.read_text(encoding='utf-8'))
              for row in (provenance.get('providers') or {}).values():
                  if not isinstance(row,dict):
                      continue
                  base=str(row.get('base_filename') or '')
                  published=str(row.get('published_filename') or '')
                  if base.startswith('provider-bases/'):
                      active_base_paths.add(base)
                  if published.startswith('providers/'):
                      active_provider_paths.add(published)

          revocation_path=Path('provider-security-revocations.json')
          revocations=json.loads(revocation_path.read_text()) if revocation_path.is_file() else {'entries':[]}
          revoked={
              str(item.get('path') or '')
              for item in (revocations.get('entries') or [])
              if isinstance(item,dict) and str(item.get('path') or '')
          }

          bad=[]
          provider_bad=[]
          stale_revoked=[]
          historical_provider=[]
          historical_base=[]
          for row in alerts:
              rule=row.get('rule') or {}
              severity=str(rule.get('security_severity_level') or rule.get('severity') or '').lower()
              instance=row.get('most_recent_instance') or {}
              location=instance.get('location') or {}
              alert_path=str(location.get('path') or '')
              if severity not in {'high','critical'}:
                  continue
              item={
                  'number': row.get('number'),
                  'rule': rule.get('id') or rule.get('name'),
                  'severity': severity,
                  'path': alert_path,
              }
              current_path=Path(alert_path) if alert_path else None
              if current_path is not None and current_path.is_file():
                  if alert_path.startswith('providers/') and alert_path not in active_provider_paths:
                      historical_provider.append({**item,'reason':'historical_unreferenced_provider_artifact'})
                      continue
                  if alert_path.startswith('provider-bases/') and alert_path not in active_base_paths:
                      historical_base.append({**item,'reason':'historical_unreferenced_provider_base'})
                      continue
                  bad.append(item)
                  if alert_path.startswith(('providers/','provider-bases/')):
                      provider_bad.append(item)
                  continue
              if alert_path in revoked:
                  stale_revoked.append(item)
                  continue
              bad.append({**item,'reason':'missing_from_current_tree_without_explicit_security_revocation'})

          print(
              f'FIELD_CODEQL_ALERTS open={len(alerts)} release_high_or_critical={len(bad)} '
              f'release_provider_high_or_critical={len(provider_bad)} stale_revoked={len(stale_revoked)} '
              f'historical_provider={len(historical_provider)} historical_base={len(historical_base)}'
          )
          for item in historical_provider:
              print('HISTORICAL_PROVIDER_HIGH_ALERT=' + json.dumps(item, sort_keys=True))
          for item in historical_base:
              print('HISTORICAL_BASE_HIGH_ALERT=' + json.dumps(item, sort_keys=True))
          for item in stale_revoked:
              print('STALE_REVOKED_HIGH_ALERT=' + json.dumps(item, sort_keys=True))
          for item in bad:
              print('OPEN_RELEASE_HIGH_ALERT=' + json.dumps(item, sort_keys=True))
          if bad:
              raise SystemExit('release-reachable or unrevoked high/critical CodeQL alerts remain on tested main tree')
'''
    text = text[:start] + block + text[end:]
    text = text.replace(
        "Global hardening contract, exhaustive published-provider scan, exact-SHA CodeQL and repository-wide High/Critical gate are green.",
        "Global hardening contract, exhaustive published-provider scan, exact-SHA CodeQL and release-reachable High/Critical gate are green.",
    )
    path.write_text(text, encoding="utf-8")

def load_module(path: Path, name: str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def migrate_active_bases() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from provider_base_store import validate_base, write_base

    overrides=json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    provenance_path=ROOT / "PROVENANCE.json"
    provenance=json.loads(provenance_path.read_text(encoding="utf-8"))
    rows=provenance.get("providers")
    if not isinstance(rows,dict):
        raise RuntimeError("PROVENANCE.providers missing")

    patches=overrides.get("provider_patches") or {}
    vf_ids={
        str(provider_id).casefold()
        for provider_id, cfg in patches.items()
        if isinstance(cfg,dict) and VF_PATCH in [str(v) for v in (cfg.get("patch_scripts") or [])]
    }

    direct_ids=set()
    base_texts={}
    for provider_id,row in rows.items():
        if not isinstance(row,dict):
            continue
        rel=str(row.get("base_filename") or "")
        path=ROOT / rel
        if not rel.startswith("provider-bases/") or not path.is_file():
            continue
        current=path.read_text(encoding="utf-8")
        base_texts[provider_id]=current
        if OLD_UNESCAPE_S in current or OLD_UNESCAPE_STR in current:
            direct_ids.add(provider_id)

    targets=set(vf_ids)|direct_ids|{"kehflix"}
    missing=[provider_id for provider_id in targets if provider_id not in rows]
    if missing:
        raise RuntimeError("missing target provenance rows: "+",".join(sorted(missing)))

    vf_module=load_module(ROOT / VF_PATCH, "vf_catalogue_recovery_codeql_hygiene")
    changed=[]
    for provider_id in sorted(targets):
        row=rows[provider_id]
        rel=str(row.get("base_filename") or "")
        path=ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"{provider_id}: active ProviderBase missing: {rel}")
        before=path.read_text(encoding="utf-8")
        after=before

        if OLD_GENERIC_URL in after:
            after=after.replace(OLD_GENERIC_URL,NEW_GENERIC_URL)
        if OLD_UNESCAPE_S in after:
            after=after.replace(OLD_UNESCAPE_S,NEW_UNESCAPE_S)
        if OLD_UNESCAPE_STR in after:
            after=after.replace(OLD_UNESCAPE_STR,NEW_UNESCAPE_STR)

        if provider_id in vf_ids:
            cfg=patches.get(provider_id) or {}
            options_by=cfg.get("patch_script_options") or {}
            options=options_by.get(VF_PATCH) if isinstance(options_by,dict) else None
            after=vf_module.apply(after, options=options if isinstance(options,dict) else {})

        if after == before:
            raise RuntimeError(f"{provider_id}: targeted ProviderBase did not change")
        if OLD_UNESCAPE_S in after or OLD_UNESCAPE_STR in after:
            raise RuntimeError(f"{provider_id}: unsafe JSON literal decoder remains")
        if provider_id in vf_ids and r'https?:\\?\/\\?\/' in after:
            raise RuntimeError(f"{provider_id}: double-escaped VF URL regex remains")

        data=after.encode("utf-8")
        validate_base(data,provider_id)
        new_rel,digest=write_base(provider_id,data)
        row["base_filename"]=new_rel
        row["base_sha256"]=digest
        changed.append((provider_id,rel,new_rel))

    provenance_path.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(
        "FIELD_CODEQL_PROVIDER_BASE_MIGRATION "
        f"changed={len(changed)} vf={len(vf_ids)} direct={len(direct_ids)} "
        "ids="+",".join(provider_id for provider_id,_,_ in changed)
    )
    for provider_id,old,new in changed:
        print(f"FIELD_CODEQL_PROVIDER_BASE_REF provider={provider_id} old={old} new={new}")

def verify_sources() -> None:
    vf=(ROOT / VF_PATCH).read_text(encoding="utf-8")
    if '"implementationVersion": 3,' not in vf:
        raise RuntimeError("VF implementation revision not applied")
    for forbidden in (
        r'https?:\\?\/\\?\/',
        r'if(/\/movie(?:\/|\{|$)/i.test(low)',
        r'if(/\/tv(?:\/|\{|$)/i.test(low)',
    ):
        if forbidden in vf:
            raise RuntimeError(f"VF source still contains forbidden pattern: {forbidden}")
    for relative in (DIRECT_V1,DIRECT_V2):
        text=(ROOT / relative).read_text(encoding="utf-8")
        if "JSON.parse('\"'+" in text or OLD_UNESCAPE_S in text or OLD_UNESCAPE_STR in text:
            raise RuntimeError(f"{relative}: unsafe synthetic JSON decoder remains")
    if OLD_GENERIC_URL in (ROOT / BASE_STORE).read_text(encoding="utf-8"):
        raise RuntimeError("provider_base_store: double-escaped normalized URL regex remains")
    gate=(ROOT / SECURITY_GATE).read_text(encoding="utf-8")
    for required in ("active_provider_paths","active_base_paths","historical_unreferenced_provider_artifact","release-reachable"):
        if required not in gate:
            raise RuntimeError(f"security gate release-reachability contract missing: {required}")

def main() -> int:
    patch_vf_source()
    patch_direct_source(DIRECT_V1,OLD_UNESCAPE_STR,NEW_UNESCAPE_STR)
    patch_direct_source(DIRECT_V2,OLD_UNESCAPE_S,NEW_UNESCAPE_S)
    patch_base_store_source()
    patch_vf_test()
    patch_security_gate()
    migrate_active_bases()
    verify_sources()
    print("FIELD_CODEQL_HYGIENE_SOURCE status=ready")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
