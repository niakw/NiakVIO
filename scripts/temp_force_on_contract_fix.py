#!/usr/bin/env python3
from pathlib import Path
import re


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


# 1) Production activation validator: catalogue activation is no longer derived
# from official_hub or health. Those are discovery/route state only.
p = Path("scripts/validate_activation_preservation.py")
s = p.read_text(encoding="utf-8")
s, n = re.subn(
    r'\A#!/usr/bin/env python3\n"""Prevent automated releases.*?"""',
    '''#!/usr/bin/env python3
"""Prevent automated releases from shrinking the canonical provider catalogue.

NIAKVIO_FORCE_ON_CATALOGUE_AUTHORITY_V2

Publication activation and runtime route confidence are separate concerns:

* every canonical provider remains present and ``enabled=true`` in the catalogue;
* ``official_hub`` is discovery/address metadata only and never an ON/OFF switch;
* Repair/health evidence controls route/DATA state (on/repair/off), not catalogue
  visibility;
* quarantined, terminal or unresolved providers remain catalogued but must fail
  closed at runtime through their audited route/DATA disposition;
* historical activation LKG remains an anti-deletion/accounting source only.

Legacy safety/provenance helpers remain in this module because historical evidence
adapters import them, but they are not permitted to turn a canonical catalogue row
off.
"""''',
    s,
    count=1,
    flags=re.S,
)
assert n == 1, "activation validator docstring patch failed"

new_validate = '''def validate() -> list[str]:
    policy = load(POLICY)
    main_rows = rows(load(MAIN))
    vf_rows = rows(load(VF))
    patches_by_id = provider_patch_rows(load_optional(OVERRIDES))
    expected = {
        str(value).casefold()
        for value in policy.get("active_ids") or []
        if str(value).strip()
    }
    minimum = int(policy.get("minimum_enabled_count") or len(expected))
    active = {
        provider_id
        for provider_id, row in main_rows.items()
        if row.get("enabled") is True
    }

    errors: list[str] = []

    # NIAKVIO_FORCE_ON_CATALOGUE_AUTHORITY_V2
    # A hub is discovery metadata. Health/Repair evidence owns executable route
    # state, while the canonical catalogue itself remains force-ON.
    for provider_id, manifest_row in sorted(main_rows.items()):
        if manifest_row.get("enabled") is not True:
            errors.append(
                f"force-ON catalogue requires enabled=true: {provider_id}"
            )

    for provider_id in sorted(expected):
        manifest_row = main_rows.get(provider_id)
        if manifest_row is None:
            errors.append(
                f"activation LKG provider missing from canonical catalogue: {provider_id}"
            )
            continue
        if manifest_row.get("enabled") is not True:
            errors.append(
                f"activation LKG provider disabled in force-ON catalogue: {provider_id}"
            )

    if len(active) < minimum:
        errors.append(
            f"enabled canonical provider count regressed: {len(active)} < {minimum}"
        )

    # Language projections must never invent a different activation state for a
    # provider they contain. Projection membership may legitimately be smaller.
    mismatched = sorted(
        provider_id
        for provider_id in set(main_rows) & set(vf_rows)
        if bool(main_rows[provider_id].get("enabled"))
        != bool(vf_rows[provider_id].get("enabled"))
    )
    if mismatched:
        errors.append(
            "force-ON activation projection mismatch: " + ",".join(mismatched)
        )

    hubless_enabled = sorted(
        provider_id
        for provider_id in active
        if not declared_hub_enabled(patches_by_id.get(provider_id))
    )
    if hubless_enabled:
        print(
            "FIELD_ACTIVATION_HUB_DISCOVERY_ONLY "
            f"enabled_without_hub={len(hubless_enabled)} "
            "activation_authority=canonical_catalogue"
        )

    return errors
'''
s, n = re.subn(
    r'def validate\(\) -> list\[str\]:\n.*?\n\ndef main\(\) -> int:',
    new_validate + "\n\ndef main() -> int:",
    s,
    count=1,
    flags=re.S,
)
assert n == 1, "activation validate() replacement failed"
s = s.replace(
    'print(f"provider activation preservation passed ({active_count} enabled; declared-hub authority; LKG history preserved)")',
    'print(f"provider activation preservation passed ({active_count} enabled; force-ON canonical catalogue; hub discovery-only)")',
)
write(str(p), s)


# 2) Repair disposition finalizer: all canonical providers remain ON;
# routeDataState carries on/repair/off and hub is metadata only.
p = Path("scripts/finalize_provider_repair_disposition_v1_impl.py")
s = p.read_text(encoding="utf-8")
s, n = re.subn(
    r'\A#!/usr/bin/env python3\n"""Finalize provider repair diagnostics.*?"""',
    '''#!/usr/bin/env python3
"""Finalize provider repair diagnostics without shrinking catalogue activation.

NIAKVIO_FORCE_ON_REPAIR_DISPOSITION_V2

Policy:
- all 96 canonical providers stay present and enabled in the catalogue;
- ``official_hub`` is discovery/address metadata, never activation authority;
- proof controls diagnostic route/DATA state: ``on`` / ``repair`` / ``off``;
- unresolved, terminal and quarantined providers remain enabled but fail closed
  through an audited repair/off disposition;
- existing route/DATA evidence is preserved for Learning/Repair;
- this script never silently shrinks supported/canonical types.

Catalogue visibility and executable route confidence are deliberately independent.
"""''',
    s,
    count=1,
    flags=re.S,
)
assert n == 1, "repair finalizer docstring patch failed"
s = s.replace(
    'parser = argparse.ArgumentParser(description="Finalize Provider v3 repair diagnostics with declared-hub activation")',
    'parser = argparse.ArgumentParser(description="Finalize Provider v3 repair diagnostics with force-ON catalogue activation")',
)
old = '''        # Single publication activation authority: a declared official hub.
        # Repair/off remain diagnostic states only and never override this rule.
        hub = declared_hub(patch)
        enabled = bool(hub)
        manifest_row["enabled"] = enabled
        manifest_overrides = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        manifest_overrides["enabled"] = enabled
        patch["manifest_overrides"] = manifest_overrides
        patch["route_data_state"] = route_state
        if enabled:
            enabled_count += 1
        else:
            disabled_providers.append(provider)
'''
new = '''        # NIAKVIO_FORCE_ON_REPAIR_DISPOSITION_V2
        # Hub discovery and catalogue activation are independent. Repair/off
        # remains explicit executable debt while every canonical provider stays ON.
        hub = declared_hub(patch)
        enabled = True
        manifest_row["enabled"] = True
        manifest_overrides = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        manifest_overrides["enabled"] = True
        patch["manifest_overrides"] = manifest_overrides
        patch["route_data_state"] = route_state
        enabled_count += 1
'''
assert old in s, "repair activation block anchor missing"
s = s.replace(old, new, 1)
s = s.replace(
    '"activationState": "enabled" if enabled else "disabled",\n            "activationAuthority": "declared-official-hub",\n            "declaredHub": hub or None,\n            "forcedEnabled": False,',
    '"activationState": "enabled",\n            "activationAuthority": "canonical-force-on",\n            "declaredHub": hub or None,\n            "forcedEnabled": True,',
    1,
)
old_policy = '''            "activeBrokenProviderAllowed": True,
            "incompleteProviderEnabled": True,
            "forceAllProvidersEnabled": False,
            "activationFollowsRepairState": False,
            "activationFollowsDeclaredHub": True,
            "activationAuthority": "provider-overrides.json:provider_patches.*.official_hub",
            "missingDeclaredHubState": "disabled",
'''
new_policy = '''            "activeBrokenProviderAllowed": True,
            "incompleteProviderEnabled": True,
            "forceAllProvidersEnabled": True,
            "activationFollowsRepairState": False,
            "activationFollowsDeclaredHub": False,
            "activationAuthority": "canonical-96-catalogue",
            "missingDeclaredHubState": "enabled-repairable",
'''
assert old_policy in s, "repair summary policy anchor missing"
s = s.replace(old_policy, new_policy, 1)
s = s.replace(
    'f"diagnostic_incomplete={len(incomplete)} activation=declared_hub"',
    'f"diagnostic_incomplete={len(incomplete)} activation=force_all_canonical"',
    1,
)
write(str(p), s)


# 3) Update CI policy fixtures to verify force-ON instead of historical
# health/hub-driven disablement.
p = Path("tests/ci_preservation_policy_test.py")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "assert 'configured_safety_quarantine' in validator_source\n",
    "assert 'configured_safety_quarantine' in validator_source\nassert 'NIAKVIO_FORCE_ON_CATALOGUE_AUTHORITY_V2' in validator_source\nassert 'declared-hub activation mismatch' not in validator_source\n",
    1,
)
start = s.index("# A historical provider may be disabled only")
end = s.index("# Verified manifest-language fallback regression tests.")
replacement = '''# Catalogue activation is force-ON. Health, route proof and hub availability may
# change executable route/DATA state, but they may not disable a canonical row.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': True}],
    report_rows=[
        {'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []},
        {'id': 'b', 'enabled': False, 'action': 'published-disabled-failed-gates', 'failed_gates': ['08_quality_and_bitrate']},
    ],
)
assert result.returncode == 0, result.stdout + result.stderr

# A canonical row may not be disabled even with conclusive negative evidence.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': False}],
    report_rows=[
        {'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []},
        {'id': 'b', 'enabled': False, 'action': 'removed-disallowed-p2p', 'failed_gates': ['01_policy_safe_no_p2p']},
    ],
)
assert result.returncode == 1
assert 'force-ON catalogue requires enabled=true: b' in result.stderr

# Historical LKG membership remains an anti-deletion guard.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}],
    report_rows=[{'id': 'a', 'enabled': True, 'action': 'enabled-current-dns-access-stream-quality-passed', 'failed_gates': []}],
)
assert result.returncode == 1
assert 'activation LKG provider missing from canonical catalogue: b' in result.stderr

# Activation no longer depends on a Deep health run.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': True}],
    report_rows=[],
    mode='quick',
)
assert result.returncode == 0, result.stdout + result.stderr

# Presence/absence of official_hub is discovery metadata only.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': True}],
    report_rows=[],
    safety={'overrides': {'provider_patches': {
        'a': {'official_hub': ''},
        'b': {'official_hub': 'https://t.me/s/example'},
    }}},
)
assert result.returncode == 0, result.stdout + result.stderr
assert 'FIELD_ACTIVATION_HUB_DISCOVERY_ONLY' in result.stdout


'''
s = s[:start] + replacement + s[end:]
write(str(p), s)


# 4) Rehash adapter test must assert the new production authority rather than
# obsolete internal accounting strings.
p = Path("tests/activation_preservation_core_rehash_test.py")
s = p.read_text(encoding="utf-8")
marker = "# Pending clean-v2 migration state must not hard-block P2 activation preservation."
if marker in s:
    prefix = s[:s.index(marker)]
    suffix = '''# Production activation is now force-ON; historical evidence helpers above
# remain tested for compatibility, but no hub/health result may disable a row.
validator_source = (ROOT / "scripts" / "validate_activation_preservation.py").read_text(encoding="utf-8")
assert "NIAKVIO_FORCE_ON_CATALOGUE_AUTHORITY_V2" in validator_source
assert "force-ON catalogue requires enabled=true" in validator_source
assert "FIELD_ACTIVATION_HUB_DISCOVERY_ONLY" in validator_source
assert "declared-hub activation mismatch" not in validator_source
'''
    s = prefix + suffix
write(str(p), s)


# 5) Frenchstream's hub is mutable discovery metadata. Test invariants, not one
# historical hub/domain literal.
p = Path("tests/overrides_test.py")
s = p.read_text(encoding="utf-8")
old = '''    assert frenchstream["capability"] == "mixed_embed_resolver"
    assert frenchstream["official_hub"] == "https://fstream.website/"
    assert frenchstream["official_site"] == "https://fs23.lol"
    runtime_domains = frenchstream.get("runtime_domain_replacements") or {}
    assert runtime_domains
    assert set(runtime_domains.values()) == {"fs23.lol"}
    assert runtime_domains.get("fs16.lol") == "fs23.lol"
    assert frenchstream["capability_promotion"]["activation_policy"] == "remain_disabled_until_native_reader_acceptance"
'''
new = '''    assert frenchstream["capability"] == "mixed_embed_resolver"
    hub = str(frenchstream.get("official_hub") or "")
    site = str(frenchstream.get("official_site") or "")
    hub_host = urlsplit(hub).hostname
    site_host = urlsplit(site).hostname
    assert hub.startswith("https://") and hub_host
    assert site.startswith("https://") and site_host
    runtime_domains = frenchstream.get("runtime_domain_replacements") or {}
    assert runtime_domains
    assert set(runtime_domains.values()) == {site_host}
    if "fs16.lol" in runtime_domains:
        assert runtime_domains["fs16.lol"] == site_host
    assert (frenchstream.get("manifest_overrides") or {}).get("enabled") is True
'''
assert old in s, "Frenchstream stale test anchor missing"
s = s.replace(old, new, 1)
write(str(p), s)

print("FORCE_ON_CONTRACT_PATCHED files=5")
