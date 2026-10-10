#!/usr/bin/env python3
"""Reproduce a simultaneous Brain/census main push without publishing stale bytes."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/persist_repair_race_evidence.sh"

def git(*args, cwd=None):
    return subprocess.check_output(["git",*args],cwd=cwd,text=True,stderr=subprocess.STDOUT).strip()

with tempfile.TemporaryDirectory(prefix="brain-race-") as td:
    root=Path(td);bare=root/"remote.git";a=root/"a";b=root/"b"
    git("init","--bare",str(bare))
    git("clone",str(bare),str(a))
    git("checkout","-b","main",cwd=a)
    git("config","user.email","test@local.invalid",cwd=a)
    git("config","user.name","Brain Replay",cwd=a)
    (a/"PROVIDER_CENSUS_STATUS.md").write_text("old census\n")
    (a/"code.py").write_text("approved = True\n")
    git("add",".",cwd=a);git("commit","-m","baseline",cwd=a)
    git("push","origin","main",cwd=a)
    base=git("rev-parse","HEAD",cwd=a)
    git("--git-dir",str(bare),"symbolic-ref","HEAD","refs/heads/main")
    git("clone",str(bare),str(b))
    git("config","user.email","test@local.invalid",cwd=b)
    git("config","user.name","Concurrent Brain",cwd=b)
    # A completed an older census but lost the race to the newer main.
    (a/"PROVIDER_CENSUS_STATUS.md").write_text("stale FALSE FULL\n")
    git("add",".",cwd=a);git("commit","-m","older evidence",cwd=a)
    (b/"code.py").write_text("approved = False\n")
    (b/"PROVIDER_CENSUS_STATUS.md").write_text("current verified census\n")
    git("add",".",cwd=b);git("commit","-m","new authoritative brain",cwd=b)
    git("push","origin","main",cwd=b)
    report=root/"prior.json"
    report.write_text(json.dumps({"schemaVersion":2,"selectedProviders":["4khdhub"],"acceptedRepairCount":0}))
    result=subprocess.run(
        ["bash",str(SCRIPT),str(report),"38016186246",base],
        cwd=a,capture_output=True,text=True
    )
    assert result.returncode==0,(result.stdout,result.stderr)
    assert "preserved=true evidence_only=true" in result.stdout,result.stdout
    git("fetch","origin","main",cwd=b)
    git("reset","--hard","origin/main",cwd=b)
    assert (b/"code.py").read_text()=="approved = False\n"
    assert (b/"PROVIDER_CENSUS_STATUS.md").read_text()=="current verified census\n"
    result_file=b/"automation/provider-brain-repair-38016186246.json"
    assert json.loads(result_file.read_text())["acceptedRepairCount"]==0
    provenance=json.loads((b/"automation/provider-brain-repair-38016186246-stale-provenance.json").read_text())
    assert provenance["publicationAllowed"] is False
    assert provenance["currentBytePlaybackAuthority"] is False
    assert provenance["testedSha"]==base
    assert provenance["requiresFreshMaterializationAndReplay"] is True

print("Repair concurrent-main evidence-only persistence contract passed")
