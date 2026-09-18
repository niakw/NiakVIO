#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/enforce_provider_activation_contract.py"
spec = importlib.util.spec_from_file_location("activation", MODULE)
assert spec and spec.loader
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)

manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
row = next(
    item for item in manifest["scrapers"]
    if isinstance(item, dict) and item.get("enabled") is not False and activation.semantic_types(item)
)
path = ROOT / row["filename"]
sha = hashlib.sha256(path.read_bytes()).hexdigest()
required = sorted(activation.semantic_types(row))
provider = activation.cid(row["id"])

cert = {
    "providerId": provider,
    "bundleSha256": sha,
    "requiredTypes": required,
    "certifiedTypes": required,
    "certified": True,
}
ok, reason = activation.exact_certified(row, cert)
assert ok and reason == "exact_bundle_all_lanes_playable", (ok, reason)

wrong_sha = dict(cert, bundleSha256="0" * 64)
assert activation.exact_certified(row, wrong_sha)[1] == "bundle_sha_mismatch"

if len(required) > 1:
    narrowed = dict(cert, requiredTypes=required[:-1], certifiedTypes=required[:-1])
else:
    narrowed = dict(cert, requiredTypes=["tv" if required[0] != "tv" else "movie"], certifiedTypes=[])
assert activation.exact_certified(row, narrowed)[1] == "certificate_lane_scope_mismatch"

uncertified = dict(cert, certified=False, certifiedTypes=[])
assert activation.exact_certified(row, uncertified)[0] is False

synthetic_manifest = {"version": "x", "scrapers": [dict(row)]}
certification = {
    "authority": "exact-bundle-playable-lane-certification-v1",
    "providers": [uncertified],
}
out, report = activation.enforce(synthetic_manifest, certification, allow_reenable=False)
assert out["scrapers"][0]["enabled"] is False
assert out["scrapers"][0]["activationState"] == "repair-learning-required"
assert report["disabledNow"] == [provider]
assert report["manifestProviderCount"] == 1
assert report["fullManifestCensus"] is False
assert report["bootstrapYieldRatio"] is None

full_certification = dict(certification)
full_certification.update({
    "fullManifestCensus": True,
    "manifestProviderCount": 1,
    "selectedProviderCount": 1,
})
full_out, full_report = activation.enforce(synthetic_manifest, full_certification, allow_reenable=False)
assert full_report["fullManifestCensus"] is True
assert full_report["manifestProviderCount"] == 1
assert full_report["exactCertifiedManifestCount"] == 0
assert full_report["bootstrapYieldRatio"] == 0.0

print("provider activation exact-bundle contract tests passed")
