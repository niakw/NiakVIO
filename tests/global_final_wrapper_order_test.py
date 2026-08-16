#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location(
    "apply_provider_overrides_final_order",
    ROOT / "scripts" / "apply_provider_overrides.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CATALOGUE = "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2"
MEDIA = "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1"
SAFETY = "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1"
HLS = "NUVIO_HLS_RUNTIME_INTEGRITY_V1"


def assert_final_order(text: str, label: str) -> None:
    positions = {marker: text.find(marker) for marker in (CATALOGUE, MEDIA, SAFETY, HLS)}
    missing = [marker for marker, position in positions.items() if position < 0]
    assert not missing, f"{label}: missing final wrappers: {missing}"
    assert positions[CATALOGUE] < positions[MEDIA] < positions[SAFETY] < positions[HLS], (
        label,
        positions,
    )


# A future HTML provider must recover catalogue/player media first, preserve its
# scoped playback context, run the final safety layer, and only then validate
# the final HLS graph.  HLS validation running before media recovery is a
# regression because it only sees intermediate embed/player rows.
future = b"async function getStreams(){return []};module.exports={getStreams};\n"
patched, _records = module.apply_overrides("kurage", future, phase="discovery")
assert_final_order(patched.decode("utf-8"), "future-html-provider")

# Reapplication must converge to the same effective order instead of toggling
# wrappers between runs.
repatched, _records2 = module.apply_overrides("kurage", patched, phase="discovery")
assert_final_order(repatched.decode("utf-8"), "future-html-provider-reapply")

# StreamZo is the positive historical sentinel: site -> player/embed -> final
# media must retain Referer/Origin/cookies for native players.  Exercise the
# exact currently published bundle through the same global reapplication path,
# rather than special-casing a fixture title in the engine.
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
streamzo = next(
    row
    for row in manifest.get("scrapers", [])
    if isinstance(row, dict) and str(row.get("id", "")).casefold() == "streamzo"
)
streamzo_path = ROOT / str(streamzo["filename"])
source = streamzo_path.read_bytes()
streamzo_patched, _streamzo_records = module.apply_overrides("streamzo", source, phase="discovery")
streamzo_text = streamzo_patched.decode("utf-8")
assert "NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT" in streamzo_text
assert "captureCookies" in streamzo_text
assert "cookieHeader" in streamzo_text
assert_final_order(streamzo_text, "streamzo-published")

streamzo_repatched, _streamzo_records2 = module.apply_overrides(
    "streamzo", streamzo_patched, phase="discovery"
)
assert_final_order(streamzo_repatched.decode("utf-8"), "streamzo-published-reapply")

print("global final media wrapper order tests passed")
