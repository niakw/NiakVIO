#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("cleanup",ROOT/"scripts/cleanup_stale_pr_branch.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
doc=json.loads((ROOT/"cleanup/stale-4khdhub-branch-2026-11-06.json").read_text())
mod.verify_policy(doc)
for field,value in (("branch","main"),("prNumber",269),("sha","a"*40),("failedProofRun",42303162753)):
    altered={**doc,field:value}
    try:mod.verify_policy(altered)
    except AssertionError:pass
    else:raise AssertionError("Unsafe stale branch retirement accepted "+field)
for old in (
    ".github/workflows/temp-anime-sama-config-rematerialize.yml",
    ".github/workflows/temp-repair28-observable-resume.yml",
    ".github/workflows/temp-resume-repair28-post-apply.yml",
):
    assert not (ROOT/old).exists(), "one-shot workflow not removed "+old
assert (ROOT/".github/workflows/temp-current-bytes-full-provider-census.yml").exists()
assert (ROOT/".github/workflows/temp-targeted-regression-recovery.yml").exists()
print("NIAKVIO_STALE_WORKFLOW_AND_BRANCH_CLEANUP_POLICY_OK")
