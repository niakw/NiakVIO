#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/sekai_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["sekai"]
for needle in ("NIAKVIO_SEKAI_RUNTIME_V1","/sitemap.xml","AVAILABLE_EPISODES","STREAM_MAIN_BASE_URL","numOriginale","lastCounters","loopEpisodeRows","_crawlDirectMedia"):
    assert needle in src, needle
for forbidden in ("arm.haglund.dev","v3-cinemeta.strem.io"):
    assert forbidden not in src, forbidden
assert ov["provider_lego_scripts"] == ["scripts/provider_patches/sekai_runtime_v1.py"]
assert ov["provider_lego_options"]["scripts/provider_patches/sekai_runtime_v1.py"]["base"] == "https://sekai.one"
js=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0].replace("CONFIG_PLACEHOLDER","{}")
subprocess.run(["node","-e","new Function(process.argv[1]);",js],check=True)
print("Sekai provider runtime contract passed")
