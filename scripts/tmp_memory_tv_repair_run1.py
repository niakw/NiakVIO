#!/usr/bin/env python3
from pathlib import Path
p=Path('MEMORY.md')
marker='## TV shared-runtime repair run 1 — 2026-09-07'
text=p.read_text(encoding='utf-8')
if marker not in text:
    text += '''

## TV shared-runtime repair run 1 — 2026-09-07

- One-shot workflow `MAIN - TV Runtime Repair`, run **34072829930**, job **101593230828**, failed safely in the migration step before tests/commit/publication.
- `CORE.MEDIA_TYPE_RESOLUTION.V1` latest-request/cancellation patch applied successfully in the ephemeral workspace; failure occurred afterward because the `STREAM_FACTS` migration anchor still used old local variable name `r` while current Core source uses `row`.
- No generated provider, manifest, DATA or public version changed from this failed run.
- Fix the migration anchor against current `global_stream_facts_v1.py`, then rerun the full focused cancellation + quality + batched-prune test set before committing any Core repair.
'''
    p.write_text(text,encoding='utf-8')
