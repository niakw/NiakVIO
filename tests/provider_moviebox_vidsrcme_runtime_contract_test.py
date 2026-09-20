#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["moviebox"]
lego="scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py"

for token in (
    "NIAKVIO_MOVIEBOX_VIDSRCME_RUNTIME_V1",
    "function hydrateImdb",
    "/stream/series/",
    "/stream/movie/",
    "current-cinescrape-json-first-legacy-vidsrcme-fallback",
    '"/vs_src.php?type="+encodeURIComponent(q.type)',
    'typeof _crawlDirectMedia==="function"',
    'g.__niakvioProviderRuntimeResolverV1={provider:"moviebox",resolve:resolve}',
):
    assert token in src, token

opts=ov["provider_lego_options"][lego]
assert opts["cinescrapeBase"].startswith("https://pengu.uk/%7B"), opts
current=opts.get("currentBases") or []
assert len(current)>=2, current
assert current[0]["base"].startswith("https://pengu.uk/%7B"), current
assert current[1]["base"].startswith("https://moviebox-cfa7.onrender.com/"), current
assert current[1]["referer"]=="https://moviebox-cfa7.onrender.com/", current
assert opts["legacyBase"]=="https://vidsrcme.ru", opts
assert ov["provider_lego_scripts"]==[lego]
assert ov["route_data_state"]=="repair"
assert ov["repair_disposition"]["quarantined"] is False
assert "/stream/movie/{imdbId}.json" in ov["candidate_learned_routes"]
assert "/stream/series/{imdbId}:{season}:{episode}.json" in ov["candidate_learned_routes"]

ledger=(ROOT/"automation/USER-PROVIDER-EVIDENCE-LEDGER.md").read_text(encoding="utf-8")
assert "MovieBox manual positive" in ledger
assert "sagaciousslumber" in ledger

print("MovieBox current Cinescrape + legacy vidsrcme contract passed")
