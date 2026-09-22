#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"scripts"/"run_brain_learning_queue.py").read_text(encoding="utf-8")

assert "route_search(provider_id, run_dir, provider_deadline)" in source
assert "refresh_stage_routes(stage, provider_deadline, provider_id)" in source
assert "route_search(provider_id, run_dir, work_deadline)" not in source
assert "refresh_stage_routes(stage, work_deadline, provider_id)" not in source

fair_idx=source.index("FIELD_BRAIN_HANDOFF_FAIR_SHARE")
route_idx=source.index("route_search(provider_id, run_dir, provider_deadline)")
assert fair_idx < route_idx, (fair_idx,route_idx)

print("Brain Learning fair-share route deadline contract passed")
