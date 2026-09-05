#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from finalize_native_android_reader_source import finalize_source

ENTRY = 'emit("FIELD_NATIVE_PLAYER_BEGIN client=mobile fixture=x provider64=x index=0 entry=nuvio-production-player")'

current_mobile = f'''
import android.content.Intent
import com.nuvio.app.MainActivity
{ENTRY}
val intent = Intent().setClassName(
    "com.nuviodebug.com",
    MainActivity::class.java.name,
)
'''
finalized = finalize_source(current_mobile, "mobile")
assert "FIELD_NATIVE_PLAYER_ENTRY client=mobile" in finalized
assert "FIELD_NATIVE_PLAYER_BEGIN client=mobile" not in finalized
assert 'Intent().setClassName(' in finalized
assert '"com.nuviodebug.com"' in finalized
assert "MainActivity::class.java.name" in finalized

legacy_mobile = f'''
{ENTRY}
val intent = context.packageManager.getLaunchIntentForPackage("com.nuviodebug.com")
'''
try:
    finalize_source(legacy_mobile, "mobile")
except ValueError as error:
    assert "setClassName" in str(error) or "obsolete" in str(error)
else:
    raise AssertionError("legacy packageManager launch must be rejected")

tv_source = '''
emit("FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=x provider64=x index=0 entry=nuvio-production-player")
'''
tv_finalized = finalize_source(tv_source, "tv")
assert "FIELD_NATIVE_PLAYER_ENTRY client=tv" in tv_finalized
assert "FIELD_NATIVE_PLAYER_BEGIN client=tv" not in tv_finalized

print("native Android reader finalizer current MainActivity launch contract passed")
