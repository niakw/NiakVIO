#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts/prepare_native_client_validation.py").read_text(encoding="utf-8")

# Historical contract: the StreamZo repair follows the site page into the player
# and extracts the final media stream. Mon Ninja et moi 3 is the positive sentinel.
# Losing that site -> player -> media chain on any required native platform is a
# regression, not a diagnostic curiosity.
assert "FIELD_DESKTOP_STREAMZO_SENTINEL status=resolved expected=resolved path=site_player_media" in source
assert "StreamZo must keep resolving Mon ninja et moi 3 on Desktop" in source
assert "StreamZo Desktop must expose final HLS media" in source

# Android TV is a first-class publication target. The repaired provider must walk
# the same real chain as Desktop: streaming site -> selected player/embed -> final
# media URL. An empty TV result is therefore promotion-blocking.
assert "FIELD_TV_STREAMZO_SENTINEL status=resolved expected=resolved path=site_player_media" in source
assert "StreamZo must resolve Mon ninja et moi 3 through site -> player -> media on Android TV" in source
assert "StreamZo TV must expose final HLS media" in source
assert "known_gap" not in source
assert "FIELD_TV_STREAMZO_COMPATIBILITY" not in source

# Mobile stays measured independently for now, but any returned result must still
# be final playable HLS rather than a catalogue or embed URL.
assert "FIELD_MOBILE_STREAMZO_COMPATIBILITY status=empty expected=diagnostic" in source
assert "Any StreamZo Mobile result must expose final HLS media" in source

print("StreamZo native platform contract tests passed")
