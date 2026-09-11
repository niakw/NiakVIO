#!/usr/bin/env python3
from pathlib import Path

# 1) Non-regression gate: audited route debt is compatible with a force-ON
# catalogue. Repair/off is runtime proof debt, not publication disablement.
p = Path('scripts/check_provider_non_regression_v1.py')
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
new = '''        # NIAKVIO_FORCE_ON_NON_REGRESSION_ROUTE_DEBT_V2
        # A canonical provider stays catalogued/enabled while Repair may mark its
        # executable route DATA as repair/off. The debt exception is valid only
        # when that force-ON state is itself explicit and fully audited.
        audited = (
            row.get("enabled") is True
            and disposition.get("authority") == "provider-repair-disposition-v1"
            and disposition.get("activationState") == "enabled"
            and disposition.get("forcedEnabled") is True
            and state in {"repair", "off"}
            and disposition.get("completeCapabilityProof") is False
            and isinstance(disposition.get("missingLanes"), list)
            and bool(disposition.get("missingLanes"))
            and isinstance(disposition.get("reasonCodes"), list)
            and bool(disposition.get("reasonCodes"))
        )
'''
assert old in s, 'non-regression activation-debt block missing'
s = s.replace(old, new, 1)
s = s.replace('    disabled_debt: list[str] = []\n', '    route_debt: list[str] = []\n', 1)
s = s.replace('            disabled_debt.append(pid)\n', '            route_debt.append(pid)\n', 1)
s = s.replace(
    '''        # Disabling does not authorize silent contract deletion. Semantic/HLS
        # capability changes remain hard failures until explicitly corrected.
''',
    '''        # Audited route debt does not authorize silent contract deletion.
        # Semantic/HLS capability changes remain hard failures until corrected.
''',
    1,
)
old_obligation = '''            "externalDriftRecorded": bool(row.get("externalDriftAccepted")),
            "disabledDebtAccepted": bool(debt_reasons),
            "disabledDebtState": debt.get("routeDataState") if isinstance(debt, dict) else None,
            "disabledDebtReasons": debt_reasons,
'''
new_obligation = '''            "externalDriftRecorded": bool(row.get("externalDriftAccepted")),
            "routeDebtAccepted": bool(debt_reasons),
            "routeDebtState": debt.get("routeDataState") if isinstance(debt, dict) else None,
            "routeDebtReasons": debt_reasons,
            # Deprecated output aliases retained for artifact consumers during the
            # schema transition; semantics are force-ON route debt, never disabled.
            "disabledDebtAccepted": bool(debt_reasons),
            "disabledDebtState": debt.get("routeDataState") if isinstance(debt, dict) else None,
            "disabledDebtReasons": debt_reasons,
'''
assert old_obligation in s, 'non-regression obligation debt fields missing'
s = s.replace(old_obligation, new_obligation, 1)
old_return = '''        "candidateSource": str(DEFAULT_CANDIDATE.relative_to(ROOT)),
        "disabledHistoricalDebtPolicy": "allowed only when manifest enabled=false and provider-repair-disposition-v1 state is repair/off; semantic/HLS contract deletion remains forbidden",
        "disabledDebtProviderCount": len(sorted(set(disabled_debt))),
        "disabledDebtProviders": sorted(set(disabled_debt)),
'''
new_return = '''        "candidateSource": str(DEFAULT_CANDIDATE.relative_to(ROOT)),
        "routeHistoricalDebtPolicy": "allowed only when canonical manifest enabled=true, forcedEnabled=true and provider-repair-disposition-v1 routeDataState is repair/off; semantic/HLS contract deletion remains forbidden",
        "routeDebtProviderCount": len(sorted(set(route_debt))),
        "routeDebtProviders": sorted(set(route_debt)),
        # Deprecated aliases retained for existing evidence readers.
        "disabledHistoricalDebtPolicy": "deprecated alias: force-ON audited route debt",
        "disabledDebtProviderCount": len(sorted(set(route_debt))),
        "disabledDebtProviders": sorted(set(route_debt)),
'''
assert old_return in s, 'non-regression return debt fields missing'
s = s.replace(old_return, new_return, 1)
s = s.replace(
    "f\"failures={result['failureCount']} disabled_debt={result['disabledDebtProviderCount']} base={args.base_ref}\"",
    "f\"failures={result['failureCount']} route_debt={result['routeDebtProviderCount']} base={args.base_ref}\"",
    1,
)
p.write_text(s, encoding='utf-8')

# 2) Static non-regression contract must assert the force-ON debt authority.
p = Path('tests/provider_non_regression_contract_test_impl.py')
s = p.read_text(encoding='utf-8')
start = s.index('# Historical proof debt may be accepted only by removing the broken provider from')
end = s.index('for token in (\n    \'"core/"\',', start)
replacement = '''# Historical proof debt may be accepted only as explicit audited route debt while
# the canonical provider remains force-ON. It may never hide semantic/HLS deletion.
for token in (
    "def current_activation_debt()",
    "NIAKVIO_FORCE_ON_NON_REGRESSION_ROUTE_DEBT_V2",
    'row.get("enabled") is True',
    'disposition.get("authority") == "provider-repair-disposition-v1"',
    'disposition.get("activationState") == "enabled"',
    'disposition.get("forcedEnabled") is True',
    'state in {"repair", "off"}',
    '"routeDebtAccepted"',
    '"routeDebtProviders"',
    '"semantic_capability_regression"',
    '"historical_hls_m3u8_regression"',
):
    assert token in gate, f"force-ON route-debt non-regression policy lost: {token}"
assert 'manifest_row["enabled"] = True' in finalizer
assert 'manifest_overrides["enabled"] = True' in finalizer
assert 'route_state = "repair"' in finalizer
assert 'route_state = "off"' in finalizer
assert '"activeBrokenProviderAllowed": True' in finalizer
assert '"forceAllProvidersEnabled": True' in finalizer
assert '"activationFollowsDeclaredHub": False' in finalizer

'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding='utf-8')

# 3) Native codegen pipeline: assert the current canonical-selection + anime
# transport-alias contract emitted into Kotlin, not the removed pre-alias line.
p = Path('tests/native_evidence_codegen_pipeline_test.py')
s = p.read_text(encoding='utf-8')
old = '''        "listOf<String>(fixtureMediaType).filter { it in declared }",
        "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=mobile",
'''
new = '''        'if (logicalFixtureMediaType !in declared) return emptyList<ProviderRequestRoute>()',
        'val runtimeMediaType = if (logicalFixtureMediaType == "anime") "tv" else logicalFixtureMediaType',
        'return listOf<ProviderRequestRoute>(ProviderRequestRoute(runtimeMediaType))',
        "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN client=mobile",
'''
assert old in s, 'native mobile codegen stale selection assertion missing'
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

print('PR112_GATE_CONTRACT_FIX_PATCHED files=3')
