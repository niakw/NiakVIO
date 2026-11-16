#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_SOURCE=ROOT/"manifest.json"
DEFAULT_VF_SOURCE=ROOT/"vf"/"manifest.json"
DEFAULT_OUTPUT=ROOT/"manifest-hub46.json"


def load_json(path):
 v=json.loads(path.read_text(encoding="utf-8"))
 if not isinstance(v,dict): raise SystemExit(f"expected JSON object: {path}")
 return v


def cid(value):
 return str(value or "").strip().casefold().replace("_","-")


def _root_filename(filename, *, projection):
 raw=str(filename or "").strip().replace("\\","/")
 if projection=="vf" and raw.startswith("../"):
  raw=raw[3:]
 path=Path(raw)
 if path.is_absolute() or ".." in path.parts or len(path.parts)!=2 or path.parts[0]!="providers" or not path.name.endswith(".js"):
  raise SystemExit(f"{projection}: active provider outside providers/: {filename}")
 return path.as_posix()


def _active_rows(source, *, projection):
 rows=[]
 seen=set()
 for raw in source.get("scrapers") or []:
  if not isinstance(raw,dict) or raw.get("enabled") is False:
   continue
  row=dict(raw)
  pid=cid(row.get("id"))
  if not pid or pid in seen:
   raise SystemExit(f"{projection}: invalid/duplicate active provider id: {pid!r}")
  row["filename"]=_root_filename(row.get("filename"),projection=projection)
  seen.add(pid)
  rows.append((pid,row))
 return rows


def build(source, vf_source=None):
 general=_active_rows(source,projection="global")
 ordered=[]
 by_id={}
 for pid,row in general:
  by_id[pid]=row
  ordered.append(pid)

 if vf_source is not None:
  for pid,row in _active_rows(vf_source,projection="vf"):
   if pid in by_id:
    if by_id[pid] != row:
     raise SystemExit(f"Global/VF active provider metadata diverges: {pid}")
    continue
   by_id[pid]=row
   ordered.append(pid)

 if not ordered:
  raise SystemExit("no active providers")

 out=dict(source)
 out["scrapers"]=[by_id[pid] for pid in ordered]
 out["labScope"]={
  "kind":"current-active-projection-union" if vf_source is not None else "current-active-providers",
  "providerCount":len(ordered),
  "authority":"Global+France current manifest references" if vf_source is not None else "providers/ current manifest references",
 }
 return out


def generate(source_path,output_path,check=False,vf_source_path=None):
 source_path=source_path.resolve()
 if vf_source_path is None and source_path==DEFAULT_SOURCE.resolve() and DEFAULT_VF_SOURCE.is_file():
  vf_source_path=DEFAULT_VF_SOURCE
 vf_doc=load_json(vf_source_path) if vf_source_path is not None else None
 out=build(load_json(source_path),vf_doc)
 rendered=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
 if check:
  if not output_path.is_file() or output_path.read_text(encoding="utf-8")!=rendered:
   raise SystemExit("derived active manifest is stale")
  print(f"FIELD_ACTIVE_MANIFEST_CHECK providers={len(out['scrapers'])} status=clean path={output_path}")
  return
 output_path.write_text(rendered,encoding="utf-8")
 print(f"FIELD_ACTIVE_MANIFEST_GENERATED providers={len(out['scrapers'])} path={output_path}")


def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source",type=Path,default=DEFAULT_SOURCE)
 p.add_argument("--vf-source",type=Path,default=None,help="optional France projection; defaults to vf/manifest.json for the repository production manifest")
 p.add_argument("--matrix",type=Path,default=None,help="deprecated; active scope comes from published projections")
 p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
 p.add_argument("--check",action="store_true")
 a=p.parse_args()
 generate(a.source,a.output,check=a.check,vf_source_path=a.vf_source)
 return 0


if __name__=="__main__":
 raise SystemExit(main())
