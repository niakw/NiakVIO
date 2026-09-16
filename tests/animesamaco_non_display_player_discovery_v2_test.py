#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "provider_patches" / "non_display_recovery_runtime_v1.py").read_text(encoding="utf-8")

assert "NIAKVIO_ANIMESAMACO_PLAYER_DISCOVERY_V2" in source
assert "videoUrls|filmUrls" in source
assert "function animeSamaPlayers(html,base)" in source
assert "var players=animeSamaPlayers(eh.text,eh.url)" in source
assert "uniq(shells.concat(players))" in source
assert "await crawl(uniq(shells.concat(players))" in source

# Player pages are only discovery inputs. The recovery must still pass every
# candidate through the existing direct-media crawler instead of returning an
# iframe/embed URL as a stream.
assert "return decorate(rows,name,language,ref)" in source
assert "_crawlDirectMedia(clean" in source

print("ANIMESAMACO_NON_DISPLAY_PLAYER_DISCOVERY_V2_OK")
