#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts/prepare_native_client_validation.py").read_text(encoding="utf-8")

# Historical contract: the StreamZo repair follows the site page into the player
# and extracts the final media stream. Mon Ninja et moi 3 is the Desktop/PC
# positive sentinel. Losing it on Desktop is a regression.
assert "FIELD_DESKTOP_STREAMZO_SENTINEL status=resolved expected=resolved" in source
assert "StreamZo must keep resolving Mon ninja et moi 3 on Desktop" in source
assert "StreamZo Desktop must expose HLS" in source

# Android TV is a known compatibility gap for that same repaired path. The test
# must observe it independently, never reinterpret an empty TV result as proof
# that the global engine or provider repair is broken everywhere.
assert "FIELD_TV_STREAMZO_COMPATIBILITY status=empty expected=known_gap" in source
assert "FIELD_TV_STREAMZO_COMPATIBILITY status=resolved expected=known_gap_improved" in source
assert "StreamZo must resolve Mon ninja et moi 3\", rows.isNotEmpty()" not in source

# Mobile is also classified independently from Desktop; its result remains a
# device observation rather than being folded into the PC sentinel.
assert "FIELD_MOBILE_STREAMZO_COMPATIBILITY status=empty expected=diagnostic" in source
assert "FIELD_MOBILE_STREAMZO_COMPATIBILITY status=resolved expected=diagnostic" in source

print("StreamZo native platform contract tests passed")
