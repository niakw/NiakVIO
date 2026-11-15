#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path
from current_provider_scope import active_provider_rows

ROOT=Path(__file__).resolve().parents[1]

def canonical_id(value)->str:
    return str(value or "").strip().casefold().replace("_","-")

def normalize_projection_row(row:dict, *, france:bool)->dict:
    current=dict(row)
    filename=str(current.get("filename") or "").strip()
    if france and filename.startswith("../"):
        filename=filename[3:]
    current["filename"]=filename
    return current

def projection_rows(manifest_path:Path, france_manifest_path:Path|None=None)->dict[str,dict]:
    payload=json.loads(manifest_path.read_text(encoding="utf-8"))
    by_id={}
    for row in payload.get("scrapers") or []:
        if not isinstance(row,dict):
            continue
        pid=canonical_id(row.get("id"))
        if not pid or pid in by_id:
            raise SystemExit(f"invalid/duplicate provider id in {manifest_path}: {pid}")
        by_id[pid]=normalize_projection_row(row,france=False)
    if france_manifest_path is None and manifest_path.resolve()==(ROOT/"manifest.json").resolve():
        france_manifest_path=ROOT/"vf"/"manifest.json"
    if france_manifest_path is not None and france_manifest_path.is_file():
        vf=json.loads(france_manifest_path.read_text(encoding="utf-8"))
        seen=set()
        for row in vf.get("scrapers") or []:
            if not isinstance(row,dict):
                continue
            pid=canonical_id(row.get("id"))
            if not pid or pid in seen:
                raise SystemExit(f"invalid/duplicate provider id in {france_manifest_path}: {pid}")
            seen.add(pid)
            projected=normalize_projection_row(row,france=True)
            existing=by_id.get(pid)
            if existing is not None:
                if (bool(existing.get("enabled") is not False) != bool(projected.get("enabled") is not False)
                    or str(existing.get("filename") or "") != str(projected.get("filename") or "")):
                    raise SystemExit(f"{pid}: Global/France projection asset or enabled-state mismatch")
                continue
            by_id[pid]=projected
    return by_id

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,default=ROOT/"manifest.json")
    p.add_argument("--stage",type=Path,default=ROOT/"staging-published")
    p.add_argument("--france-manifest",type=Path,default=None,help="Optional France projection for targeted union tests.")
    p.add_argument("--provider",action="append",default=[],help="Optional exact provider id filter; may be repeated.")
    args=p.parse_args()
    requested={canonical_id(x) for x in args.provider if str(x or "").strip()}
    # Targeted Learning must scale with the requested cohort, not the full
    # catalogue. When explicit providers are supplied, validate only those
    # manifest rows/files. Full physical-folder validation remains the default
    # unfiltered publication contract.
    if requested:
        by_id=projection_rows(args.manifest,args.france_manifest)
        missing=sorted(requested-set(by_id))
        if missing: raise SystemExit("published provider stage missing requested ids: "+",".join(missing))
        rows=[]
        for pid in sorted(requested):
            row=by_id[pid]
            filename=str(row.get("filename") or "")
            if row.get("enabled") is False or not filename.startswith("providers/"):
                raise SystemExit(f"{pid}: requested provider is not active published Provider v3")
            path=(ROOT/filename).resolve()
            path.relative_to((ROOT/"providers").resolve())
            if not path.is_file():
                raise SystemExit(f"{pid}: requested published provider asset missing: {filename}")
            rows.append(row)
    elif args.manifest.resolve() != (ROOT/"manifest.json").resolve():
        payload=json.loads(args.manifest.read_text(encoding="utf-8"))
        rows=[r for r in payload.get("scrapers") or [] if isinstance(r,dict) and r.get("enabled") is not False and str(r.get("filename") or "").startswith("providers/")]
    else:
        rows=active_provider_rows()
    if args.stage.exists(): shutil.rmtree(args.stage)
    (args.stage/"providers").mkdir(parents=True,exist_ok=True)
    candidates=[]; seen=set()
    for row in rows:
        pid=str(row["id"]).strip().casefold()
        if not pid or pid in seen: raise SystemExit(f"invalid/duplicate active provider id: {pid}")
        seen.add(pid)
        rel=Path(str(row["filename"]))
        src=(ROOT/rel).resolve(); src.relative_to((ROOT/"providers").resolve())
        data=src.read_bytes(); digest=hashlib.sha256(data).hexdigest()
        dst=args.stage/"providers"/src.name; dst.write_bytes(data)
        metadata=dict(row); metadata["publishedFilename"]=str(rel).replace("\\","/")
        candidates.append({"key":f"published-v3:{pid}","source":"published-v3","upstream_id":pid,"canonical_id":pid,"local_path":f"providers/{src.name}","sha256":digest,"metadata":metadata,"canonical_metadata":{"contentLanguage":row.get("contentLanguage") or [],"formats":row.get("formats") or [],"descriptions":[row.get("description")] if row.get("description") else []},"published_exact_bytes":True,"repair_allowed":False})
    if not candidates: raise SystemExit("no active published providers")
    registry={"schema_version":1,"source":"published-provider-v3","candidate_count":len(candidates),"excluded_count":0,"repair_allowed":False,"candidates":candidates}
    (args.stage/"candidates.json").write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"FIELD_PUBLISHED_V3_STAGE providers={len(candidates)} repair_allowed=false filtered={'true' if requested else 'false'}")
    return 0
if __name__=="__main__": raise SystemExit(main())
