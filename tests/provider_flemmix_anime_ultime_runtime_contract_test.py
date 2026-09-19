#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]

flemmix=(ROOT/"scripts/provider_patches/flemmix_runtime_v1.py").read_text(encoding="utf-8")
anime=(ROOT/"scripts/provider_patches/anime_ultime_runtime_v1.py").read_text(encoding="utf-8")

assert "NIAKVIO_FLEMMIX_RUNTIME_V1" in flemmix
assert "function runtimeBase()" in flemmix
assert 'm&&(m.officialSite||m.knownSite)||c.base' in flemmix
assert '"/index.php?do=search&subaction=search&search_start=0&full_search=0&story="' in flemmix
assert "video-server-tab" in flemmix and "episode-server-tab" in flemmix
assert "saison-" in flemmix and "_crawlDirectMedia" in flemmix
assert "arm.haglund.dev" not in flemmix

assert "NIAKVIO_ANIME_ULTIME_RUNTIME_V1" in anime
assert "/MenuSearch.html" in anime
assert "/VideoPlayer.html" in anime
assert "data-serie" in anime and "data-focus" in anime
assert "arm.haglund.dev" not in anime

assert ov["flemmix"]["provider_lego_scripts"] == ["scripts/provider_patches/flemmix_runtime_v1.py"]
assert "api_recipe" not in ov["flemmix"]
assert ov["flemmix"]["learned_routes"]==["/index.php?do=search&subaction=search&search_start=0&full_search=0&story={query}"]
assert ov["flemmix"]["search_request_plan"][0]["route"]=="/index.php?do=search&subaction=search&search_start=0&full_search=0&story={query}"
assert ov["flemmix"]["provider_lego_options"]["scripts/provider_patches/flemmix_runtime_v1.py"]["base"] == "https://flemmix.cloud"
assert '"base": "https://flemmix.cloud"' in flemmix
assert ov["flemmix"]["official_site"] == "https://flemmix.cloud"
flemmix_js=flemmix.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
assert flemmix_js.count("c.base")==2, "only runtimeBase fallback may reference the legacy Flemmix config base"
compiled=flemmix_js.replace("CONFIG_PLACEHOLDER","{}")
subprocess.run(["node","-e","new Function(process.argv[1]);",compiled],check=True)
assert ov["anime-ultime"]["provider_lego_scripts"] == ["scripts/provider_patches/anime_ultime_runtime_v1.py"]

print("Flemmix and Anime-Ultime provider runtime contracts passed")
