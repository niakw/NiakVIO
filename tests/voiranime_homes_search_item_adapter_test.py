#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))

import voiranime_homes_dle_runtime_v1 as homes

wrapper = homes._voiranime_homes_wrapper()
assert homes.SEARCH_ITEM_MARKER in wrapper
assert "location\\.href" in wrapper
assert "search-title|search-item-title" in wrapper
assert "href.match(/\\/(\\d+)-/)" in wrapper
assert "manga_episodes_api.php" in wrapper
assert wrapper.count("NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1") == 1
print("voiranime-homes live search-item adapter contract passed")
