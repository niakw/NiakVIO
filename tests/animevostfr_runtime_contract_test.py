#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=(ROOT/"scripts/provider_patches/animevostfr_runtime_v1.py").read_text(encoding="utf-8")
overrides=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["animevostfr"]
hubs=json.loads((ROOT/"provider-hubs.json").read_text(encoding="utf-8"))["providers"]["animevostfr"]
assert "NIAKVIO_ANIMEVOSTFR_RUNTIME_V1" in p
assert 'c.base+"/?s="+encodeURIComponent' in p
assert '/animes\\/' in p or '/animes/' in p
assert "episodeScore" in p
assert "searchLabel" in p
assert "(?:alt|title)=" in p
assert 'mark="/animes/"' in p
assert "decodeURIComponent(slug)" in p
assert "trembed" in p
assert "await _crawlDirectMedia([ext],players[i],2)" in p
assert 'provider:"animevostfr"' in p
assert '"base": "https://animevostfr.org"' in p
assert overrides["official_site"] == "https://animevostfr.org"
assert overrides["provider_lego_options"]["scripts/provider_patches/animevostfr_runtime_v1.py"]["base"] == "https://animevostfr.org"
assert overrides["runtime_domain_replacements"]["v2.animevostfr.org"] == "animevostfr.org"
assert hubs["direct"] == "https://animevostfr.org/"
assert hubs["direct_authority"] == "explicit_current"
assert any(
    row.get("type") == "redirect" and row.get("url") == "https://v2.animevostfr.org/"
    for row in hubs.get("sources") or []
)
print("AnimeVOSTFR runtime contract passed")
