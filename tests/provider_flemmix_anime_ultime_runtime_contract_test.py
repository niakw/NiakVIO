#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]

flemmix=(ROOT/"scripts/provider_patches/flemmix_runtime_v1.py").read_text(encoding="utf-8")
anime=(ROOT/"scripts/provider_patches/anime_ultime_runtime_v1.py").read_text(encoding="utf-8")

assert "NIAKVIO_FLEMMIX_RUNTIME_V1" in flemmix
assert '"/search?q="' in flemmix
assert "video-server-tab" in flemmix and "episode-server-tab" in flemmix
assert "saison-" in flemmix and "_crawlDirectMedia" in flemmix
assert "arm.haglund.dev" not in flemmix

assert "NIAKVIO_ANIME_ULTIME_RUNTIME_V1" in anime
assert "/MenuSearch.html" in anime
assert "/VideoPlayer.html" in anime
assert "data-serie" in anime and "data-focus" in anime
assert "arm.haglund.dev" not in anime

assert ov["flemmix"]["provider_lego_scripts"] == ["scripts/provider_patches/flemmix_runtime_v1.py"]
assert ov["flemmix"]["provider_lego_options"]["scripts/provider_patches/flemmix_runtime_v1.py"]["base"] == "https://flemmix.me"
assert '"base": "https://flemmix.me"' in flemmix
assert ov["anime-ultime"]["provider_lego_scripts"] == ["scripts/provider_patches/anime_ultime_runtime_v1.py"]

print("Flemmix and Anime-Ultime provider runtime contracts passed")
