#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "build_provider_activation_consensus.py"
spec = importlib.util.spec_from_file_location("consensus", MODULE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory(dir=ROOT) as td:
    d=Path(td)
    bundle=d/"p.js"; bundle.write_text("module.exports={getStreams:async()=>[]};\n", encoding="utf-8")
    rel=bundle.relative_to(ROOT).as_posix()
    sha=mod.sha256_file(bundle)
    manifest={"version":"x","scrapers":[
        {"id":"p","enabled":True,"filename":rel,"canonicalSupportedTypes":["movie"]},
        {"id":"retained","enabled":False,"filename":rel,"canonicalSupportedTypes":["movie"]},
    ]}
    node={"providers":[{"providerId":"p","bundleSha256":sha,"lanes":{"movie":{"state":"uncertified","attempts":[{"debugStage":"provider_network_zero_result"}]}}}]}
    native={"p":[{"source":"native_lab","client":"tv","status":"FULL","lanes":{"movie":"positive"},"log":"tv.log"}]}
    out=mod.build(manifest,node=node,registry={},native=native)
    row=out["providers"][0]
    assert row["certified"] is True
    assert row["disableEligible"] is False
    assert row["lanes"]["movie"]["state"]=="certified"
    assert any(e["source"]=="native_lab" for e in row["lanes"]["movie"]["positiveEvidence"])
    assert out["manifestProviderCount"] == 2
    assert out["activeCandidateCount"] == 1
    assert out["certifiedManifestCount"] == 1
    assert out["autoCertificationRatio"] == 0.5
    assert out["activeAutoCertificationRatio"] == 1.0

    no_native=mod.build(manifest,node=node,registry={},native={})
    row=no_native["providers"][0]
    assert row["certified"] is False
    assert row["activationAction"]=="native_fallback_then_brain"
    assert row["disableEligible"] is False
    assert row["lanes"]["movie"]["inconclusiveOrNegativeEvidence"][0]["authoritativeForDisable"] is False

print("provider activation consensus tests passed")
