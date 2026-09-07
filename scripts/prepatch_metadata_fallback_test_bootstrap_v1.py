#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'tests/global_stream_presentation_metadata_fallback_test.py'
KEY_LINE = "global.TMDB_API_KEY='0123456789abcdef0123456789abcdef';\n"
text = TARGET.read_text(encoding='utf-8')
anchor = 'global.__native_fetch=function(){};\n'
if KEY_LINE not in text:
    count = text.count(anchor)
    if count != 2:
        raise AssertionError(f'expected two metadata fallback native bridges, got {count}')
    text = text.replace(anchor, KEY_LINE + anchor)
    TARGET.write_text(text, encoding='utf-8')
value = TARGET.read_text(encoding='utf-8')
assert value.count(KEY_LINE) == 2
print('METADATA_FALLBACK_TEST_RUNTIME_TMDB_BOOTSTRAP_V1_OK')
