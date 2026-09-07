#!/usr/bin/env python3
from pathlib import Path
p=Path('MEMORY.md')
marker='## TV shared-runtime repair run 2 — 2026-09-07'
text=p.read_text(encoding='utf-8')
if marker not in text:
    text += '''

## TV shared-runtime repair run 2 — 2026-09-07

- `MAIN - TV Runtime Repair` retry run **34073021357**, job **101593778197**, failed safely in migration validation before focused tests/commit/publication.
- The current-source `STREAM_FACTS` prepatch succeeded (`STREAM_FACTS_QUALITY_V2_PREPATCH_OK`) and wrote the intended richer quality-fact logic in the ephemeral workspace.
- Failure was only the upgrader's own stale validation literal: it still required `r&&r.resolution` / `r&&r.height`, while current `global_stream_facts_v1.py` correctly uses `row&&row.resolution` / `row&&row.height`.
- No provider bundle, manifest or public version changed. Fix the migration validator, then rerun the full focused cancellation + quality + batched-prune suite.
'''
    p.write_text(text,encoding='utf-8')
