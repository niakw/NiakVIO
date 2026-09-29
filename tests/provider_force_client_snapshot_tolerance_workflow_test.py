#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "provider-recognition-repair-v6.yml"
src = WF.read_text(encoding="utf-8")

required = [
    'data.get("requireExternalForceMutations") is True',
    'FIELD_REPAIR_NUVIO_CLIENT_CACHE ready=false provider_force_only=true transient_transport=true action=continue-isolated-sandbox',
    'FIELD_REPAIR_NUVIO_CLIENT_CACHE ready=false provider_force_only=$provider_force_only transient_transport=$transient_transport action=fail-closed',
    'TimeoutExpired|timed out|Could not resolve|certificate|TLS|SSL|connection (?:reset|timed out|refused)|network is unreachable',
]
for value in required:
    assert value in src, value

# The exception must remain after the normal guard attempt and before Force evaluation.
guard = 'python3 scripts/guard_nuvio_client_brain_compat.py "$validated"'
force = '- name: Evaluate isolated Brain LLM Force candidates'
assert src.index(guard) < src.index('continue-isolated-sandbox') < src.index(force)

# This path may only be enabled by explicit external Force. Generic Repair/Learning
# must still fail closed on unverifiable client state.
assert 'str(data.get("mode") or "").strip().casefold()=="force"' in src
assert 'data.get("directApplyValidated") is True' in src
assert 'bool(data.get("targetProviders"))' in src

print("Provider-only Force transient client snapshot tolerance contract passed")
