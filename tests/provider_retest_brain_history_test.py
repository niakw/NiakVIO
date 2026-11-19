#!/usr/bin/env python3
"""Negative Retest experience retained per provider without leaking sensitive URLs."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "scripts/merge_retest_brain_evidence_history.py"
spec = importlib.util.spec_from_file_location("retest_memory", p)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def latest(provider, run, *, digest="a"*64):
    return {
        "schemaVersion": 1, "authority": "current-retest-observation-only",
        "sourceNiakvioSha": "f"*40, "sourceCensusRunId": f"{run}-retest",
        "proofAuthority": False, "publicationAuthority": False,
        "rows": [{
            "provider": provider, "providerArtifactSha256": digest, "lane": "anime",
            "status": "playable_unverified", "debugStage": "provider_returned_streams",
            "fixture": {"mediaType": "anime", "tmdbId": "95479", "season": 1, "episode": 1},
            "raw": 2, "playable": 2, "verified": 0,
            "identityReasons": ["duration_incomplete_hls", "insufficient_identity_metadata"],
            "url": "https://signed.example/private?t=SECRET",
            "sourceTitle": "secret",
            "proofAuthority": False, "publicationAuthority": False,
            "nativePlaybackAuthority": False,
        }],
    }

history = mod.merge({}, latest("alpha", 123))
history = mod.merge(history, latest("beta", 124))
assert history["providerCount"] == 2
assert history["observationCount"] == 2
assert [x["provider"] for x in history["rows"]] == ["beta", "alpha"]
assert all(x["publicationAuthority"] is False and x["nativePlaybackAuthority"] is False
           for x in history["rows"])
raw = json.dumps(history)
assert "signed.example" not in raw and "SECRET" not in raw and "secret" not in raw
again = mod.merge(history, latest("alpha", 123))
assert again["observationCount"] == 2
assert again["rows"][0]["provider"] == "alpha"  # current replay recency
other_version = mod.merge(again, latest("alpha", 125, digest="b"*64))
assert other_version["observationCount"] == 3
assert {x["providerArtifactSha256"] for x in other_version["rows"] if x["provider"] == "alpha"} == {"a"*64, "b"*64}
for i in range(126, 150):
    other_version = mod.merge(other_version, latest("beta", i))
assert len([x for x in other_version["rows"] if x["provider"] == "beta"]) == 10
assert any(x["provider"] == "alpha" for x in other_version["rows"])
negative = latest("gamma", 150)
negative["rows"][0]["nativePlaybackAuthority"] = True
assert mod.merge(other_version, negative)["providerCount"] == 2
negative = latest("gamma", 150)
negative["proofAuthority"] = True
assert mod.merge(other_version, negative)["providerCount"] == 2

workflow = (ROOT / ".github/workflows/provider-retest.yml").read_text()
runner = (ROOT / "scripts/run_provider_retest.py").read_text()
assert "provider_retest_brain_history_test.py" in workflow
assert "automation/provider-retest-brain-evidence-history.json" in workflow
assert "merge_retest_brain_evidence_history.py" in runner
print("Brain Retest sanitized multi-provider history contract passed")
