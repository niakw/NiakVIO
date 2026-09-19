#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "scripts/provider_patches/movieshunt_runtime_v1.py").read_text(encoding="utf-8")
ov = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["movieshunt"]
hubs = json.loads((ROOT / "provider-hubs.json").read_text(encoding="utf-8"))["providers"]["movieshunt"]

for needle in (
    "NIAKVIO_MOVIESHUNT_RUNTIME_V1",
    "/?s=",
    "abhilinks",
    "hubcloud",
    "vcloud",
    "fsl-buckets",
    "NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1",
    "/search.html?q=",
    "/lookup.php?q=",
    "dynamicLookup",
    "post_title",
    "permalink",
    ".html",
):
    assert needle.lower() in src.lower(), needle

assert hubs["direct"] == "https://movieshunt.run/"
assert hubs["direct_authority"] == "explicit_current"
assert ov["official_site"] == "https://movieshunt.run"
assert ov["provider_lego_scripts"] == ["scripts/provider_patches/movieshunt_runtime_v1.py"]
opts = ov["provider_lego_options"]["scripts/provider_patches/movieshunt_runtime_v1.py"]
assert opts["base"] == "https://movieshunt.run"
assert int(opts["maxStreams"]) == 6
assert ov["learned_routes"] == ["/search.html?q={query}", "/?s={query}"], ov["learned_routes"]
assert ov["search_request_plan"][0]["base"] == "https://movieshunt.run"
assert ov["search_request_plan"][0]["route"] == "/search.html?q={query}"
# JSON lookup is only a dynamic fallback on the actual host reached by the
# current /search.html response; it is not promoted as direct-domain authority.
assert "movieshunt.monster" not in ov["learned_routes"]
# Current live proof uses hubcloud.ist and needs one more bounded hop
# (HubCloud -> HuntPlay -> terminal HLS) than the old cx-only path.
assert r"hubcloud\.[a-z0-9.-]+\/(?:drive|video)\/" in src
assert "_crawlDirectMedia([url],referer,3)" in src
js=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER","{}")
subprocess.run(["node","-e","new Function(process.argv[1]);",js],check=True)

print("MoviesHunt provider runtime/domain contract passed")
