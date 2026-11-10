#!/usr/bin/env python3
"""Reverse-repair the actual published provider bytes through Brain's generic Lego.

Offline deterministic response oracle only. No direct provider source changes,
no accepted repair, no production publication, no decoded playback claim.
"""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts"/"adaptive_runtime"))
sys.path.insert(1,str(ROOT/"scripts"))
import runtime_repair as brain_runtime  # noqa: E402

brain_spec=importlib.util.spec_from_file_location(
    "niakvio_oracle_canonical_brain",ROOT/"scripts/brain_repair_runtime.py")
assert brain_spec and brain_spec.loader
brain_planner=importlib.util.module_from_spec(brain_spec)
brain_spec.loader.exec_module(brain_planner)

manifest = json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
matches = [row for row in manifest["scrapers"]
           if str(row.get("id") or "").casefold()=="4khdhub"]
assert len(matches)==1, matches
relative = matches[0]["filename"]
old_bytes = (ROOT/relative).read_bytes()
assert b"NIAKVIO_4KHDHUB_RUNTIME_V1" in old_bytes
assert b"NUVIO_HTML_CLASS_TOKEN_EXACT_V1" not in old_bytes
original_sha = hashlib.sha256(old_bytes).hexdigest()

# Reuse the exact same real-world HTML and nested classes from the published
# provider regression rather than manufacture a happy-path fixture.
tree=ast.parse((ROOT/"tests"/"provider_4khdhub_runtime_behavior_test.py").read_text())
value=next(node.value for node in tree.body
           if isinstance(node,ast.Assign)
           and any(isinstance(t,ast.Name) and t.id=="js" for t in node.targets))
assert isinstance(value,ast.BinOp) and isinstance(value.left,ast.BinOp)
assert isinstance(value.left.left,ast.Constant)
assert isinstance(value.right,ast.Constant)
prefix=value.left.left.value
suffix=value.right.value

BEGIN="/* STARTFIX:PROVIDER.4KHDHUB.RUNTIME.V1 */"
END="/* CLOSEFIX:PROVIDER.4KHDHUB.RUNTIME.V1 */"
def runtime_span(raw: bytes) -> str:
    text=raw.decode("utf-8")
    assert text.count(BEGIN)==text.count(END)==1
    a=text.index(BEGIN);b=text.index(END,a)+len(END)
    return text[a:b]

def replay(raw: bytes, stage: Path) -> dict:
    script=stage/"exact-published-lego-oracle.cjs"
    script.write_text(prefix+runtime_span(raw)+suffix,encoding="utf-8")
    proc=subprocess.run(["node",str(script)],cwd=ROOT,timeout=22,
                        capture_output=True,text=True,check=False)
    if proc.returncode:
        raise AssertionError("Provider runtime oracle failed: "+proc.stderr[-1200:])
    return json.loads(proc.stdout.splitlines()[-1])

with tempfile.TemporaryDirectory(prefix="brain-html-class-oracle-") as folder:
    stage=Path(folder)
    original=stage/relative
    original.parent.mkdir(parents=True,exist_ok=True)
    original.write_bytes(old_bytes)
    candidate={
        "key":"published:4khdhub", "canonical_id":"4khdhub","source":"nuvio",
        "local_path":relative,"bytes":len(old_bytes),"sha256":original_sha,
        "local_patches":[]
    }
    observation={"status":"no_streams","tests":[{"status":"no_streams","stream_count":0}]}
    evidence=brain_planner._current_source_structural_repair_evidence(
        stage,candidate,observation)
    assert evidence.get("profile")=="html_class_token_exact_v1",evidence
    assert evidence["sourceSha256"]==original_sha,evidence
    # Run the real Brain JS decision over this *same* published source SHA.
    planner_input={
        "mode":"repair","policy":{
            "production":{
                "negativeExperimentMemory":{
                    "rotateExperimentAfterFailures":1,"maxVariantsPerSignature":5},
                "maxHypotheses":3,"maxMutationsPerProvider":2,
                "maxRepeatedSignature":2,"maxGeneratedBytesPerProvider":180000,
                "maxElapsedMsPerProvider":45000,
            },"skillMaturity":{},
        },
        "negativeMemory":[],"historicalSolutions":[],"llmGuidance":[],
        "learnedSkills":[],
        "items":[{
            "key":candidate["key"],
            "candidate":{"canonical_id":candidate["canonical_id"],
                         "metadata":{"supportedTypes":["movie","tv"]},
                         "censusPrior":{"status":"ROUTE PROVEN",
                                        "dominantIssue":"provider_network_zero_result"},
                         "structuralRepairEvidence":evidence},
            "result":{"status":"no_streams",
                      "evidence":{"streams_playable":0,"streams_returned":0},
                      "tests":[{"status":"no_streams",
                                "failure_class":"content_lookup_completed_no_streams",
                                "fixture":{"category":"movie","mediaType":"movie"},
                                "stream_count":0,"streams_playable":0,
                                "network_observations":[{"status":200,"ok":True,
                                                         "stage":"search"}]}]},
            "state":{},
        }],
    }
    planned=subprocess.run(
        ["node",str(ROOT/"engine_v2/scripts/plan-repairs.mjs")],
        cwd=ROOT,input=json.dumps(planner_input),text=True,capture_output=True,
        check=False,timeout=24)
    assert planned.returncode==0,planned.stderr
    selected=json.loads(planned.stdout)["plans"][candidate["key"]]
    assert selected["action"]=="probe-targeted-repair",selected
    assert selected["allowedProfiles"][0]=="html_class_token_exact_v1",selected
    assert selected["sourceStructuralProfileSelected"] is True,selected
    brain_planner.reset_runtime_state()
    brain_planner.PLANS[candidate["key"]]=selected
    matching=brain_planner.wrap_matching_profiles(brain_runtime.matching_profiles)
    chosen=matching(candidate,observation,old_bytes.decode("utf-8"),config={})
    assert chosen and chosen[0]==brain_runtime.HTML_CLASS_TOKEN_PROFILE,chosen
    repaired,error=brain_runtime.create_repair_candidate(
        stage,candidate,chosen[0],1
    )
    assert error is None,(error,repaired)
    assert repaired is not None
    repaired_bytes=(stage/repaired["local_path"]).read_bytes()
    assert repaired["sha256"]==hashlib.sha256(repaired_bytes).hexdigest()
    assert repaired_bytes!=old_bytes
    assert original.read_bytes()==old_bytes,"Published source mutated in sandbox"
    assert b"NUVIO_HTML_CLASS_TOKEN_EXACT_V1" in repaired_bytes
    profile=(repaired.get("runtime_repair") or {}).get("strategy")
    assert profile=="html_class_token_exact_v1"
    before=replay(old_bytes,stage)
    after=replay(repaired_bytes,stage)
    assert not before["movie"] and not before["tv"],before
    assert len(after["movie"])==1 and len(after["tv"])==1,after
    assert after["movie"][0]["url"]=="https://media.workers.dev/colony.mkv"
    assert after["tv"][0]["url"]=="https://media.workers.dev/bb-s01e01.mkv"
    assert "S01E01" in after["tv"][0]["title"]
    assert any("/the-colony-movie-7978/" in u for u in after["fetchTrace"])
    assert any("/breaking-bad-series-1385/" in u for u in after["fetchTrace"])
    print("FIELD_BRAIN_HTML_CLASS_REVERSE_REPLAY "+
          json.dumps({
            "provider":"4khdhub","current_published_sha256":original_sha,
            "repair_profile":profile,"strategy_applied_in_sandbox":True,
            "source_bytes_modified":False,"mock_movie_before":0,
            "mock_movie_after":1,"mock_tv_before":0,"mock_tv_after":1,
            "identity_proof":"fixture-label-only","network_real":False,
            "decoded_playback_verified":False,"brain_plan_selected":True,
            "published_repair":False
          },sort_keys=True))
