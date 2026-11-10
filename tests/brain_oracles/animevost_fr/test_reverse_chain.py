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
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT / "scripts"))
sys.path.insert(0,str(ROOT / "scripts" / "provider_patches"))
from anime_catalogue_runtime_common import apply_runtime  # noqa: E402

SOURCE = "module.exports={getStreams:async()=>[]};\n"
# The dated pre-correction producer is fetched from Git, never re-created
# from today's source. This remains a genuine reverse-engineering differential.
HISTORICAL_SHA = "f43011bb408d769586d30727cb832f46d2eb225d"
old = subprocess.run(
    ["git", "show", HISTORICAL_SHA + ":scripts/provider_patches/anime_catalogue_runtime_common.py"],
    cwd=ROOT,capture_output=True,text=True,timeout=20,check=True,
).stdout
module = types.ModuleType("historical_anime_catalogue_runtime_common")
exec(compile(old, "historical_anime_catalogue_runtime_common.py", "exec"), module.__dict__)

opts=dict(
    managed_fix_id="PROVIDER.ANIMEVOST-FR.RUNTIME.V1",
    marker="NIAKVIO_ANIMEVOST_FR_RUNTIME_V1",
    defaults={
        "mode":"animevost_api","base":"https://animevost.fr",
        "provider":"animevost-fr","name":"AnimeVOST.fr",
    }
)
BROKEN = module.apply_runtime(SOURCE, **opts)
CURRENT = apply_runtime(SOURCE, **opts)
assert "function requestMeta(args)" in BROKEN and "function requestMeta(args)" in CURRENT
assert "async function animevost(meta)" in BROKEN and "async function animevost(meta)" in CURRENT

with tempfile.TemporaryDirectory(prefix="niakvio-oracle-") as temp:
    old_path = Path(temp) / "historical-unsafe-runtime.cjs"
    new_path = Path(temp) / "current-shared-runtime.cjs"
    old_path.write_text(BROKEN, encoding="utf-8")
    new_path.write_text(CURRENT, encoding="utf-8")
    result = subprocess.run(
        ["node",str(Path(__file__).with_name("run_oracle.cjs")),str(old_path),str(new_path)],
        cwd=ROOT,capture_output=True,text=True,timeout=20,check=False,
    )
    if result.returncode:
        raise AssertionError(
            "Real runtime-to-reference oracle comparison failed\n"
            + result.stdout[-1600:] + "\n" + result.stderr[-3000:]
        )
    assert "baseline_wrong_s00=true" in result.stdout, result.stdout
    assert "subtitle_cross_episode_rejected=true" in result.stdout
    assert "shared_runtime_correct_s00=true" in result.stdout
    assert "shared_runtime_no_episode_fallback=true" in result.stdout
    assert "secondary_search_empty_primary_recovered=true" in result.stdout
    print(result.stdout.strip())
