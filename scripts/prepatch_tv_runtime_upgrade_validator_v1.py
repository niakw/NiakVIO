#!/usr/bin/env python3
from pathlib import Path
p=Path('scripts/upgrade_tv_runtime_regressions_v1.py')
text=p.read_text(encoding='utf-8')
old='for needle in (MARKER_QUALITY, "r&&r.resolution", "r&&r.height", "urlFacts(r)"):'
new='for needle in (MARKER_QUALITY, "row&&row.resolution", "row&&row.height", "urlFacts(row)"):'
if old in text:
    text=text.replace(old,new,1)
elif new not in text:
    raise AssertionError('TV runtime validator anchor missing')
p.write_text(text,encoding='utf-8')
print('TV_RUNTIME_UPGRADE_VALIDATOR_PREPATCH_OK')
