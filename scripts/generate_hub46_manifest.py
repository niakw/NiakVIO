#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DEFAULT_SOURCE=ROOT/"manifest.json"; DEFAULT_OUTPUT=ROOT/"manifest-hub46.json"

def load_json(path):
 v=json.loads(path.read_text(encoding="utf-8"));
 if not isinstance(v,dict): raise SystemExit(f"expected JSON object: {path}")
 return v
def build(source):
 rows=[]; seen=set()
 for row in source.get("scrapers") or []:
  if not isinstance(row,dict) or row.get("enabled") is False: continue
  pid=str(row.get("id") or "").strip().casefold(); filename=str(row.get("filename") or "").strip()
  if not pid or pid in seen: raise SystemExit(f"invalid/duplicate active provider id: {pid!r}")
  if not filename.startswith("providers/"): raise SystemExit(f"{pid}: active provider outside providers/: {filename}")
  seen.add(pid); rows.append(row)
 if not rows: raise SystemExit("no active providers")
 out=dict(source); out["scrapers"]=rows; out["labScope"]={"kind":"current-active-providers","providerCount":len(rows),"authority":"providers/ current manifest references"}; return out
def generate(source_path,output_path,check=False):
 out=build(load_json(source_path)); rendered=json.dumps(out,ensure_ascii=False,indent=2)+"\n"
 if check:
  if not output_path.is_file() or output_path.read_text(encoding="utf-8")!=rendered: raise SystemExit("derived active manifest is stale")
  print(f"FIELD_ACTIVE_MANIFEST_CHECK providers={len(out['scrapers'])} status=clean path={output_path}"); return
 output_path.write_text(rendered,encoding="utf-8"); print(f"FIELD_ACTIVE_MANIFEST_GENERATED providers={len(out['scrapers'])} path={output_path}")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--source",type=Path,default=DEFAULT_SOURCE); p.add_argument("--matrix",type=Path,default=None,help="deprecated; active scope comes from providers/"); p.add_argument("--output",type=Path,default=DEFAULT_OUTPUT); p.add_argument("--check",action="store_true"); a=p.parse_args(); generate(a.source,a.output,check=a.check); return 0
if __name__=="__main__": raise SystemExit(main())
