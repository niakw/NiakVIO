#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGETS={"coflix","frenchstream","streamzo","french-manga"}

def patch_embedded_text(text: str) -> tuple[str,int]:
    total=0
    old='return _text(value).replace('
    new='return _text(value).split("\\\\/").join("/").replace('
    if old in text:
        text=text.replace(old,new)
        total+=1
    old_alt=r'|\\\/|'
    if old_alt in text:
        text=text.replace(old_alt,'|')
        total+=text.count('|') >= 0
    old_cond='if (normalized === "\\\\u002f" || normalized === "\\\\/") return "/";'
    new_cond='if (normalized === "\\\\u002f") return "/";'
    if old_cond in text:
        text=text.replace(old_cond,new_cond)
        total+=1
    return text,total

def patch_source() -> None:
    p=ROOT/"scripts/provider_base_store.py"
    before=p.read_text(encoding="utf-8")
    after,count=patch_embedded_text(before)
    if after==before:
        raise RuntimeError("provider_base_store.py: embedded-text pattern not changed")
    p.write_text(after,encoding="utf-8")
    print(f"FIELD_CODEQL_EMBEDDED_SOURCE replacements={count}")

    fp=ROOT/"scripts/provider_patches/frenchstream_dle_catalogue.py"
    before=fp.read_text(encoding="utf-8")
    after=before.replace(
        r'\s*=\s*\\?["\'])([^"\'\\]+)(?:\\?["\'])',
        r'\s*=\s*["\'])([^"\']+)(?:["\'])',
    )
    if after!=before:
        fp.write_text(after,encoding="utf-8")
        print("FIELD_CODEQL_FRENCHSTREAM_ONCLICK source=patched")
    else:
        print("FIELD_CODEQL_FRENCHSTREAM_ONCLICK source=unchanged")

def patch_bases() -> None:
    sys.path.insert(0,str(ROOT/"scripts"))
    from provider_base_store import validate_base, write_base

    prov_path=ROOT/"PROVENANCE.json"
    provenance=json.loads(prov_path.read_text(encoding="utf-8"))
    rows=provenance.get("providers") or {}
    changed=[]
    for provider_id in sorted(TARGETS):
        row=rows.get(provider_id)
        if not isinstance(row,dict):
            raise RuntimeError(f"{provider_id}: missing provenance")
        old_rel=str(row.get("base_filename") or "")
        old_path=ROOT/old_rel
        before=old_path.read_text(encoding="utf-8")
        after,count=patch_embedded_text(before)
        if provider_id=="frenchstream":
            after=after.replace(
                r'\s*=\s*\\?["\'])([^"\'\\]+)(?:\\?["\'])',
                r'\s*=\s*["\'])([^"\']+)(?:["\'])',
            )
        if after==before:
            raise RuntimeError(f"{provider_id}: active base unchanged")
        if r'|\\\/|' in after or 'normalized === "\\\\/"' in after:
            raise RuntimeError(f"{provider_id}: embedded slash regex residue remains")
        data=after.encode("utf-8")
        validate_base(data,provider_id)
        new_rel,digest=write_base(provider_id,data)
        row["base_filename"]=new_rel
        row["base_sha256"]=digest
        changed.append((provider_id,old_rel,new_rel))
    prov_path.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FIELD_CODEQL_EMBEDDED_BASES changed="+str(len(changed))+" ids="+",".join(x[0] for x in changed))
    for provider_id,old,new in changed:
        print(f"FIELD_CODEQL_EMBEDDED_BASE provider={provider_id} old={old} new={new}")

def main() -> int:
    patch_source()
    patch_bases()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
