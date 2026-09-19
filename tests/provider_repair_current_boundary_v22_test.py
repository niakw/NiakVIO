#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fast = (ROOT / 'scripts/run_provider_repair_fast_targeted_v20.py').read_text(encoding='utf-8')
pipe = (ROOT / 'scripts/run_provider_repair_pipeline_v6.py').read_text(encoding='utf-8')
base = (ROOT / 'scripts/provider_base_store.py').read_text(encoding='utf-8')
recovery = (ROOT / 'scripts/recover_provider_routes_from_upstreams.py').read_text(encoding='utf-8')

assert 'PROVIDER_REPAIR_CURRENT_BOUNDARY_V22' in fast
assert 'upgrade_provider_runtime_reconstruction_v21_12 as v212' in fast
assert 'v212.patch_recovery()' in fast and 'v212.patch_base()' in fast
assert 'FIELD_PROVIDER_V21_12_BOUNDARY ready=true revision=v21.12' in fast

assert 'PROVIDER_REPAIR_CURRENT_BOUNDARY_V22' in pipe
assert '"scripts/upgrade_provider_runtime_reconstruction_v21_12.py"' in pipe
assert '"scripts/upgrade_provider_voiranime_homes_authority_v21_10.py"' not in pipe
assert '"tests/provider_voiranime_homes_authority_v21_10_test.py"' not in pipe
assert '"routePlanRevision": "v21.12"' in pipe

assert 'NIAKVIO_PROVIDER_RUNTIME_RECONSTRUCTION_V21_12' in base
assert 'ROUTE_RECOVERY_IDENTITY_SEARCH_V21_12' in recovery

print('PROVIDER_REPAIR_CURRENT_BOUNDARY_V22_TEST_OK live_boundary=v21.12 obsolete_voiranime_homes_replay=0')
