#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]
co=(ROOT/"scripts/provider_patches/coflix_runtime_v1.py").read_text(encoding="utf-8")
au=(ROOT/"scripts/provider_patches/animesultra_runtime_v1.py").read_text(encoding="utf-8")
assert "NIAKVIO_COFLIX_RUNTIME_V1" in co
for needle in ("/ajax/search/suggest?keyword=","/ajax/episode/list-episode?movieId=","/ajax/episode/player?episode_id=","_crawlDirectMedia"):
    assert needle in co, needle
assert "arm.haglund.dev" not in co
assert "NIAKVIO_ANIMESULTRA_RUNTIME_V1" in au
for needle in ("/index.php?do=search&subaction=search&story=","/engine/ajax/full-story.php?newsId=","content_player_","video.sibnet.ru/shell.php?videoid=","_crawlDirectMedia"):
    assert needle in au, needle
assert "arm.haglund.dev" not in au
assert ov["coflix"]["provider_lego_scripts"] == ["scripts/provider_patches/coflix_runtime_v1.py"]
assert ov["animesultra"]["provider_lego_scripts"] == ["scripts/provider_patches/animesultra_runtime_v1.py"]
assert ov["animesultra"]["provider_lego_options"]["scripts/provider_patches/animesultra_runtime_v1.py"]["base"] == "https://v2.animesultra.org"\nassert '"base":"https://v2.animesultra.org"' in au\nprint("Coflix and AnimesUltra provider runtime contracts passed")
