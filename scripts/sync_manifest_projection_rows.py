#!/usr/bin/env python3
"""Synchronize derived manifest rows after targeted provider publication."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
from generate_language_manifests import build_no_anime_manifest, nested_entry

ROOT = Path(__file__).resolve().parents[1]

def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise SystemExit(f'{path}: object required')
    return value

def canonical(value: object) -> str:
    return str(value or '').strip().casefold()

def synced_vf(root_manifest: dict[str, Any], current_vf: dict[str, Any]) -> dict[str, Any]:
    root_rows={canonical(row.get('id')):row for row in root_manifest.get('scrapers') or [] if isinstance(row,dict) and canonical(row.get('id'))}
    rows=[]
    for old in current_vf.get('scrapers') or []:
        if not isinstance(old,dict): continue
        source=root_rows.get(canonical(old.get('id')))
        if source is None: raise SystemExit(f'VF projection contains provider absent from root: {old.get("id")}')
        rows.append(nested_entry(source))
    return {'name':f"{root_manifest.get('name','NiakVIO')} — VF uniquement",'version':root_manifest.get('version'),'scrapers':rows}

def expected_all() -> dict[Path,dict[str,Any]]:
    root=load(ROOT/'manifest.json')
    vf=synced_vf(root,load(ROOT/'vf/manifest.json'))
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
