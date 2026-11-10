#!/usr/bin/env python3
"""Read-only live provider probe of Brain-generated sandbox candidate.

The offline reverse-repair oracle proves actual CSS parse improvement; this
second probe checks which real network/terminal stage blocks production. A
GitHub Actions SUCCESS means *the probe was executed*, not a provider repair.
"""
from __future__ import annotations
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts/adaptive_runtime"))
sys.path.insert(1,str(ROOT/"scripts"))
import runtime_repair as brain  # noqa: E402

manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
entries=[x for x in manifest.get("scrapers",[]) if str(x.get("id") or "").lower()=="4khdhub"]
assert len(entries)==1, entries
relative=str(entries[0]["filename"])
original=(ROOT/relative).read_bytes()
assert b"NIAKVIO_4KHDHUB_RUNTIME_V1" in original
probe=ROOT/"tests/brain_oracles/4khdhub/live_runtime_probe.cjs"
BEGIN="/* STARTFIX:PROVIDER.4KHDHUB.RUNTIME.V1 */"
END="/* CLOSEFIX:PROVIDER.4KHDHUB.RUNTIME.V1 */"
def isolate(raw: bytes) -> str:
    text=raw.decode("utf-8")
    assert text.count(BEGIN)==1 and text.count(END)==1
    return text[text.index(BEGIN):text.index(END)+len(END)]
fixtures=[
  {"name":"The Colony (2021)","tmdbId":"760873","mediaType":"movie",
   "title":"The Colony","year":2021},
  {"name":"Breaking Bad S01E01","tmdbId":"1396","mediaType":"tv",
   "title":"Breaking Bad","year":2008,"season":1,"episode":1},
]
results=[]
with tempfile.TemporaryDirectory(prefix="brain-real-upstream-") as tmp:
    stage=Path(tmp)
    source=stage/relative
    source.parent.mkdir(parents=True)
    source.write_bytes(original)
    candidate={"key":"published:4khdhub","canonical_id":"4khdhub",
               "local_path":relative,"bytes":len(original),"source":"nuvio",
               "local_patches":[]}
    repaired,error=brain.create_repair_candidate(
        stage,candidate,brain.HTML_CLASS_TOKEN_PROFILE,1)
    assert error is None and repaired is not None,(error,repaired)
    after=(stage/repaired["local_path"]).read_bytes()
    assert original!=after
    assert source.read_bytes()==original
    assert b"NUVIO_HTML_CLASS_TOKEN_EXACT_V1" in after
    paths={}
    for name,data in (("published_original",original),("brain_sandbox_repaired",after)):
        path=stage/(name+".cjs")
        path.write_text(isolate(data),encoding="utf-8")
        paths[name]=path
    for fixture in fixtures:
        for variant,path in paths.items():
            cmd=["node",str(probe),str(path),json.dumps(fixture,separators=(",",":"))]
            proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,
                                timeout=125,check=False)
            lines=[line for line in proc.stdout.splitlines() if line.startswith("{")]
            if not lines:
                raise AssertionError(f"{variant}:{fixture['name']} did not produce probe evidence; "
                                     f"exit={proc.returncode} stderr={proc.stderr[-500:]}")
            row=json.loads(lines[-1])
            if not isinstance(row.get("attemptedRequests"),int) or row["attemptedRequests"]<1:
                raise AssertionError(f"{variant}:{fixture['name']} no actual upstream attempt: {row}")
            row["variant"]=variant
            row["exitCode"]=proc.returncode
            results.append(row)
            print("FIELD_BRAIN_LIVE_PROVIDER_PROBE",json.dumps(row,sort_keys=True),flush=True)

summary={
    "provider":"4khdhub","source":"published_content_addressed",
    "brainProfile":"html_class_token_exact_v1",
    "candidateMaterialized":True,"originalUnmodified":True,
    "realUpstreamAttempted":True,
    "actualTerminalMediaProven":False,
    "decodedCorrectWorkEpisodeAndSubtitles":False,
    "rows":results,
}
out=Path(os.environ.get("NIAKVIO_BRAIN_ORACLE_LIVE_OUTPUT", ""))
if str(out) not in {"",".","/"}:
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print("FIELD_BRAIN_LIVE_ORACLE_RESULT",
      json.dumps({"cases":len(results),"sourceScope":"4khdhub",
                  "materialized":True,"networkAttempted":True,
                  "terminalProven":False,"decodedIdentityProven":False,
                  "no_provider_publish":True},sort_keys=True))
