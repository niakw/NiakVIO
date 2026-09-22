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
assert '"--rebuild", "--provider", provider_id' in queue
reconciler=(ROOT/"scripts/reconcile_provider_domain_metadata.py").read_text(encoding="utf-8")
assert 'parser.add_argument("--provider"' in reconciler
assert 'if selected_provider and provider_id.casefold() != selected_provider' in reconciler
profiles_script=(ROOT/"scripts/build_provider_runtime_profiles.py").read_text(encoding="utf-8")
assert 'parser.add_argument("--provider", action="append"' in profiles_script
collect_stage=profiles_script.index("def collect_staged")
reapply_stage=profiles_script.index("def reapply_stage")
main_stage=profiles_script.index("def main()")
target_guard=profiles_script.index("if target_ids and provider_id not in target_ids")
assert collect_stage < reapply_stage < target_guard < main_stage
assert "target_ids" not in profiles_script[collect_stage:reapply_stage]
assert '"last_refresh_scope": "targeted"' in profiles_script
assert 'build_provider_runtime_profiles.py"), "--stage", str(stage), "--apply-stage", "--provider", provider_id' in queue
assert queue.count("refresh_stage_routes(stage, provider_deadline, provider_id)") == 2
assert "refresh_stage_routes(stage, work_deadline, provider_id)" not in queue
assert "FIELD_BRAIN_PROVIDER_REFRESH_ISOLATED" in queue
assert '"isolatedProviderRefreshFailures"' in queue
assert 'route_refresh.get("ok") is False' in queue

print("Learning targeted domain-refresh scope contract passed")
assert '"--stage", str(stage), "--provider", provider_id' in queue
validator=(ROOT/"scripts/validate_override_pipeline.py").read_text(encoding="utf-8")
assert 'parser.add_argument("--provider"' in validator
assert 'if selected_provider and provider_id != selected_provider' in validator
