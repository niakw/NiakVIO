#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'scripts/native_player_diagnostics_codegen.py').read_text(encoding='utf-8')
assert 'queryIntentActivities(launcherQuery, 0)' in text
assert 'info.activityInfo?.name == MainActivity::class.java.name' in text
assert 'launchActivity.activityInfo.packageName' in text
assert 'launchActivity.activityInfo.name' in text
assert 'context.packageName,\n                MainActivity::class.java.name' not in text
assert '"com.nuviodebug.com",\n                MainActivity::class.java.name' not in text
print('native mobile player launch V37 applicationId resolution test passed')
