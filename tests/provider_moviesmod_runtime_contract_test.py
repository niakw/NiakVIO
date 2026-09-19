#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/moviesmod_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["moviesmod"]
hubs=json.loads((ROOT/"provider-hubs.json").read_text(encoding="utf-8"))["providers"]["moviesmod"]
for needle in ("/search/","form","?go=","driveseed","instant download","resume cloud","NIAKVIO_MOVIESMOD_RUNTIME_V1"):
    assert needle.lower() in src.lower(), needle
assert hubs["direct"] == "https://moviesmod.army/"
assert hubs["direct_authority"] == "explicit_current"
assert ov["provider_lego_scripts"] == ["scripts/provider_patches/moviesmod_runtime_v1.py"]
assert ov["provider_lego_options"]["scripts/provider_patches/moviesmod_runtime_v1.py"]["base"] == "https://moviesmod.army"
print("MoviesMod provider runtime/domain contract passed")
