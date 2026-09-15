#!/usr/bin/env python3
"""One-shot durable migration from historical fixed counts to Active44 authority.

The recoverable catalogue remains 46 rows. Executable/native/automatic-repair
scope is owned by automation/evidence/hub-lab-matrix-46.json and is currently 44.
Explicit manual OFF providers must never be re-enabled to satisfy a historical
cardinality.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0 and new in text:
        return text
    if count != 1:
        raise SystemExit(f"{label}: expected one legacy anchor, got {count}")
    return text.replace(old, new, 1)


def patch_pipeline() -> None:
    rel = "scripts/run_provider_repair_pipeline_v6.py"
    text = read(rel)
    if 'HUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"' not in text:
        text = once(
            text,
            'DISPOSITION = ROOT / "automation" / "provider-repair-disposition.json"\n',
            'DISPOSITION = ROOT / "automation" / "provider-repair-disposition.json"\n'
            'HUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"\n',
            rel + " matrix const",
        )
    old = '''    catalogue = [cid(row.get("id")) for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]\n    if len(catalogue) != 96 or len(set(catalogue)) != 96:\n        raise SystemExit(f"provider catalogue must be exactly 96, got {len(catalogue)}")\n    requested = {cid(value) for value in args.provider if cid(value)}\n    targets = [provider for provider in catalogue if provider not in skipped and (not requested or provider in requested)]\n'''
    new = '''    catalogue_rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]\n    catalogue = [cid(row.get("id")) for row in catalogue_rows]\n    if len(catalogue) != 46 or len(set(catalogue)) != 46:\n        raise SystemExit(f"provider catalogue must be exactly 46 unique ids, got {len(catalogue)}/{len(set(catalogue))}")\n    matrix = load(HUB_MATRIX)\n    matrix_ids = [cid(row.get("manifestId") or row.get("provider")) for row in matrix.get("rows") or [] if isinstance(row, dict) and cid(row.get("manifestId") or row.get("provider"))]\n    declared_active = int(matrix.get("hubCount") or 0)\n    if declared_active <= 0 or len(matrix_ids) != declared_active or len(set(matrix_ids)) != declared_active:\n        raise SystemExit(f"active provider matrix mismatch: declared={declared_active} rows={len(matrix_ids)} unique={len(set(matrix_ids))}")\n    active_catalogue = [cid(row.get("id")) for row in catalogue_rows if row.get("enabled") is True]\n    if set(active_catalogue) != set(matrix_ids):\n        raise SystemExit("manifest enabled set differs from active provider matrix")\n    requested = {cid(value) for value in args.provider if cid(value)}\n    unknown = sorted(requested - set(catalogue))\n    if unknown:\n        raise SystemExit("unknown providers: " + ",".join(unknown))\n    disabled_requested = sorted(requested - set(active_catalogue))\n    if disabled_requested:\n        raise SystemExit("requested providers are explicitly OFF/disabled: " + ",".join(disabled_requested))\n    targets = [provider for provider in active_catalogue if provider not in skipped and (not requested or provider in requested)]\n'''
    text = once(text, old, new, rel + " catalogue block")
    text = text.replace(
        'f"mode={args.mode} catalogue=96 targeted={len(targets)} skipped_green={len(skipped)} "',
        'f"mode={args.mode} catalogue={len(catalogue)} active={len(active_catalogue)} targeted={len(targets)} skipped_green={len(skipped)} "',
    )
    text = text.replace(
        '"--output", str(MERGED_REPORT.relative_to(ROOT)))',
        '"--output", str(MERGED_REPORT.relative_to(ROOT)), "--manifest", "manifest.json")',
    )
    text = text.replace(
        'run(sys.executable, "scripts/validate_published_provider_config.py", "--expected", "96")',
        'run(sys.executable, "scripts/validate_published_provider_config.py", "--expected", str(len(catalogue)))',
    )
    text = text.replace(
        '"catalogueProviderCount": 46,',
        '"catalogueProviderCount": len(catalogue),\n        "activeProviderCount": len(active_catalogue),',
    )
    write(rel, text)


def patch_fast_repair() -> None:
    rel = "scripts/run_provider_repair_fast_targeted_v1.py"
    text = read(rel)
    if 'HUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"' not in text:
        text = once(
            text,
            'SUMMARY = ROOT / "automation" / "provider-repair-fast-summary.json"\n',
            'SUMMARY = ROOT / "automation" / "provider-repair-fast-summary.json"\n'
            'HUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"\n',
            rel + " matrix const",
        )
    old = '''    manifest = load(MANIFEST)\n    catalogue = [cid(row.get("id")) for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]\n    if len(catalogue) != 96 or len(set(catalogue)) != 96:\n        raise SystemExit(f"provider catalogue must be exactly 96, got {len(catalogue)}")\n\n    skip_path = args.skip_file if args.skip_file.is_absolute() else ROOT / args.skip_file\n'''
    new = '''    manifest = load(MANIFEST)\n    catalogue_rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]\n    catalogue = [cid(row.get("id")) for row in catalogue_rows]\n    if len(catalogue) != 46 or len(set(catalogue)) != 46:\n        raise SystemExit(f"provider catalogue must be exactly 46 unique ids, got {len(catalogue)}/{len(set(catalogue))}")\n    matrix = load(HUB_MATRIX)\n    active = {cid(row.get("manifestId") or row.get("provider")) for row in matrix.get("rows") or [] if isinstance(row, dict) and cid(row.get("manifestId") or row.get("provider"))}\n    declared_active = int(matrix.get("hubCount") or 0)\n    manifest_active = {cid(row.get("id")) for row in catalogue_rows if row.get("enabled") is True}\n    if declared_active <= 0 or len(active) != declared_active or active != manifest_active:\n        raise SystemExit(f"active provider matrix mismatch: declared={declared_active} matrix={len(active)} manifest={len(manifest_active)}")\n\n    skip_path = args.skip_file if args.skip_file.is_absolute() else ROOT / args.skip_file\n'''
    text = once(text, old, new, rel + " catalogue block")
    text = once(
        text,
        '    unknown = [value for value in requested if value not in catalogue]\n    if unknown:\n        raise SystemExit("unknown providers: " + ",".join(unknown))\n    targets = [value for value in requested if value not in skipped]\n',
        '    unknown = [value for value in requested if value not in catalogue]\n    if unknown:\n        raise SystemExit("unknown providers: " + ",".join(unknown))\n    disabled = [value for value in requested if value not in active]\n    if disabled:\n        raise SystemExit("requested providers are explicitly OFF/disabled: " + ",".join(disabled))\n    targets = [value for value in requested if value not in skipped]\n',
        rel + " target block",
    )
    text = text.replace(
        'f"catalogue=96 targeted={len(targets)} skipped_green={len(skipped)} "',
        'f"catalogue={len(catalogue)} active={len(active)} targeted={len(targets)} skipped_green={len(skipped)} "',
    )
    text = text.replace(
        'run(sys.executable, "scripts/validate_published_provider_config.py", "--expected", "96")',
        'run(sys.executable, "scripts/validate_published_provider_config.py", "--expected", str(len(catalogue)))',
    )
    text = text.replace("skips the full 96-provider", "skips the full current-provider")
    text = text.replace("expensive 96-provider output guard", "expensive full-provider output guard")
    text = text.replace("repeated 96-provider non-network guard", "repeated full-provider non-network guard")
    write(rel, text)


def patch_merge() -> None:
    rel = "scripts/merge_provider_repair_report_v6.py"
    text = read(rel)
    text = text.replace(
        '"""Merge targeted route proof with the 96-provider baseline and exact-source LKG.',
        '"""Merge targeted route proof with the historical baseline and exact-source LKG.',
    )
    if 'parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))' not in text:
        text = once(
            text,
            '    parser.add_argument("--output", type=Path, default=Path("automation/provider-route-recovery-v6.json"))\n',
            '    parser.add_argument("--output", type=Path, default=Path("automation/provider-route-recovery-v6.json"))\n'
            '    parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))\n',
            rel + " manifest arg",
        )
    old = '''    baseline = load(ROOT / args.baseline)\n    targeted = load(ROOT / args.targeted)\n    if int(baseline.get("providerCount") or 0) != 96 or len(baseline.get("providers") or []) != 96:\n        raise SystemExit("baseline route proof must contain 96 providers")\n\n    lkg_path = ROOT / args.lkg\n'''
    new = '''    baseline = load(ROOT / args.baseline)\n    targeted = load(ROOT / args.targeted)\n    manifest = load(ROOT / args.manifest)\n    catalogue_ids = [\n        str(row.get("id") or "").strip().casefold().replace("_", "-")\n        for row in manifest.get("scrapers") or []\n        if isinstance(row, dict) and str(row.get("id") or "").strip()\n    ]\n    if len(catalogue_ids) != 46 or len(set(catalogue_ids)) != 46:\n        raise SystemExit(f"current provider catalogue must contain 46 unique ids, got {len(catalogue_ids)}/{len(set(catalogue_ids))}")\n    catalogue_set = set(catalogue_ids)\n    baseline_rows = [row for row in baseline.get("providers") or [] if isinstance(row, dict) and pid(row) in catalogue_set]\n    missing_baseline = sorted(catalogue_set - {pid(row) for row in baseline_rows})\n    if missing_baseline:\n        raise SystemExit("historical baseline missing current providers: " + ",".join(missing_baseline))\n\n    lkg_path = ROOT / args.lkg\n'''
    text = once(text, old, new, rel + " baseline block")
    text = once(
        text,
        '    rows = {pid(row): row for row in baseline.get("providers") or [] if isinstance(row, dict) and pid(row)}\n',
        '    rows = {pid(row): row for row in baseline_rows if pid(row)}\n',
        rel + " row map",
    )
    text = once(
        text,
        '    targeted_ids = {pid(row) for row in targeted_rows}\n',
        '    targeted_ids = {pid(row) for row in targeted_rows}\n'
        '    outside = sorted(targeted_ids - catalogue_set)\n'
        '    if outside:\n'
        '        raise SystemExit("targeted report contains providers outside current catalogue: " + ",".join(outside))\n',
        rel + " target scope",
    )
    text = text.replace(
        '    if len(rows) != 46:\n        raise SystemExit(f"merged provider rows={len(rows)}, expected=46")',
        '    if len(rows) != len(catalogue_ids):\n        raise SystemExit(f"merged provider rows={len(rows)}, expected={len(catalogue_ids)}")',
    )
    text = text.replace(
        '        "providerCount": 46,\n        "catalogueProviderCount": 46,',
        '        "providerCount": len(catalogue_ids),\n        "catalogueProviderCount": len(catalogue_ids),',
    )
    text = text.replace(
        '            "preservedProviderCount": 96 - len(targeted_ids),',
        '            "preservedProviderCount": len(catalogue_ids) - len(targeted_ids),',
    )
    text = text.replace(
        'f"targeted={len(targeted_ids)} preserved={96-len(targeted_ids)} "',
        'f"targeted={len(targeted_ids)} preserved={len(catalogue_ids)-len(targeted_ids)} "',
    )
    write(rel, text)


def patch_finalizer() -> None:
    rel = "scripts/finalize_provider_repair_disposition_v1_impl.py"
    text = read(rel)
    text = text.replace(
        'description="Finalize Provider v3 repair diagnostics with 46-hub targeted activation"',
        'description="Finalize Provider v3 repair diagnostics with matrix-targeted activation"',
    )
    text = text.replace(
        'raise SystemExit(f"expected exact 46-hub activation matrix, got count={hub_matrix.get(\'hubCount\')} ids={len(target_hubs)}")',
        'raise SystemExit(f"active hub matrix mismatch: count={hub_matrix.get(\'hubCount\')} ids={len(target_hubs)}")',
    )
    old = '''        if complete and not quarantined:\n            route_state = "on"\n            reason_codes = ["all_declared_lanes_live_proven"]\n        else:\n            if quarantined or terminal:\n                route_state = "off"\n            else:\n                route_state = "repair"\n            reason_codes = []\n            if missing:\n                reason_codes.append("declared_lane_unproven")\n            if terminal:\n                reason_codes.append(terminal)\n            if quarantined:\n                reason_codes.append("explicit_quarantine")\n            status = str(recovery_row.get("status") or "").strip().casefold()\n            if status:\n                reason_codes.append("recovery_" + status.replace("_", "-"))\n            for stage in sorted(debug_stages.get(provider) or set()):\n                reason_codes.append("quick_" + stage.replace("_", "-"))\n            if not reason_codes:\n                reason_codes.append("repair_incomplete")\n            incomplete.append(provider)\n'''
    new = '''        manual_off_reason = str(patch.get("manual_off_reason") or "").strip()\n        manual_off = bool(manual_off_reason)\n        if manual_off:\n            route_state = "off"\n            reason_codes = [manual_off_reason]\n            complete = False\n        elif complete and not quarantined:\n            route_state = "on"\n            reason_codes = ["all_declared_lanes_live_proven"]\n        else:\n            if quarantined or terminal:\n                route_state = "off"\n            else:\n                route_state = "repair"\n            reason_codes = []\n            if missing:\n                reason_codes.append("declared_lane_unproven")\n            if terminal:\n                reason_codes.append(terminal)\n            if quarantined:\n                reason_codes.append("explicit_quarantine")\n            status = str(recovery_row.get("status") or "").strip().casefold()\n            if status:\n                reason_codes.append("recovery_" + status.replace("_", "-"))\n            for stage in sorted(debug_stages.get(provider) or set()):\n                reason_codes.append("quick_" + stage.replace("_", "-"))\n            if not reason_codes:\n                reason_codes.append("repair_incomplete")\n            incomplete.append(provider)\n'''
    text = once(text, old, new, rel + " manual off block")
    text = text.replace('"targetHubProviderCount": 46,', '"targetHubProviderCount": len(target_hubs),')
    text = text.replace(
        'f"diagnostic_incomplete={len(incomplete)} activation=hub_matrix_46"',
        'f"diagnostic_incomplete={len(incomplete)} activation=hub_matrix_active count={len(target_hubs)}"',
    )
    write(rel, text)


def patch_strategy_test() -> None:
    rel = "tests/provider_v3_strategy_plan_contract_test.py"
    text = read(rel)
    text = text.replace(
        "Provider v3 strategy-to-executable-plan contract for the hub-only 46 catalogue.",
        "Provider v3 strategy-to-executable-plan contract for the 46-row catalogue with matrix-driven activation.",
    )
    text = text.replace(
        '- the 46 providers in ``hub-lab-matrix-46.json`` are the complete executable catalogue;',
        '- active providers are exactly the rows currently declared by ``hub-lab-matrix-46.json``;',
    )
    text = text.replace(
        "    return quarantined or terminal in TERMINAL_DISABLED",
        '    return quarantined or terminal in TERMINAL_DISABLED or bool(str(patch.get("manual_off_reason") or "").strip())',
    )
    text = text.replace(
        '    assert int(matrix.get("hubCount") or 0) == 46, matrix.get("hubCount")\n    assert len(targets) == 46, len(targets)',
        '    declared = int(matrix.get("hubCount") or 0)\n    assert declared > 0, declared\n    assert len(targets) == declared, (len(targets), declared)',
    )
    text = text.replace(
        '    if enabled_count != 46:\n        failures.append(f"hub46 enabled count mismatch: {enabled_count} != 46")',
        '    if enabled_count != len(targets):\n        failures.append(f"active enabled count mismatch: {enabled_count} != {len(targets)}")',
    )
    text = text.replace(
        "    executable_count = 46 - diagnostic_non_executable",
        "    executable_count = len(rows) - diagnostic_non_executable",
    )
    text = text.replace(
        '        f"providers=46 enabled=46 disabled=0 executable={executable_count} diagnostic_non_executable={diagnostic_non_executable} "',
        '        f"providers={len(rows)} enabled={enabled_count} disabled={len(rows)-enabled_count} executable={executable_count} diagnostic_non_executable={diagnostic_non_executable} "',
    )
    write(rel, text)


def patch_native_scope_test() -> None:
    rel = "tests/native_hub46_scope_contract_test.py"
    text = read(rel)
    text = text.replace(
        'assert int(data.get("hubCount") or 0) == 46, data.get("hubCount")\nassert len(ids) == 46, len(ids)',
        'declared = int(data.get("hubCount") or 0)\nassert declared > 0, declared\nassert len(ids) == declared, (len(ids), declared)',
    )
    text = text.replace(
        'print("native Hub-46 rotating execution scope contract tests passed: providers=46 workflows=3")',
        'print(f"native active-scope rotating execution contract tests passed: providers={declared} workflows=3")',
    )
    write(rel, text)


def patch_sweep_planner() -> None:
    rel = "scripts/provider_parallel_sweep_plan_v1.py"
    text = read(rel)
    text = text.replace(
        "- manifest.json defines the complete 96-provider catalogue;",
        "- manifest.json defines the current 46-row recoverable catalogue and enabled executable subset;",
    )
    old = '''def catalogue() -> list[str]:\n    manifest = load(MANIFEST)\n    ids = [cid(row.get("id")) for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]\n    if len(ids) != EXPECTED or len(set(ids)) != EXPECTED:\n        raise SystemExit(f"provider catalogue must be exactly {EXPECTED} unique ids, got {len(ids)}/{len(set(ids))}")\n    return ids\n'''
    new = '''def catalogue() -> list[str]:\n    manifest = load(MANIFEST)\n    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]\n    ids = [cid(row.get("id")) for row in rows]\n    if len(ids) != EXPECTED or len(set(ids)) != EXPECTED:\n        raise SystemExit(f"provider catalogue must be exactly {EXPECTED} unique ids, got {len(ids)}/{len(set(ids))}")\n    active = [cid(row.get("id")) for row in rows if row.get("enabled") is True]\n    if not active:\n        raise SystemExit("provider executable scope is empty")\n    return active\n'''
    text = once(text, old, new, rel + " active catalogue")
    text = text.replace("    limit = max(1, min(int(args.limit), EXPECTED))", "    limit = max(1, int(args.limit))")
    write(rel, text)


def patch_hub_publication() -> None:
    rel = "scripts/hub_activation_publication.py"
    text = read(rel)
    if 'MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"' not in text:
        text = once(
            text,
            "EXPECTED = 46\n",
            'EXPECTED = 46\nMATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"\n',
            rel + " matrix const",
        )
    helper = '''\n\ndef active_scope() -> set[str]:\n    matrix = load("automation/evidence/hub-lab-matrix-46.json")\n    ids = {cid(row.get("manifestId") or row.get("provider")) for row in matrix.get("rows") or [] if isinstance(row, dict) and cid(row.get("manifestId") or row.get("provider"))}\n    declared = int(matrix.get("hubCount") or 0)\n    assert declared > 0 and len(ids) == declared, (declared, len(ids))\n    return ids\n'''
    if "def active_scope()" not in text:
        text = once(
            text,
            'def cid(value: object) -> str:\n    return str(value or "").strip().casefold().replace("_", "-")\n',
            'def cid(value: object) -> str:\n    return str(value or "").strip().casefold().replace("_", "-")\n' + helper,
            rel + " active helper",
        )
    text = text.replace(
        "    enabled, disabled = [], []\n    for row in rows:",
        "    targets = active_scope()\n    enabled, disabled = [], []\n    for row in rows:",
    )
    text = text.replace(
        '        hub = str(patch.get("official_hub") or "").strip()\n        expected = bool(hub)',
        "        expected = pid in targets",
    )
    text = text.replace(
        '        assert bool(row.get("enabled")) is expected, (pid, row.get("enabled"), hub)',
        '        assert bool(row.get("enabled")) is expected, (pid, row.get("enabled"), expected)',
    )
    text = text.replace(
        '        assert bool(mo.get("enabled")) is expected, (pid, mo.get("enabled"), hub)',
        '        assert bool(mo.get("enabled")) is expected, (pid, mo.get("enabled"), expected)',
    )
    text = text.replace(
        '"authority": "provider-overrides.json:provider_patches.*.official_hub",',
        '"authority": "automation/evidence/hub-lab-matrix-46.json:rows[].manifestId",',
    )
    text = text.replace(
        '        hub = str(patch.get("official_hub") or "").strip()\n        assert bool(scraper.get("enabled")) == bool(hub), (pid, scraper.get("enabled"), hub)',
        '        expected = pid in set(scope["enabledProviders"])\n        assert bool(scraper.get("enabled")) == expected, (pid, scraper.get("enabled"), expected)',
    )
    pattern = r"def append_memory\(scope: dict\) -> None:\n.*?\n\ndef main\(\) -> int:"
    replacement = '''def append_memory(scope: dict) -> None:\n    memory = ROOT / "MEMORY.md"\n    text = memory.read_text(encoding="utf-8")\n    marker = "## 2026-09-15 — active matrix publication authority"\n    if marker in text:\n        return\n    block = f"""\\n\\n{marker}\\n\\n- Recoverable catalogue census: **{scope['catalogueProviderCount']}**.\\n- Executable/visible providers: **{scope['enabledProviderCount']}**, owned by `automation/evidence/hub-lab-matrix-46.json`.\\n- Disabled providers: **{scope['disabledProviderCount']}**. `official_hub` is discovery/address metadata only and cannot activate a provider.\\n- Explicit manual OFF states remain disabled until separately re-authorized; Repair/Learn must not target them automatically.\\n"""\n    memory.write_text(text.rstrip() + block + "\\n", encoding="utf-8")\n\n\ndef main() -> int:'''
    text, count = re.subn(pattern, replacement, text, flags=re.S)
    if count != 1:
        raise SystemExit(f"{rel}: append_memory replacement count={count}")
    text = text.replace("Validate/persist declared-hub activation publication state.", "Validate/persist active-matrix publication state.")
    text = text.replace("explicit provider-overrides.json `official_hub` authority", "active provider matrix authority")
    write(rel, text)


def patch_release_normalizer() -> None:
    rel = "scripts/normalize_hub46_release_gate_sources.py"
    text = read(rel)
    pattern = r"def patch_strategy_plan_contract\(\) -> bool:\n.*?\n\ndef patch_engine_language_contract\(\) -> bool:"
    replacement = '''def patch_strategy_plan_contract() -> bool:\n    path = ROOT / "tests/provider_v3_strategy_plan_contract_test.py"\n    text = path.read_text(encoding="utf-8")\n    original = text\n    text = text.replace("    executable_count = 96 - diagnostic_non_executable\\n", "    executable_count = len(rows) - diagnostic_non_executable\\n")\n    text = text.replace("    executable_count = 46 - diagnostic_non_executable\\n", "    executable_count = len(rows) - diagnostic_non_executable\\n")\n    text = text.replace("    if enabled_count != 46:\\n        failures.append(f\\\"hub46 enabled count mismatch: {enabled_count} != 46\\\")", "    if enabled_count != len(targets):\\n        failures.append(f\\\"active enabled count mismatch: {enabled_count} != {len(targets)}\\\")")\n    if "enabled_count != 46" in text or "enabled=46 disabled=0" in text:\n        raise AssertionError("strategy plan still encodes a fixed active-provider count")\n    if text != original:\n        path.write_text(text, encoding="utf-8")\n        return True\n    return False\n\n\ndef patch_engine_language_contract() -> bool:'''
    text, count = re.subn(pattern, replacement, text, flags=re.S)
    if count != 1:
        raise SystemExit(f"{rel}: strategy normalizer replacement count={count}")
    write(rel, text)


def patch_misc() -> None:
    rel = "scripts/build_published_provider_stage.py"
    text = read(rel).replace(
        '    if len(rows)!=96:\n        raise SystemExit(f"published Provider v3 stage requires 96 rows, got {len(rows)}")',
        '    if len(rows)!=46:\n        raise SystemExit(f"published Provider v3 stage requires current 46-row census, got {len(rows)}")',
    )
    write(rel, text)

    rel = "scripts/validate_published_provider_config.py"
    write(rel, read(rel).replace('parser.add_argument("--expected", type=int, default=96)', 'parser.add_argument("--expected", type=int, default=46)'))

    rel = "scripts/apply_hub46_native_lab_scope.py"
    text = read(rel).replace("providers=46", "providers=active-scope")
    text = text.replace("exact physical Hub-46 manifest", "physical active-scope manifest")
    text = text.replace("global 96-provider manifest remains unchanged", "recoverable catalogue remains unchanged")
    write(rel, text)

    rel = "tests/provider_repair_pipeline_v6_contract_test.py"
    text = read(rel).replace(
        "only the 46 current-live-positive\n# matrix members are visible.",
        "only current matrix members are visible; the count is not hard-coded.",
    )
    write(rel, text)

    rel = ".github/workflows/main-route-proof-reconstruction.yml"
    write(rel, read(rel).replace("name: MAIN - Route Proof Reconstruction 96", "name: HISTORICAL - Route Proof Reconstruction 96"))


def patch_memory() -> None:
    rel = "MEMORY.md"
    text = read(rel)
    marker = "## 2026-09-15 — Active44 durability repair"
    if marker not in text:
        text = text.rstrip() + '''\n\n## 2026-09-15 — Active44 durability repair\n\n- Recoverable provider catalogue is 46 rows; executable/native/automatic-repair scope is matrix-driven and currently 44. DesiFlix and FullAnime are explicit OFF and must never be reactivated merely to satisfy an old cardinality.\n- Repair V6 and fast targeted Repair must reject explicit OFF providers, derive executable targets from `automation/evidence/hub-lab-matrix-46.json`, and may use the historical 96-provider proof baseline only as evidence filtered down to the current 46-row catalogue.\n- Existing user browser evidence is authoritative for avoiding duplicate manual requests: MoviesMod terminal media chain, 4KHDHub movie+TV chain, AllWish/AllAnime HLS 200, plus the larger manual-test history supplied 2026-09-15.\n- `official_hub` is discovery/address metadata, not activation authority. Current activation is the matrix plus explicit manual-OFF state.\n'''
    write(rel, text)


def main() -> int:
    patch_pipeline()
    patch_fast_repair()
    patch_merge()
    patch_finalizer()
    patch_strategy_test()
    patch_native_scope_test()
    patch_sweep_planner()
    patch_hub_publication()
    patch_release_normalizer()
    patch_misc()
    patch_memory()
    print("ACTIVE44_DURABILITY_PATCH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
