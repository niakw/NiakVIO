#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGETS={"coflix","frenchstream","streamzo","french-manga"}

def replace_all(text: str, old: str, new: str) -> tuple[str,int]:
    count=text.count(old)
    return text.replace(old,new),count

def patch_source(path: str, replacements: list[tuple[str,str]], *, required_any: bool=True) -> None:
    p=ROOT/path
    text=p.read_text(encoding="utf-8")
    total=0
    for old,new in replacements:
        text,count=replace_all(text,old,new)
        total+=count
    if required_any and total==0:
        raise RuntimeError(f"{path}: no expected CodeQL hygiene pattern found")
    p.write_text(text,encoding="utf-8")
    print(f"FIELD_CODEQL_SOURCE_PATCH path={path} replacements={total}")

def patch_sources() -> None:
    slash=(r'.replace(/\\\//g,"/")', r'.split("\\/").join("/")')
    optional_url=(r'https?:\\?\/\\?\/', r'https?:\/\/')
    patch_source("scripts/provider_patches/coflix_exact_catalogue.py",[
        optional_url,slash,
        ('function playerRows(html,pageUrl,title){var out=[]',
         'function playerRows(html,pageUrl,title){html=String(html||"").split("\\/").join("/");var out=[]'),
        ('re.exec(String(html||""))','re.exec(html)'),
    ])
    patch_source("scripts/provider_patches/frenchstream_detail_players.py",[optional_url,slash])
    patch_source("scripts/provider_patches/frenchstream_dle_catalogue.py",[
        slash,
        (r'\\?["\']', r'["\']'),
        (r'[^"\'\\]+', r'[^"\']+'),
    ])
    for path in (
        "scripts/provider_patches/streamzo_public_catalogue.py",
        "scripts/provider_patches/streamzo_public_catalogue_v2.py",
        "scripts/provider_patches/global_catalogue_alias_recovery_v2.py",
        "scripts/provider_patches/vf_catalogue_recovery.py",
    ):
        patch_source(path,[slash],required_any=False)

def patch_active_bases() -> None:
    sys.path.insert(0,str(ROOT/"scripts"))
    from provider_base_store import validate_base, write_base

    prov_path=ROOT/"PROVENANCE.json"
    provenance=json.loads(prov_path.read_text(encoding="utf-8"))
    rows=provenance.get("providers") or {}
    changed=[]
    for provider_id in sorted(TARGETS):
        row=rows.get(provider_id)
        if not isinstance(row,dict):
            raise RuntimeError(f"{provider_id}: provenance row missing")
        old_rel=str(row.get("base_filename") or "")
        old_path=ROOT/old_rel
        if not old_path.is_file():
            raise RuntimeError(f"{provider_id}: active base missing {old_rel}")
        before=old_path.read_text(encoding="utf-8")
        after=before
        after=after.replace(r'https?:\\?\/\\?\/',r'https?:\/\/')
        after=after.replace(r'.replace(/\\\//g,"/")',r'.split("\\/").join("/")')
        # FrenchStream's DLE onclick parser had optional escaped quotes after the
        # surrounding HTML had already been normalized; keep the normalized form.
        if provider_id=="frenchstream":
            after=after.replace(r'\\?["\']',r'["\']')
            after=after.replace(r'[^"\'\\]+',r'[^"\']+')
        if after==before:
            raise RuntimeError(f"{provider_id}: no active-base hygiene replacement applied")
        if r'https?:\\?\/\\?\/' in after:
            raise RuntimeError(f"{provider_id}: double-escaped URL pattern remains")
        if r'.replace(/\\\//g,"/")' in after:
            raise RuntimeError(f"{provider_id}: escaped-slash regex normalizer remains")
        data=after.encode("utf-8")
        validate_base(data,provider_id)
        new_rel,digest=write_base(provider_id,data)
        row["base_filename"]=new_rel
        row["base_sha256"]=digest
        changed.append((provider_id,old_rel,new_rel))
    prov_path.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FIELD_CODEQL_ACTIVE_BASES changed="+str(len(changed))+" ids="+",".join(x[0] for x in changed))
    for provider_id,old,new in changed:
        print(f"FIELD_CODEQL_ACTIVE_BASE provider={provider_id} old={old} new={new}")

def main() -> int:
    patch_sources()
    patch_active_bases()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
