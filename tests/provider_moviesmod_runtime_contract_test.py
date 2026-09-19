#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/moviesmod_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["moviesmod"]
hubs=json.loads((ROOT/"provider-hubs.json").read_text(encoding="utf-8"))["providers"]["moviesmod"]
for needle in ("/search/","form","?go=","driveseed","cloud.unblockedgames.world","urlflix.xyz","gatewayToDrive","headingDownloadLinks","instant download","resume cloud","NIAKVIO_MOVIESMOD_RUNTIME_V1"):
    assert needle.lower() in src.lower(), needle
assert hubs["direct"] == "https://moviesmod.ai.in/"
assert hubs["direct_authority"] == "explicit_current"
assert ov["provider_lego_scripts"] == ["scripts/provider_patches/moviesmod_runtime_v1.py"]
assert ov["official_site"] == "https://moviesmod.ai.in"
assert ov["domain_substitutions"]["moviesmod.zone"] == "moviesmod.ai.in"
assert ov["provider_lego_options"]["scripts/provider_patches/moviesmod_runtime_v1.py"]["base"] == "https://moviesmod.ai.in"
assert 'return s(q.type==="movie"?(md.title||md.original_title||md.name):(md.name||md.original_name||md.title))' in src
assert "md.imdb_id||md.imdbId" not in src
js=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER","{}")
subprocess.run(["node","-e","new Function(process.argv[1]);",js],check=True)
print("MoviesMod provider runtime/domain contract passed")
