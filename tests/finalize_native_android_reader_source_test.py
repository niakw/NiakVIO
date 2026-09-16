#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from finalize_native_android_reader_source import finalize_source
ENTRY='emit("FIELD_NATIVE_PLAYER_BEGIN client=mobile fixture=x provider64=x index=0 entry=nuvio-production-player")'
current_mobile=f'''
import android.content.Intent
import com.nuvio.app.MainActivity
{ENTRY}
val launcherQuery = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
val launchActivity = context.packageManager.queryIntentActivities(launcherQuery, 0)
    .firstOrNull {{ info -> info.activityInfo?.name == MainActivity::class.java.name }}
    ?: context.packageManager.queryIntentActivities(launcherQuery, 0).first()
val intent = Intent().setClassName(
    launchActivity.activityInfo.packageName,
    launchActivity.activityInfo.name,
)
'''
finalized=finalize_source(current_mobile,"mobile")
assert "FIELD_NATIVE_PLAYER_ENTRY client=mobile" in finalized
assert "FIELD_NATIVE_PLAYER_BEGIN client=mobile" not in finalized
assert "queryIntentActivities(launcherQuery, 0)" in finalized
assert "launchActivity.activityInfo.packageName" in finalized
assert "launchActivity.activityInfo.name" in finalized
assert "MainActivity::class.java.packageName" not in finalized
legacy=f'''{ENTRY}
val intent = Intent().setClassName(context.packageName, MainActivity::class.java.name)
'''
try: finalize_source(legacy,"mobile")
except ValueError: pass
else: raise AssertionError("namespace-based package launch must be rejected")
tv='emit("FIELD_NATIVE_PLAYER_BEGIN client=tv fixture=x provider64=x index=0 entry=nuvio-production-player")'
out=finalize_source(tv,"tv")
assert "FIELD_NATIVE_PLAYER_ENTRY client=tv" in out
print("native Android reader finalizer installed-launcher contract passed")
