#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGETS={"coflix","frenchstream","streamzo","french-manga"}
SAFE_HELPER="function unpackPackers(){return[]}\n"

def strip_legacy_packer(text: str, label: str) -> str:
    start=text.find("function decodeLiteral(raw){")
    end=text.find("function decodeVidzy",start)
    if start<0 or end<0:
        raise RuntimeError(f"{label}: legacy packer helper block not found")
    block=text[start:end]
    if "function unpackPackers(source)" not in block:
        raise RuntimeError(f"{label}: unpackPackers missing")
    return text[:start]+SAFE_HELPER+text[end:]

def patch_source() -> None:
    path=ROOT/"scripts/provider_patches/nuvio_tv_target_media_v3.py"
    before=path.read_text(encoding="utf-8")
    after=strip_legacy_packer(before,str(path))
    path.write_text(after,encoding="utf-8")
    print("FIELD_CODEQL_PACKER_SOURCE action=removed")

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
            raise RuntimeError(f"{provider_id}: provenance missing")
        old_rel=str(row.get("base_filename") or "")
        old_path=ROOT/old_rel
        before=old_path.read_text(encoding="utf-8")
        after=strip_legacy_packer(before,provider_id)
        if "decodeLiteral(" in after or "function unpackPackers(source)" in after:
            raise RuntimeError(f"{provider_id}: legacy packer decoder remains")
        data=after.encode("utf-8")
        validate_base(data,provider_id)
        new_rel,digest=write_base(provider_id,data)
        row["base_filename"]=new_rel
        row["base_sha256"]=digest
        changed.append((provider_id,old_rel,new_rel))
    prov_path.write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FIELD_CODEQL_PACKER_BASES action=removed count="+str(len(changed))+" ids="+",".join(x[0] for x in changed))
    for provider_id,old,new in changed:
        print(f"FIELD_CODEQL_PACKER_BASE provider={provider_id} old={old} new={new}")

def main() -> int:
    patch_source()
    patch_bases()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
