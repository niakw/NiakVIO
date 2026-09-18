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
        {"id":"partial","enabled":True,"filename":rel,"canonicalSupportedTypes":["movie","tv"]},
        {"id":"retained","enabled":False,"filename":rel,"canonicalSupportedTypes":["movie"]},
    ]}
    node={"providers":[
        {"providerId":"p","bundleSha256":sha,"lanes":{"movie":{"state":"uncertified","attempts":[{"debugStage":"provider_network_zero_result"}]}}},
        {"providerId":"partial","bundleSha256":sha,"lanes":{"movie":{"state":"certified","fixtureSlug":"x","attempts":[]},"tv":{"state":"uncertified","attempts":[{"debugStage":"provider_network_zero_result"}]}}},
    ]}
    native_log=d/"tv.log"
    native_log.write_text(f"FIELD_NATIVE_PROVIDER_STATUS client=tv provider=p status=FULL lanes=movie:positive bundle_sha={sha}\\n", encoding="utf-8")
    native=mod.parse_native_logs([native_log])
    assert native["p"][0]["bundleSha256"] == sha
    out=mod.build(manifest,node=node,registry={},native=native)
    row=out["providers"][0]
    assert row["certified"] is True
    assert row["disableEligible"] is False
    assert row["lanes"]["movie"]["state"]=="certified"
    assert any(e["source"]=="native_lab_exact_bundle" for e in row["lanes"]["movie"]["positiveEvidence"])
    assert out["manifestProviderCount"] == 3
    assert out["activeCandidateCount"] == 2
    assert out["certifiedManifestCount"] == 1
    assert out["greenManifestCount"] == 2
    assert out["greenActiveCount"] == 2
    assert out["fullCertificationRatio"] == round(1 / 3, 4)
    assert out["autoCertificationRatio"] == round(2 / 3, 4)
    assert out["activeAutoCertificationRatio"] == 1.0

    stale_native={"p":[{"source":"native_lab","client":"tv","status":"FULL","lanes":{"movie":"positive"},"log":"stale.log","bundleSha256":"0"*64}]}
    stale_out=mod.build(manifest,node=node,registry={},native=stale_native)
    stale_row=stale_out["providers"][0]
    assert stale_row["certified"] is False
    assert stale_row["lanes"]["movie"]["positiveEvidence"] == []
    assert stale_row["lanes"]["movie"]["inconclusiveOrNegativeEvidence"][-1]["scope"] == "unscoped_or_bundle_mismatch"

    no_native=mod.build(manifest,node=node,registry={},native={})
    row=no_native["providers"][0]
    assert row["certified"] is False
    assert row["activationAction"]=="native_fallback_then_brain"
    assert row["disableEligible"] is False
    assert row["lanes"]["movie"]["inconclusiveOrNegativeEvidence"][0]["authoritativeForDisable"] is False

print("provider activation consensus tests passed")
