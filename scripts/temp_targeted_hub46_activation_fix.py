#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"
MANIFESTS = [
    ROOT / "manifest.json",
    ROOT / "vf" / "manifest.json",
    ROOT / "no-anime" / "manifest.json",
    ROOT / "vf-no-anime" / "manifest.json",
]


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


matrix = load(HUB_MATRIX)
rows = matrix.get("rows") or []
targets = {cid(row.get("manifestId")) for row in rows if isinstance(row, dict) and cid(row.get("manifestId"))}
assert matrix.get("hubCount") == 46, matrix.get("hubCount")
assert len(rows) == 46, len(rows)
assert len(targets) == 46, sorted(targets)

main = load(ROOT / "manifest.json")
main_ids = {cid(row.get("id")) for row in main.get("scrapers") or [] if isinstance(row, dict)}
assert len(main_ids) == 96, len(main_ids)
assert targets <= main_ids, sorted(targets - main_ids)

# Exact activation surface: 46 matrix providers ON, every other canonical row OFF.
for path in MANIFESTS:
    data = load(path)
    for row in data.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        pid = cid(row.get("id"))
        row["enabled"] = pid in targets
    write(path, data)

# Keep published overrides aligned with the same authority.
overrides_path = ROOT / "provider-overrides.json"
overrides = load(overrides_path)
patches = overrides.get("provider_patches") or {}
assert isinstance(patches, dict)
for raw_pid, patch in patches.items():
    if not isinstance(patch, dict):
        continue
    pid = cid(raw_pid)
    mo = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
    mo["enabled"] = pid in targets
    patch["manifest_overrides"] = mo
write(overrides_path, overrides)

# Finalizer: Repair owns route state only; hub-matrix membership owns activation.
p = ROOT / "scripts" / "finalize_provider_repair_disposition_v1_impl.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'OUTPUT = ROOT / "automation" / "provider-repair-disposition.json"\n',
    'OUTPUT = ROOT / "automation" / "provider-repair-disposition.json"\nHUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"\n',
    1,
)
s = s.replace(
    'parser = argparse.ArgumentParser(description="Finalize Provider v3 repair diagnostics with force-ON catalogue activation")',
    'parser = argparse.ArgumentParser(description="Finalize Provider v3 repair diagnostics with 46-hub targeted activation")',
    1,
)
s = s.replace(
    '    parser.add_argument("--output", type=Path, default=OUTPUT)\n',
    '    parser.add_argument("--output", type=Path, default=OUTPUT)\n    parser.add_argument("--hub-matrix", type=Path, default=HUB_MATRIX)\n',
    1,
)
s = s.replace(
    '    quick = load(args.quick_yield)\n',
    '    quick = load(args.quick_yield)\n    hub_matrix = load(args.hub_matrix)\n    target_hubs = {cid(row.get("manifestId")) for row in hub_matrix.get("rows") or [] if isinstance(row, dict) and cid(row.get("manifestId"))}\n    if int(hub_matrix.get("hubCount") or 0) != 46 or len(target_hubs) != 46:\n        raise SystemExit(f"expected exact 46-hub activation matrix, got count={hub_matrix.get(\'hubCount\')} ids={len(target_hubs)}")\n',
    1,
)
old = '''        # NIAKVIO_FORCE_ON_REPAIR_DISPOSITION_V2
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

        disposition = {
            "schemaVersion": 1,
            "authority": "provider-repair-disposition-v1",
            "activationState": "enabled",
            "activationAuthority": "canonical-force-on",
            "declaredHub": hub or None,
            "forcedEnabled": True,
'''
new = '''        # NIAKVIO_HUB46_ACTIVATION_AUTHORITY_V1
        # Repair/off is route debt. Visibility is owned exclusively by the exact
        # 46-provider hub matrix selected for this repair campaign.
        hub = declared_hub(patch)
        enabled = provider in target_hubs
        manifest_row["enabled"] = enabled
        manifest_overrides = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        manifest_overrides["enabled"] = enabled
        patch["manifest_overrides"] = manifest_overrides
        patch["route_data_state"] = route_state
        if enabled:
            enabled_count += 1
        else:
            disabled_providers.append(provider)

        disposition = {
            "schemaVersion": 1,
            "authority": "provider-repair-disposition-v1",
            "activationState": "enabled" if enabled else "disabled",
            "activationAuthority": "hub-lab-matrix-46",
            "declaredHub": hub or None,
            "forcedEnabled": enabled,
'''
assert old in s, "force-ON finalizer block not found"
s = s.replace(old, new, 1)
old_policy = '''            "activeBrokenProviderAllowed": True,
            "incompleteProviderEnabled": True,
            "forceAllProvidersEnabled": True,
            "activationFollowsRepairState": False,
            "activationFollowsDeclaredHub": False,
            "activationAuthority": "canonical-96-catalogue",
            "missingDeclaredHubState": "enabled-repairable",
'''
new_policy = '''            "activeBrokenProviderAllowed": True,
            "incompleteProviderEnabled": True,
            "forceAllProvidersEnabled": False,
            "activationFollowsRepairState": False,
            "activationFollowsDeclaredHub": False,
            "activationAuthority": "automation/evidence/hub-lab-matrix-46.json:rows[].manifestId",
            "targetHubProviderCount": 46,
            "nonTargetProviderState": "disabled",
            "registryOnlyTargetMayRemainEnabled": True,
'''
assert old_policy in s, "force-ON summary policy not found"
s = s.replace(old_policy, new_policy, 1)
s = s.replace(
    'f"diagnostic_incomplete={len(incomplete)} activation=force_all_canonical"',
    'f"diagnostic_incomplete={len(incomplete)} activation=hub_matrix_46"',
    1,
)
p.write_text(s, encoding="utf-8")

# Activation validator: exact-set equality, not 96/96 and not official_hub presence.
p = ROOT / "scripts" / "validate_activation_preservation.py"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'OVERRIDES = ROOT / "provider-overrides.json"\n',
    'OVERRIDES = ROOT / "provider-overrides.json"\nHUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"\n',
    1,
)
s = s.replace('NIAKVIO_FORCE_ON_CATALOGUE_AUTHORITY_V2', 'NIAKVIO_HUB46_ACTIVATION_AUTHORITY_V1')
new_validate = '''def validate() -> list[str]:
    main_rows = rows(load(MAIN))
    vf_rows = rows(load(VF))
    patches_by_id = provider_patch_rows(load_optional(OVERRIDES))
    matrix = load(HUB_MATRIX)
    target = {
        str(row.get("manifestId") or "").strip().casefold().replace("_", "-")
        for row in matrix.get("rows") or []
        if isinstance(row, dict) and str(row.get("manifestId") or "").strip()
    }
    active = {
        provider_id
        for provider_id, row in main_rows.items()
        if row.get("enabled") is True
    }

    errors: list[str] = []
    if int(matrix.get("hubCount") or 0) != 46 or len(target) != 46:
        errors.append(f"hub activation authority must contain exactly 46 providers, got {len(target)}")
    if len(main_rows) != 96:
        errors.append(f"canonical catalogue must contain 96 providers, got {len(main_rows)}")

    missing = sorted(target - set(main_rows))
    extra = sorted(active - target)
    disabled_target = sorted(target - active)
    if missing:
        errors.append("46-hub target missing from canonical catalogue: " + ",".join(missing))
    if disabled_target:
        errors.append("46-hub target unexpectedly disabled: " + ",".join(disabled_target))
    if extra:
        errors.append("non-target provider unexpectedly enabled: " + ",".join(extra))
    if len(active) != 46:
        errors.append(f"enabled provider count must be exactly 46, got {len(active)}")

    for provider_id, patch in sorted(patches_by_id.items()):
        mo = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        if "enabled" in mo and bool(mo.get("enabled")) != (provider_id in target):
            errors.append(f"override activation mismatch for hub46 authority: {provider_id}")

    mismatched = sorted(
        provider_id
        for provider_id in set(main_rows) & set(vf_rows)
        if bool(main_rows[provider_id].get("enabled"))
        != bool(vf_rows[provider_id].get("enabled"))
    )
    if mismatched:
        errors.append("hub46 activation projection mismatch: " + ",".join(mismatched))

    registry_only = sorted(
        provider_id
        for provider_id in active
        if not declared_hub_enabled(patches_by_id.get(provider_id))
    )
    if registry_only:
        print(
            "FIELD_ACTIVATION_HUB46_REGISTRY_ONLY "
            f"count={len(registry_only)} activation_authority=hub_lab_matrix_46"
        )

    return errors
'''
s, n = re.subn(
    r'def validate\(\) -> list\[str\]:\n.*?\n\ndef main\(\) -> int:',
    new_validate + '\n\ndef main() -> int:',
    s,
    count=1,
    flags=re.S,
)
assert n == 1, "validate() replacement failed"
s = s.replace(
    'print(f"provider activation preservation passed ({active_count} enabled; force-ON canonical catalogue; hub discovery-only)")',
    'print(f"provider activation preservation passed ({active_count} enabled; exact hub-matrix-46 authority)")',
    1,
)
p.write_text(s, encoding="utf-8")

# Focused CI policy test: fixture matrix now explicitly chooses only A as target.
p = ROOT / "tests" / "ci_preservation_policy_test.py"
s = p.read_text(encoding="utf-8")
s = s.replace("assert 'NIAKVIO_FORCE_ON_CATALOGUE_AUTHORITY_V2' in validator_source", "assert 'NIAKVIO_HUB46_ACTIVATION_AUTHORITY_V1' in validator_source")
s = s.replace(
    "        (root / 'automation').mkdir()\n",
    "        (root / 'automation').mkdir()\n        (root / 'automation' / 'evidence').mkdir()\n        (root / 'automation' / 'evidence' / 'hub-lab-matrix-46.json').write_text(json.dumps({'hubCount': 46, 'rows': [{'manifestId': 'a'}] + [{'manifestId': f'x{i}'} for i in range(45)]}), encoding='utf-8')\n",
    1,
)
# Replace only the activation-focused section; leave language/Brain regression tests intact.
start = s.index('# Catalogue activation is force-ON.')
end = s.index('# Verified manifest-language fallback regression tests.')
replacement = '''# Activation is targeted: only members of the selected hub matrix may be ON.
# The synthetic validator fixture uses target 'a'; the other 45 matrix rows are
# intentionally absent from this tiny catalogue, so this unit checks the specific
# active/non-target invariant via the exact expected error surface.
result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': False}],
    report_rows=[],
)
assert result.returncode == 1
assert 'canonical catalogue must contain 96 providers' in result.stderr
assert '46-hub target missing from canonical catalogue' in result.stderr
assert 'non-target provider unexpectedly enabled' not in result.stderr

result = run_validator(
    manifest_rows=[{'id': 'a', 'enabled': True}, {'id': 'b', 'enabled': True}],
    report_rows=[],
)
assert result.returncode == 1
assert 'non-target provider unexpectedly enabled: b' in result.stderr

# official_hub itself is not activation authority; registry-only targets are legal.
assert 'FIELD_ACTIVATION_HUB46_REGISTRY_ONLY' in validator_source


'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding="utf-8")

# Core-rehash static test: assert targeted authority markers, not 96 force-ON.
p = ROOT / "tests" / "activation_preservation_core_rehash_test.py"
s = p.read_text(encoding="utf-8")
s = s.replace('NIAKVIO_FORCE_ON_CATALOGUE_AUTHORITY_V2', 'NIAKVIO_HUB46_ACTIVATION_AUTHORITY_V1')
s = s.replace('force-ON catalogue requires enabled=true', 'non-target provider unexpectedly enabled')
s = s.replace('FIELD_ACTIVATION_HUB_DISCOVERY_ONLY', 'FIELD_ACTIVATION_HUB46_REGISTRY_ONLY')
p.write_text(s, encoding="utf-8")

print("TARGETED_HUB46_ACTIVATION_PATCHED targets=46 non_targets=50")
