#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_v3_filename_policy import matches_provider_v3_filename

SHA = "a" * 64

workspace = {"context": "workspace", "publication": False}
published = {"context": "main", "publication": True}
release = {"context": "release", "publication": True}

assert matches_provider_v3_filename("anime-sama", "anime-sama-aaaaaaaaaaaaaaaa.js", SHA, workspace)
assert not matches_provider_v3_filename("anime-sama", "anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", SHA, workspace)

assert matches_provider_v3_filename("anime-sama", "anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", SHA, published)
assert matches_provider_v3_filename("anime-sama", "anime-sama--published-baseline--aaaaaaaaaaaaaaaa.js", SHA, release)
assert not matches_provider_v3_filename("anime-sama", "anime-sama-aaaaaaaaaaaaaaaa.js", SHA, published)

# Unknown/legacy contexts are fail-closed to the stricter publication shape.
assert matches_provider_v3_filename("anime-sama", "anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", SHA, {})
assert not matches_provider_v3_filename("anime-sama", "anime-sama-aaaaaaaaaaaaaaaa.js", SHA, {})

assert not matches_provider_v3_filename("anime-sama", "anime-sama--nuvio--bbbbbbbbbbbbbbbb.js", SHA, published)
assert not matches_provider_v3_filename("anime-sama", "../anime-sama--nuvio--aaaaaaaaaaaaaaaa.js", "bad", published)

print("provider v3 filename policy tests passed: workspace=simple publication=source-qualified fail_closed=publication")
