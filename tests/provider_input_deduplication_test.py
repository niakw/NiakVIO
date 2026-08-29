#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "scripts" / "discover_candidates.py"
QUICK_REPAIR = ROOT / "scripts" / "run_adaptive_quick_repair.py"
PROMOTER = ROOT / "scripts" / "promote_candidates.py"
STAGE_GATE = ROOT / "engine_v2" / "scripts" / "validate-stage-against-catalog.mjs"
SOURCES = ROOT / "sources.json"

discovery = DISCOVERY.read_text(encoding="utf-8")
quick = QUICK_REPAIR.read_text(encoding="utf-8")
promoter = PROMOTER.read_text(encoding="utf-8")
stage_gate = STAGE_GATE.read_text(encoding="utf-8")
subprocess.run(["node", "--check", str(STAGE_GATE)], check=True)
sources = json.loads(SOURCES.read_text(encoding="utf-8"))

# Duplicate identity is decided at import, before any expensive provider fetch.
duplicate_check = 'if provider_id in seen_canonical_ids:'
fetch_call = 'data = fetch_bytes(provider_url)'
assert duplicate_check in discovery
assert fetch_call in discovery
assert discovery.index(duplicate_check) < discovery.index(fetch_call)

# Canonical ownership is acquired only after a provider was successfully
# validated and added; a failed first source therefore does not block a later one.
append_index = discovery.index('candidates.append(')
seen_write = 'seen_canonical_ids[provider_id] = {'
assert seen_write in discovery
assert append_index < discovery.index(seen_write)

# Published/LKG fallbacks obey the same canonical existence registry.
assert 'if provider_id in seen_canonical_ids or key in known_keys:' in discovery
assert discovery.count('if provider_id in seen_canonical_ids or key in known_keys:') >= 2

# There must be no late source-variant grouping/selection after discovery.
assert 'canonical_groups' not in discovery
assert 'choose_variant_with_baseline_protection' not in promoter
assert 'duplicate canonical candidate reached promotion' in promoter
assert 'staging input deduplication failed' in stage_gate

# Repair operates on one canonical provider, not on sibling/source variants.
assert 'sibling' not in quick.casefold()

policy = sources.get("selection_policy") or {}
assert policy.get("deduplicate_at_input") is True
assert "reject later declaration immediately" in str(policy.get("duplicate_policy") or "")
assert policy.get("duplicate_key") == "case-insensitive canonical provider id"

print("provider input deduplication tests passed")
