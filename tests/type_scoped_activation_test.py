#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / 'health-config.json').read_text(encoding='utf-8'))
source = (ROOT / 'scripts' / 'promote_candidates.py').read_text(encoding='utf-8')

assert config['activation'].get('allow_type_scoped_activation') is True
assert 'def independently_proven_categories(' in source
assert 'height < minimum_height' in source
assert 'bandwidth is not None and bandwidth < minimum_bandwidth' in source
assert 'if require_language and not (audio or subtitle_ok):' in source
assert 'scoped_categories = required_categories & independently_proven' in source
assert '"activation_supported_types": sorted(scoped_categories)' in source
assert 'if enabled and activation_mode == "strict_current" and activation_supported_types:' in source
assert 'promoted_entry["supportedTypes"] = activation_supported_types' in source
assert 'tracked_fields = ("filename", "supportedTypes", "supportsExternalPlayer")' in source

# A type cannot be published from metadata alone: the independently-proven set
# explicitly requires a healthy current fixture plus verified media/quality.
healthy_idx = source.index('if not isinstance(test, dict) or test.get("status") != "healthy":')
payload_idx = source.index('if int(test.get("payload_verified_streams", 0)) < minimum_payload:')
quality_idx = source.index('if height < minimum_height')
publish_idx = source.index('promoted_entry["supportedTypes"] = activation_supported_types')
assert healthy_idx < payload_idx < quality_idx < publish_idx

print('type-scoped activation tests passed')
