#!/usr/bin/env python3
"""One failing real provider runtime -> isolated repaired test oracle.

The reference provider lives in tests/brain_oracles only; never publish it.
Tests use a deterministic simulated API response to prove causality, not to
claim that animevost.fr returns playable media on the current network.
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT / "scripts" / "provider_patches"))
from anime_catalogue_runtime_common import apply_runtime  # noqa: E402

SOURCE = "module.exports={getStreams:async()=>[]};\n"
BROKEN = apply_runtime(SOURCE,
    managed_fix_id="PROVIDER.ANIMEVOST-FR.RUNTIME.V1",
    marker="NIAKVIO_ANIMEVOST_FR_RUNTIME_V1",
    defaults={
        "mode":"animevost_api","base":"https://animevost.fr",
        "provider":"animevost-fr","name":"AnimeVOST.fr",
    }
)
assert "function requestMeta(args)" in BROKEN
assert "async function animevost(meta)" in BROKEN

with tempfile.TemporaryDirectory(prefix="niakvio-oracle-") as temp:
    generated = Path(temp) / "published-runtime-before-repair.cjs"
    generated.write_text(BROKEN, encoding="utf-8")
    result = subprocess.run(
        ["node",str(Path(__file__).with_name("run_oracle.cjs")),str(generated)],
        cwd=ROOT,capture_output=True,text=True,timeout=20,check=False,
    )
    if result.returncode:
        raise AssertionError(
            "Real runtime-to-reference oracle comparison failed\n"
            + result.stdout[-1600:] + "\n" + result.stderr[-3000:]
        )
    assert "baseline_wrong_s00=true" in result.stdout, result.stdout
    assert "subtitle_cross_episode_rejected=true" in result.stdout
    print(result.stdout.strip())
