#!/usr/bin/env python3
"""Synchronize derived manifest rows after targeted provider publication."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
from generate_language_manifests import build_no_anime_manifest, nested_entry, france_only_catalog_rows

ROOT = Path(__file__).resolve().parents[1]

def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise SystemExit(f'{path}: object required')
    return value

def canonical(value: object) -> str:
    return str(value or '').strip().casefold()

def synced_vf(root_manifest: dict[str, Any], current_vf: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    """Refresh shared rows and retain canonical VF-only rows without Global leakage."""
    root_rows={canonical(row.get('id')):row for row in root_manifest.get('scrapers') or [] if isinstance(row,dict) and canonical(row.get('id'))}
    france_rows={canonical(row.get('id')):row for row in france_only_catalog_rows(root=root)}
    if root_rows.keys() & france_rows.keys():
        raise SystemExit('France-only catalog provider duplicated in Global')
    rows=[]
    seen=set()
    for old in current_vf.get('scrapers') or []:
        if not isinstance(old,dict): continue
        identity=canonical(old.get('id'))
        if not identity or identity in seen:
            raise SystemExit(f'VF projection contains empty or duplicate identity: {identity}')
        seen.add(identity)
        if identity in france_rows:
            # Use canonical DATA rather than stale nested publication bytes.
            # Append exclusive rows in the same order as the full generator.
            continue
        source=root_rows.get(identity)
        if source is None:
            raise SystemExit(f'VF projection contains provider absent from root and France-only catalog: {old.get("id")}')
        rows.append(nested_entry(source))
    rows.extend(nested_entry(row) for row in france_rows.values())
    return {'name':f"{root_manifest.get('name','NiakVIO')} — VF uniquement",'version':root_manifest.get('version'),'scrapers':rows}

def expected_all() -> dict[Path,dict[str,Any]]:
    root=load(ROOT/'manifest.json')
    vf=synced_vf(root,load(ROOT/'vf/manifest.json'),root=ROOT)
    return {
        Path('vf/manifest.json'):vf,
        Path('no-anime/manifest.json'):build_no_anime_manifest(root),
        Path('vf-no-anime/manifest.json'):build_no_anime_manifest(vf),
    }

def sync(*,check:bool=False) -> int:
    drift=[]
    for relative,expected in expected_all().items():
        path=ROOT/relative
        if load(path)!=expected:
            drift.append(str(relative))
            if not check:path.write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if check and drift: raise SystemExit('manifest projection parity drift: '+','.join(drift))
    print(f"MANIFEST_PROJECTION_PARITY {'CHECK' if check else 'SYNC'} drift={len(drift)} files={','.join(drift) if drift else '-'}")
    return 0

def main() -> int:
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();return sync(check=a.check)
if __name__=='__main__':raise SystemExit(main())
