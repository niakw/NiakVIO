#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'scripts/native_player_diagnostics_codegen.py').read_text(encoding='utf-8')
assert 'Intent().setClassName(' in text
assert 'context.packageName,\n                MainActivity::class.java.name' in text
assert '"com.nuviodebug.com",\n                MainActivity::class.java.name' not in text
print('native mobile player launch V36 test passed')
