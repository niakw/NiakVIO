import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
baseline = json.loads((ROOT / "automation" / "provider-hub-curated-baseline.json").read_text(encoding="utf-8"))
registry = json.loads((ROOT / "provider-hubs.json").read_text(encoding="utf-8"))
providers = registry.get("providers") or {}
required = set(baseline.get("required_registry_ids") or [])
retired = set((baseline.get("explicitly_retired") or {}).keys())
supplemental = set(baseline.get("supplemental_user_chat_ids") or [])
missing = sorted(required - set(providers))
assert not missing, f"curated provider hub inventory regression: missing={missing}"
assert not (retired & set(providers)), f"explicitly retired provider hubs restored unexpectedly: {sorted(retired & set(providers))}"
assert supplemental <= set(providers), f"chat-supplied hub rows lost: {sorted(supplemental - set(providers))}"
assert registry.get("curated_baseline_commit") == baseline.get("source_commit")
for provider_id in sorted(required):
    row = providers[provider_id]
    assert isinstance(row, dict), provider_id
    assert row.get("sources") or row.get("direct_candidates") or row.get("search_queries"), provider_id
print(f"provider hub curated baseline passed required={len(required)} supplemental={len(supplemental)} retired={len(retired)}")
