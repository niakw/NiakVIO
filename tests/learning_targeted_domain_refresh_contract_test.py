#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
resolver=(ROOT/"scripts/resolve_provider_hubs.py").read_text(encoding="utf-8")
queue=(ROOT/"scripts/run_brain_learning_queue.py").read_text(encoding="utf-8")

selected=resolver.index('selected_ids = {canonical_provider_id(item) for item in args.provider}')
sanitize=resolver.index('sanitize_unsafe_published_routes(config, sanitize_hubs, history_providers)')
work=resolver.index('work: list[tuple[str, dict[str, Any], dict[str, Any]]] = []')
assert selected < sanitize < work
assert 'if selected_ids\n        else hubs' in resolver

refresh=queue.index('def refresh_stage_routes')
reconcile=queue.index('reconcile_provider_domain_metadata.py',refresh)
profiles=queue.index('build_provider_runtime_profiles.py',refresh)
validate=queue.index('validate_override_pipeline.py',refresh)
assert refresh < reconcile < profiles < validate

print("Learning targeted domain-refresh scope contract passed")
