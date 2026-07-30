#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'provider-lkg.json').read_text())
assert registry['schema_version'] >= 2
for provider_id, record in registry.get('providers', {}).items():
    assert int(record.get('stream_count', 0)) > 0, provider_id
    assert record.get('validated_at'), provider_id
    assert record.get('fixture'), provider_id
    assert record.get('category') in {'movie', 'tv', 'anime'}, provider_id
    assert len(str(record.get('sha256', ''))) == 64, provider_id
print('LKG current-proof policy tests passed')
