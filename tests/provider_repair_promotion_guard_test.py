#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from runtime_repair import compare_results

parent = {"status": "no_streams", "score": 10, "evidence": {"streams_playable": 0}, "tests": []}
false_positive = {
    "status": "healthy",
    "score": 72,
    "evidence": {
        "streams_playable": 1,
        "required_fixture_categories": ["movie", "anime"],
        "healthy_fixture_categories": ["movie"],
    },
    "tests": [{"streams_playable": 1}],
}
accepted, reason = compare_results(parent, false_positive)
assert not accepted and reason == "required_category_playable_proof:anime", (accepted, reason)
root = Path(__file__).resolve().parents[1]
worker = (root / "scripts/provider_worker.cjs").read_text(encoding="utf-8")
sanitizer = (root / "scripts/provider_patches/stream_output_sanitizer.py").read_text(encoding="utf-8")
assert "NUVIO_NON_MEDIA_ASSET_GUARD_V1" in worker
assert "non_media_asset_host" in worker
assert '"implementationVersion": 5' in sanitizer
assert "NUVIO_EMBED_HTML_ALLOWLIST_V1" in sanitizer
assert "embedLike" in sanitizer
print("provider repair promotion guard tests passed")
