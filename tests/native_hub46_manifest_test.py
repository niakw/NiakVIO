#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
from current_provider_scope import active_provider_count
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import generate_hub46_manifest as active_manifest
from current_provider_scope import active_provider_ids

def main()->int:
 source=active_manifest.load_json(ROOT/"manifest.json")
 built=active_manifest.build(source)
 rows=built.get("scrapers") or []
 expected=active_provider_ids()
 actual=[str(row.get("id") or "").strip().casefold().replace("_","-") for row in rows]
 assert set(actual)==expected,(set(actual)-expected,expected-set(actual))
 assert len(set(actual))==len(actual)
 for row in rows:
  filename=str(row.get("filename") or "")
  assert filename.startswith("providers/"),(row.get("id"),filename)
  assert not filename.startswith("/") and ".." not in Path(filename).parts
 scope=built.get("labScope") or {}
 assert int(scope.get("providerCount") or 0)==len(expected)
 assert scope.get("authority")=="providers/ current manifest references"
 if (ROOT/"manifest-hub46.json").exists():
  active_manifest.generate(ROOT/"manifest.json",ROOT/"manifest-hub46.json",check=True)
 for script in ("run_native_corpus_desktop_suite.sh","run_native_corpus_mobile_suite.sh","run_native_corpus_tv_suite.sh","run_native_corpus_ios_suite.sh"):
  text=(ROOT/"scripts"/script).read_text(encoding="utf-8")
  assert "native-hub46/manifest.json" in text,script
 print(f"native current-provider manifest contract passed providers={len(expected)} transport=native-hub46/manifest.json")
 return 0
if __name__=="__main__": raise SystemExit(main())
