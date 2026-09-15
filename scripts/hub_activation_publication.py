#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"scripts"))
from current_provider_scope import active_provider_ids, disabled_provider_ids, visible_provider_ids, assert_directory_contract

def load(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8"))
def cid(v): return str(v or "").strip().casefold().replace("_","-")

def compute_scope():
 assert_directory_contract(); manifest=load("manifest.json"); rows=[r for r in manifest.get("scrapers") or [] if isinstance(r,dict)]
 active=active_provider_ids(); disabled=disabled_provider_ids(); visible=visible_provider_ids(); row_ids={cid(r.get("id")) for r in rows}
 if row_ids!=visible: raise AssertionError(f"manifest/folder identity mismatch missing={sorted(visible-row_ids)} extra={sorted(row_ids-visible)}")
 return {"schemaVersion":3,"authority":"providers/ + provider-disabled/ physical current folders","catalogueProviderCount":len(visible),"enabledProviderCount":len(active),"disabledProviderCount":len(disabled),"enabledProviders":sorted(active),"disabledProviders":sorted(disabled),"repairScope":"providers-active-only","nativeLabPolicy":"reuse-existing-artifacts-first; rerun-only-for-specific-fix-validation"}

def write_scope(scope): (ROOT/"automation/hub-activation-scope.json").write_text(json.dumps(scope,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def verify_catalog(scope):
 catalog=load("provider_catalog.json"); providers=[r for r in catalog.get("providers") or [] if isinstance(r,dict)]; a=set(); d=set()
 for row in providers:
  scraper=row.get("scraper") or {}; pid=cid(row.get("canonicalId") or scraper.get("id"));
  if not pid: continue
  (d if scraper.get("enabled") is False else a).add(pid)
 if a!=set(scope["enabledProviders"]) or d!=set(scope["disabledProviders"]): raise AssertionError("provider_catalog activation differs from provider folders")
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--write-scope",action="store_true"); ap.add_argument("--verify-catalog",action="store_true"); ap.add_argument("--append-memory",action="store_true"); args=ap.parse_args(); scope=compute_scope()
 if args.write_scope: write_scope(scope)
 if args.verify_catalog: verify_catalog(scope)
 print("HUB_ACTIVATION_SCOPE",f"visible={scope['catalogueProviderCount']}",f"enabled={scope['enabledProviderCount']}",f"disabled={scope['disabledProviderCount']}")
 return 0
if __name__=="__main__": raise SystemExit(main())
