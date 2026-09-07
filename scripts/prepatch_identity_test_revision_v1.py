#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'tests/global_stream_identity_test.py'
OLD = 'cross-client-shared-tv-year-soft-v8'
NEW = 'cross-client-shared-tmdb-owner-movie-year-only-v10'

text = TARGET.read_text(encoding='utf-8')
count = text.count(OLD)
if count:
    text = text.replace(OLD, NEW)
if 'NUVIO_IDENTITY_SHARED_TMDB_CAPABILITY_V1' not in text:
    anchor = f'assert "{NEW}" in patched\n'
    if anchor not in text:
        raise AssertionError('identity revision assertion anchor missing')
    text = text.replace(anchor, anchor + 'assert "NUVIO_IDENTITY_SHARED_TMDB_CAPABILITY_V1" in patched\n', 1)
TARGET.write_text(text, encoding='utf-8')
value = TARGET.read_text(encoding='utf-8')
assert OLD not in value
assert NEW in value
assert 'NUVIO_IDENTITY_SHARED_TMDB_CAPABILITY_V1' in value
print(f'IDENTITY_TEST_REVISION_V1_OK replaced={count}')
