#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "provider_patches"))

import french_manga_dle_runtime_v1 as fm

wrapper = fm._french_manga_wrapper()
assert fm.SEARCH_ITEM_MARKER in wrapper
assert "location\\.href" in wrapper
assert "search-title|search-item-title" in wrapper
assert "href.match(/\\/(\\d+)-/)" in wrapper
assert "manga_episodes_api.php" in wrapper
assert wrapper.count("NIAKVIO_PROVIDER_RUNTIME_RESOLVER_V1") == 1
print("french-manga live search-item adapter contract passed")
