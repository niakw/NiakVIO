#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from provider_base_store import canonical_id
from provider_patch_blocks import decode_managed_data
from current_provider_scope import active_provider_rows, disabled_provider_rows
DECL="const NIAKVIO_PROVIDER_MODEL = Object.freeze("

def validate_bundle(text:str,provider_id:str)->None:
 canonical=canonical_id(provider_id)
 if "NIAKVIO_PROVIDER_BASE_OWNED_V3" not in text: return
 fix_id=f"PROVIDER.{canonical.upper()}.CONFIG.V1"; start=f"/* STARTFIX:{fix_id} */"; close=f"/* CLOSEFIX:{fix_id} */"
 if text.count(start)!=1 or text.count(close)!=1: raise ValueError(f"{canonical}: CONFIG Lego cardinality invalid")
 if text.count(DECL)!=1: raise ValueError(f"{canonical}: NIAKVIO_PROVIDER_MODEL declaration count={text.count(DECL)}")
 if not (text.index(start)<text.index(DECL)<text.index(close)): raise ValueError(f"{canonical}: model declaration outside CONFIG Lego")
 model=decode_managed_data(text,fix_id)
 if canonical_id(str(model.get("providerId") or ""))!=canonical: raise ValueError(f"{canonical}: CONFIG providerId mismatch")
 if text.count("/* BEGIN NIAKVIO_PROVIDER */")!=1 or text.count("/* END NIAKVIO_PROVIDER */")!=1: raise ValueError(f"{canonical}: Provider envelope cardinality invalid")

def validate_manifest(path:Path)->None:
 if path.resolve()==(ROOT/"manifest.json").resolve(): rows=active_provider_rows()+disabled_provider_rows()
 else:
  payload=json.loads(path.read_text(encoding="utf-8")); rows=[r for r in payload.get("scrapers") or [] if isinstance(r,dict)]
 seen=set(); active=disabled=0
 for row in rows:
  provider_id=canonical_id(str(row.get("id") or ""))
  if not provider_id or provider_id in seen: raise ValueError(f"invalid/duplicate provider id: {provider_id!r}")
  seen.add(provider_id); relative=str(row.get("filename") or ""); bundle=(ROOT/relative).resolve()
  if row.get("enabled") is False:
   if not relative.startswith("provider-disabled/") or (ROOT/"provider-disabled").resolve() not in bundle.parents: raise ValueError(f"{provider_id}: disabled bundle outside provider-disabled/: {relative}")
   disabled+=1
  else:
   if not relative.startswith("providers/") or (ROOT/"providers").resolve() not in bundle.parents: raise ValueError(f"{provider_id}: active bundle outside providers/: {relative}")
   active+=1
  if not bundle.is_file(): raise ValueError(f"{provider_id}: bundle missing: {relative}")
  validate_bundle(bundle.read_text(encoding="utf-8"),provider_id)
 print(f"final published Provider CONFIG tests passed active={active} disabled={disabled} visible={len(rows)}")

def main()->int:
 parser=argparse.ArgumentParser(); parser.add_argument("--manifest",type=Path,default=ROOT/"manifest.json"); parser.add_argument("--expected",type=int,default=None,help="deprecated compatibility argument; cardinality is derived from provider identities")
 args=parser.parse_args(); validate_manifest(args.manifest.resolve())
 if args.expected is not None: print(f"FIELD_PROVIDER_EXPECTED_IGNORED requested={args.expected} authority=provider-folders")
 return 0
if __name__=="__main__": raise SystemExit(main())
