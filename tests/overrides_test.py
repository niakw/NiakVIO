#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides


# Stable replacements still happen during discovery.
patched, records = apply_overrides("movix", b'const API="https://api.movix.cash/";')
assert b"api.movix.show" in patched
assert b"api.movix.cash" not in patched
assert records and records[0]["count"] == 1


def test_staged_artifact_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        (stage / "providers" / "gowaru").mkdir(parents=True)
        upstream = b'const APIS=["https://api.movix.cloud","https://api.movix.cash"];'
        output, patch_records = apply_overrides("movix", upstream)
        target = stage / "providers" / "gowaru" / "movix.js"
        target.write_bytes(output)
        registry = {
            "candidates": [
                {
                    "key": "gowaru:movix",
                    "canonical_id": "movix",
                    "upstream_id": "movix",
                    "local_path": "providers/gowaru/movix.js",
                    "upstream_sha256": hashlib.sha256(upstream).hexdigest(),
                    "sha256": hashlib.sha256(output).hexdigest(),
                    "local_patches": patch_records,
                }
            ]
        }
        (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_override_pipeline.py"),
                "--stage",
                str(stage),
            ],
            check=True,
        )


def test_domain_overrides() -> None:
    source = b"const BASE='https://french-stream.one';"
    output, patch_records = apply_overrides("frenchstream", source)
    assert b"frenchstream.food" in output
    assert b"french-stream.one" not in output
    assert any(
        row.get("from") == "french-stream.one"
        and row.get("to") == "frenchstream.food"
        for row in patch_records
    )


def synthetic_metadata_bundle() -> bytes:
    return b'''function G(a,b,c){return c()}function W(t,n){return function(A,D,T,x){return G(this,arguments,function*(f,g,h,_,m={}){let $=null,s=1,M="x";let P=yield zw(n(f,g,h,_,{signal:$}),s,M);return P})}}function zw(v){return v}function P(c,f,g,h){return G(this,arguments,function*(t,n,i,s,a={}){let D=yield X2(t,n,{season:i});if(!D||D.length===0)return[];return D})}function X2(){return Promise.resolve([])}module.exports={getStreams:async()=>[]}'''


def test_runtime_profiles_are_not_blindly_applied() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text())
    for name, profile in config["patch_profiles"].items():
        assert profile["phase"] == "runtime", name
        assert profile["auto_apply"] is False, name
        assert "provider_id" not in profile, name
        assert profile["runtime_trigger"], name

    source = synthetic_metadata_bundle()
    discovery, discovery_records = apply_overrides("arbitrary-provider", source)
    assert discovery == source
    assert not any(row.get("type") == "patch_profile" for row in discovery_records)

    runtime, runtime_records = apply_overrides(
        "another-arbitrary-provider",
        source,
        phase="runtime",
        profile_names=["metadata_context_recovery"],
    )
    assert b"[Nuvio Runtime Repair] Using fixture title metadata" in runtime
    assert b"Object.assign({},m||{},{signal:$})" in runtime
    assert any(
        row.get("type") == "patch_profile"
        and row.get("profile") == "metadata_context_recovery"
        for row in runtime_records
    )
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(runtime)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            check=True,
        )


test_staged_artifact_contract()
test_domain_overrides()
test_runtime_profiles_are_not_blindly_applied()
print("override tests passed")
