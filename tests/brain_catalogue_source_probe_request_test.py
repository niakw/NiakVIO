#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("source_request",ROOT/"scripts/build_brain_catalogue_source_probe_request.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
FLAGS={x:False for x in mod.FLAGS}
template={"schemaVersion":1,"probeKind":"catalogue-inline-source-contract",
 "providerId":"anime-sama","fixture":"mushoku-s01e01","catalogueSlug":"mushoku-tensei",
 "season":1,"voice":"vostfr","sourceRunId":"11111111","sourceNiakvioSha":"f"*40,
 "providerArtifactSha256":"f"*64,**FLAGS}
with tempfile.TemporaryDirectory() as td:
 root=Path(td);(root/"providers").mkdir()
 data=b"current\n";(root/"providers/a.js").write_bytes(data);digest=hashlib.sha256(data).hexdigest()
 (root/"manifest.json").write_text(json.dumps({"scrapers":[{"id":"anime-sama","filename":"providers/a.js"}]}))
 row={"provider":"anime-sama","fixture":"mushoku-s01e01","nativeRunId":"45321345600",
  "sourceNiakvioSha":"a"*40,"providerArtifactSha256":digest,"manifestScope":"manifest.json",
  "appSelected":True,"readerEvidenceComplete":True,"nativeExtractionZeroObserved":True,
  "nativeSourceScriptShapePatterns":["script_http_missing","script_html_2xx"],**FLAGS}
 ledger={"schemaVersion":1,"authority":"official-android-tv-emulator-diagnostic-only",
  "primaryClient":"tv","rows":[row],**FLAGS}
 request=mod.build(root,template,ledger,"45321345600")
 assert request and request["sourceRunId"]=="45321345600"
 assert request["sourceNiakvioSha"]=="a"*40 and request["providerArtifactSha256"]==digest
 assert request["catalogueSlug"]=="mushoku-tensei"
 # Historical provenance in the template is deliberately ignored.
 assert request["sourceRunId"]!=template["sourceRunId"]
 assert mod.build(root,template,ledger,"45321345601") is None
 drift=json.loads(json.dumps(ledger));drift["rows"][0]["providerArtifactSha256"]="e"*64
 assert mod.build(root,template,drift,"45321345600") is None
 positive=json.loads(json.dumps(ledger));positive["rows"][0]["nativeExtractionZeroObserved"]=False
 assert mod.build(root,template,positive,"45321345600") is None
 no_shape=json.loads(json.dumps(ledger));no_shape["rows"][0]["nativeSourceScriptShapePatterns"]=[]
 assert mod.build(root,template,no_shape,"45321345600") is None
 forged=json.loads(json.dumps(ledger));forged["rows"][0]["publicationAuthority"]=True
 assert mod.build(root,template,forged,"45321345600") is None
print("Brain catalogue source request uses exact current native parent and ignores stale template provenance")
