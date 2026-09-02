#!/usr/bin/env python3
"""Rebuild only domain-affected published Provider v3 artifacts, proving all others stable."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
from materialize_provider_v3_all import materialize_all

ROOT=Path(__file__).resolve().parents[1]

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--changes",type=Path,required=True)
    p.add_argument("--manifest",type=Path,default=ROOT/"manifest.json")
    p.add_argument("--overrides",type=Path,default=ROOT/"provider-overrides.json")
    args=p.parse_args()
    requested={str(v).strip().casefold() for v in (load(args.changes).get("changed") or []) if str(v).strip()}
    if not requested:
        print("FIELD_PROVIDER_V3_DOMAIN_REFRESH providers=0 changed=0")
        return 0
    current=load(args.manifest)
    current_rows={str(r.get("id") or "").casefold():r for r in current.get("scrapers") or [] if isinstance(r,dict)}
    if len(current_rows)!=96: raise SystemExit(f"expected 96 providers, got {len(current_rows)}")
    unknown=sorted(requested-set(current_rows))
    if unknown: raise SystemExit(f"domain refresh unknown providers: {unknown}")
    old_files={pid:ROOT/str(row["filename"]) for pid,row in current_rows.items()}
    old_hash={pid:sha(path) for pid,path in old_files.items()}
    old_context=os.environ.get("NUVIO_PROVIDER_V3_CONTEXT")
    try:
        os.environ["NUVIO_PROVIDER_V3_CONTEXT"]="main"
        with tempfile.TemporaryDirectory(prefix="niakvio-domain-refresh-") as raw:
            tmp=Path(raw)
            tm=tmp/"manifest.json"
            tm.write_bytes(args.manifest.read_bytes())
            report=materialize_all(
                source_manifest_path=tm,
                overrides_path=args.overrides,
                output_dir=tmp/"providers",
                report_path=tmp/"provider-v3-materialization.json",
            )
            rebuilt=load(tm)
            rebuilt_rows={str(r.get("id") or "").casefold():r for r in rebuilt.get("scrapers") or [] if isinstance(r,dict)}
            changed=set()
            for pid,row in rebuilt_rows.items():
                path=tmp/"providers"/Path(str(row["filename"])).name
                digest=sha(path)
                if digest!=old_hash[pid]: changed.add(pid)
            unexpected=sorted(changed-requested)
            if unexpected:
                raise SystemExit("domain refresh changed non-requested providers: "+",".join(unexpected))
            # A route DATA update may be metadata-only for a provider; that's valid.
            for pid in changed:
                new_row=rebuilt_rows[pid]
                src=tmp/"providers"/Path(str(new_row["filename"])).name
                dst=ROOT/str(new_row["filename"])
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,dst)
            args.manifest.write_bytes(tm.read_bytes())
            (ROOT/"provider-v3-materialization.json").write_bytes((tmp/"provider-v3-materialization.json").read_bytes())
            referenced={str(r.get("filename") or "") for r in rebuilt.get("scrapers") or [] if isinstance(r,dict)}
            for pid in changed:
                old=old_files[pid]
                rel=str(old.relative_to(ROOT)).replace("\\","/")
                if rel not in referenced and old.exists(): old.unlink()
            print(
                f"FIELD_PROVIDER_V3_DOMAIN_REFRESH providers={len(requested)} "
                f"changed={len(changed)} generation={str(report.get('generation') or '')[:16]} "
                "repair=false"
            )
    finally:
        if old_context is None: os.environ.pop("NUVIO_PROVIDER_V3_CONTEXT",None)
        else: os.environ["NUVIO_PROVIDER_V3_CONTEXT"]=old_context
    return 0
if __name__=="__main__":
    raise SystemExit(main())
