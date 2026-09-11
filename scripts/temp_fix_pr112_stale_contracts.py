#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1) Non-regression gate: audited route debt may exist on either an enabled
# hub46 target or a disabled non-target. Activation itself is not proof quality.
p = ROOT / 'scripts' / 'check_provider_non_regression_v1.py'
s = p.read_text(encoding='utf-8')
old = '''        audited = (
            row.get("enabled") is False
            and disposition.get("authority") == "provider-repair-disposition-v1"
            and disposition.get("activationState") == "disabled"
            and state in {"repair", "off"}
            and disposition.get("completeCapabilityProof") is False
            and isinstance(disposition.get("missingLanes"), list)
            and bool(disposition.get("missingLanes"))
            and isinstance(disposition.get("reasonCodes"), list)
            and bool(disposition.get("reasonCodes"))
        )
'''
new = '''        expected_activation_state = "enabled" if row.get("enabled") is True else "disabled"
        audited = (
            disposition.get("authority") == "provider-repair-disposition-v1"
            and disposition.get("activationAuthority") == "hub-lab-matrix-46"
            and disposition.get("activationState") == expected_activation_state
            and bool(disposition.get("forcedEnabled")) == (row.get("enabled") is True)
            and state in {"repair", "off"}
            and disposition.get("completeCapabilityProof") is False
            and isinstance(disposition.get("missingLanes"), list)
            and bool(disposition.get("missingLanes"))
            and isinstance(disposition.get("reasonCodes"), list)
            and bool(disposition.get("reasonCodes"))
        )
'''
assert old in s, 'non-regression debt block missing'
s = s.replace(old, new, 1)
s = s.replace(
    '# Disabling does not authorize silent contract deletion. Semantic/HLS\n        # capability changes remain hard failures until explicitly corrected.',
    '# Activation state does not authorize silent contract deletion. Semantic/HLS\n        # capability changes remain hard failures until explicitly corrected.',
    1,
)
s = s.replace(
    '"disabledHistoricalDebtPolicy": "allowed only when manifest enabled=false and provider-repair-disposition-v1 state is repair/off; semantic/HLS contract deletion remains forbidden",',
    '"disabledHistoricalDebtPolicy": "audited route debt is allowed for hub46 targets or disabled non-targets when provider-repair-disposition-v1 state is repair/off; semantic/HLS contract deletion remains forbidden",',
    1,
)
p.write_text(s, encoding='utf-8')

# 2) Static contract test: assert the current targeted activation semantics.
p = ROOT / 'tests' / 'provider_non_regression_contract_test_impl.py'
s = p.read_text(encoding='utf-8')
old = '''# Historical proof debt may be accepted only by removing the broken provider from
# active execution. This exception may never hide semantic/HLS contract deletion.
for token in (
    "def current_activation_debt()",
    'disposition.get("authority") == "provider-repair-disposition-v1"',
    'disposition.get("activationState") == "disabled"',
    'state in {"repair", "off"}',
    '"disabledDebtAccepted"',
    '"disabledDebtProviders"',
    '"semantic_capability_regression"',
    '"historical_hls_m3u8_regression"',
):
    assert token in gate, f"disabled-debt non-regression policy lost: {token}"
assert 'manifest_row["enabled"] = enabled' in finalizer
assert 'route_state = "repair"' in finalizer
assert 'route_state = "off"' in finalizer
assert '"activeBrokenProviderAllowed": False' in finalizer
'''
new = '''# Historical proof debt may be represented as audited route debt. A targeted
# hub46 provider can remain visible while routeDataState=repair/off; non-targets
# remain disabled. Neither case may hide semantic/HLS contract deletion.
for token in (
    "def current_activation_debt()",
    'disposition.get("authority") == "provider-repair-disposition-v1"',
    'disposition.get("activationAuthority") == "hub-lab-matrix-46"',
    'expected_activation_state = "enabled" if row.get("enabled") is True else "disabled"',
    'bool(disposition.get("forcedEnabled")) == (row.get("enabled") is True)',
    'state in {"repair", "off"}',
    '"disabledDebtAccepted"',
    '"disabledDebtProviders"',
    '"semantic_capability_regression"',
    '"historical_hls_m3u8_regression"',
):
    assert token in gate, f"audited route-debt non-regression policy lost: {token}"
assert 'manifest_row["enabled"] = enabled' in finalizer
assert '"activationAuthority": "hub-lab-matrix-46"' in finalizer
assert 'route_state = "repair"' in finalizer
assert 'route_state = "off"' in finalizer
assert '"activeBrokenProviderAllowed": True' in finalizer
assert '"forceAllProvidersEnabled": False' in finalizer
'''
assert old in s, 'stale static non-regression contract block missing'
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# 3) Native codegen test: assert the current canonical-anime-selection + TV
# transport alias implementation, rather than a historical source comment.
p = ROOT / 'tests' / 'native_evidence_codegen_pipeline_test.py'
s = p.read_text(encoding='utf-8')
old = '''    for required in (
        "listOf<String>(fixtureMediaType).filter { it in declared }",
        "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=mobile",
'''
new = '''    for required in (
        "if (logicalFixtureMediaType !in declared) return emptyList<ProviderRequestRoute>()",
        'val runtimeMediaType = if (logicalFixtureMediaType == "anime") "tv" else logicalFixtureMediaType',
        "return listOf<ProviderRequestRoute>(ProviderRequestRoute(runtimeMediaType))",
        "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=mobile",
'''
assert old in s, 'stale mobile request-route assertion missing'
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

print('PR112_STALE_CONTRACTS_PATCHED non_regression=hub46_route_debt native_codegen=current_alias_contract')
