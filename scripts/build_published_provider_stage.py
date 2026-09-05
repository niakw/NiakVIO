#!/usr/bin/env python3
"""Build a health-check stage from the exact currently published Provider v3 bytes."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,default=ROOT/"manifest.json")
    p.add_argument("--stage",type=Path,default=ROOT/"staging-published")
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    rows=[r for r in manifest.get("scrapers") or [] if isinstance(r,dict) and r.get("id") and r.get("filename")]
    if len(rows)!=96:
        raise SystemExit(f"published Provider v3 stage requires 96 rows, got {len(rows)}")
    if args.stage.exists():
        shutil.rmtree(args.stage)
    (args.stage/"providers").mkdir(parents=True,exist_ok=True)
    candidates=[]
    seen=set()
    for row in rows:
        pid=str(row["id"]).strip().casefold()
        if pid in seen: raise SystemExit(f"duplicate provider id: {pid}")
        seen.add(pid)
        rel=Path(str(row["filename"]))
        src=(ROOT/rel).resolve()
        src.relative_to((ROOT/"providers").resolve())
        data=src.read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        dst=args.stage/"providers"/src.name
        dst.write_bytes(data)
        metadata=dict(row)
        metadata["publishedFilename"]=str(rel).replace("\\","/")
        candidates.append({
            "key":f"published-v3:{pid}",
            "source":"published-v3",
            "upstream_id":pid,
            "canonical_id":pid,
            "local_path":f"providers/{src.name}",
            "sha256":digest,
            "metadata":metadata,
            "canonical_metadata":{
                "contentLanguage":row.get("contentLanguage") or [],
                "formats":row.get("formats") or [],
                "descriptions":[row.get("description")] if row.get("description") else [],
            },
            "published_exact_bytes":True,
            "repair_allowed":False,
        })
    registry={
        "schema_version":1,
        "source":"published-provider-v3",
        "candidate_count":len(candidates),
        "excluded_count":0,
        "repair_allowed":False,
        "candidates":candidates,
    }
    (args.stage/"candidates.json").write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"FIELD_PUBLISHED_V3_STAGE providers={len(candidates)} repair_allowed=false")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
