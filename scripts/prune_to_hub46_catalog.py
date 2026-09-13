#!/usr/bin/env python3
"""One-way catalogue migration: keep only the authoritative 46 hub providers active.

The 50 providers outside automation/evidence/hub-lab-matrix-46.json are removed
from active catalogue/config/materialization/repair projections. Their historical
ProviderBase bytes under provider-bases/ are deliberately preserved.

This script is idempotent and must never modify main implicitly.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"
EXPECTED = 46


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def targets() -> tuple[set[str], set[str]]:
    data = load(MATRIX)
    rows = [row for row in data.get("rows") or [] if isinstance(row, dict)]
    manifest_ids = {cid(row.get("manifestId")) for row in rows if cid(row.get("manifestId"))}
    registry_ids = {cid(row.get("registryId")) for row in rows if cid(row.get("registryId"))}
    if int(data.get("hubCount") or 0) != EXPECTED or len(manifest_ids) != EXPECTED or len(registry_ids) != EXPECTED:
        raise SystemExit(
            f"invalid hub46 authority: hubCount={data.get('hubCount')} manifest={len(manifest_ids)} registry={len(registry_ids)}"
        )
    return manifest_ids, registry_ids


def filter_manifest(path: Path, keep_manifest: set[str]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    data = load(path)
    rows = data.get("scrapers")
    if not isinstance(rows, list):
        return None
    kept = [row for row in rows if isinstance(row, dict) and cid(row.get("id")) in keep_manifest]
    for row in kept:
        row["enabled"] = True
    data["scrapers"] = kept
    dump(path, data)
    return data


def filter_provider_catalog(path: Path, keep_registry: set[str]) -> set[str]:
    data = load(path)
    providers = data.get("providers") if isinstance(data.get("providers"), list) else []
    old_ids = {cid(row.get("canonicalId")) for row in providers if isinstance(row, dict) and cid(row.get("canonicalId"))}
    data["providers"] = [
        row for row in providers if isinstance(row, dict) and cid(row.get("canonicalId")) in keep_registry
    ]
    order = data.get("manifestOrder")
    if isinstance(order, dict):
        for key, values in list(order.items()):
            if isinstance(values, list):
                order[key] = [value for value in values if cid(value) in keep_registry]
    policy = data.get("policy")
    if isinstance(policy, dict):
        for key in ("committedProviderNameCount", "committedProviderLogoCount"):
            if key in policy:
                policy[key] = EXPECTED
    dump(path, data)
    return old_ids


def filter_keyed_provider_dict(path: Path, keys: tuple[str, ...], keep_registry: set[str]) -> None:
    if not path.is_file():
        return
    data = load(path)
    changed = False
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            data[key] = {k: v for k, v in value.items() if cid(k) in keep_registry}
            changed = True
    if changed:
        dump(path, data)


def filter_materialization(path: Path, keep_registry: set[str]) -> None:
    if not path.is_file():
        return
    data = load(path)
    rows = data.get("providers") if isinstance(data.get("providers"), list) else []
    data["providers"] = [row for row in rows if isinstance(row, dict) and cid(row.get("provider")) in keep_registry]
    data["providerCount"] = EXPECTED
    data["expectedProviderCount"] = EXPECTED
    dump(path, data)


def filter_disposition(path: Path, keep_registry: set[str]) -> None:
    if not path.is_file():
        return
    data = load(path)
    providers = data.get("providers") if isinstance(data.get("providers"), list) else []
    providers = [row for row in providers if isinstance(row, dict) and cid(row.get("provider")) in keep_registry]
    data["providers"] = providers
    data["catalogueProviderCount"] = EXPECTED
    data["enabledProviderCount"] = EXPECTED
    data["disabledProviderCount"] = 0
    data["disabledProviders"] = []
    if isinstance(data.get("policy"), dict):
        data["policy"]["targetHubProviderCount"] = EXPECTED
        data["policy"]["nonTargetProviderState"] = "removed-from-catalogue-providerbase-history-only"
    incomplete = [cid(v) for v in data.get("incompleteProviders") or [] if cid(v) in keep_registry]
    data["incompleteProviders"] = incomplete
    data["incompleteProviderCount"] = len(incomplete)
    states = Counter(str(row.get("routeDataState") or "repair") for row in providers)
    data["stateCounts"] = {key: states.get(key, 0) for key in ("off", "on", "repair")}
    dump(path, data)


def filter_named_provider_lists(path: Path, keep_registry: set[str]) -> None:
    if not path.is_file():
        return
    data = load(path)
    changed = False
    for key, value in list(data.items()):
        if isinstance(value, list) and (key.lower().endswith("providers") or key.lower().endswith("providerids")):
            if all(not isinstance(item, dict) for item in value):
                data[key] = [item for item in value if cid(item) in keep_registry]
                changed = True
    for key in ("providerCount", "catalogueProviderCount", "expectedProviderCount"):
        if key in data and isinstance(data.get(key), int):
            data[key] = EXPECTED
            changed = True
    if changed:
        dump(path, data)


def delete_excluded_generated_bundles(excluded: set[str]) -> list[str]:
    deleted: list[str] = []
    out = ROOT / "providers"
    if not out.is_dir():
        return deleted
    ordered = sorted(excluded, key=len, reverse=True)
    for path in out.glob("*.js"):
        name = path.name.casefold()
        if any(name.startswith(slug + "-") for slug in ordered):
            path.unlink()
            deleted.append(path.relative_to(ROOT).as_posix())
    return deleted


def patch_contract_counts() -> None:
    replacements = {
        "scripts/materialize_provider_v3_all.py": [
            ("EXPECTED_PROVIDER_COUNT = 96", "EXPECTED_PROVIDER_COUNT = 46"),
        ],
        "scripts/audit_provider_v3_static.py": [
            ("exact 96 Provider v3 bytes", "exact 46 hub Provider v3 bytes"),
            ("assert len(rows)==96 and len(reports)==96", "assert len(rows)==46 and len(reports)==46"),
            ("material.get(\"providerCount\")==96 and material.get(\"expectedProviderCount\")==96", "material.get(\"providerCount\")==46 and material.get(\"expectedProviderCount\")==46"),
            ("providers=96 reconstruction=false", "providers=46 reconstruction=false"),
        ],
        "scripts/provider_route_reconstructor.py": [
            ("EXPECTED_PROVIDERS = 96", "EXPECTED_PROVIDERS = 46"),
        ],
        "scripts/check_provider_non_regression_v1.py": [
            ("EXPECTED = 96", "EXPECTED = 46"),
        ],
        "scripts/finalize_provider_repair_disposition_v1_impl.py": [
            ("EXPECTED = 96", "EXPECTED = 46"),
        ],
        "scripts/hub_activation_publication.py": [
            ("EXPECTED = 96", "EXPECTED = 46"),
        ],
        "scripts/provider_parallel_sweep_plan_v1.py": [
            ("EXPECTED = 96", "EXPECTED = 46"),
        ],
        "scripts/merge_provider_repair_report_v6.py": [
            ("len(rows) != 96", "len(rows) != 46"),
            ("expected=96", "expected=46"),
            ('"providerCount": 96', '"providerCount": 46'),
            ('"catalogueProviderCount": 96', '"catalogueProviderCount": 46'),
        ],
        "scripts/run_provider_repair_pipeline_v6.py": [
            ('"catalogueProviderCount": 96', '"catalogueProviderCount": 46'),
        ],
        "scripts/run_provider_repair_fast_targeted_v1.py": [
            ('"catalogueProviderCount": 96', '"catalogueProviderCount": 46'),
        ],
        "scripts/provider_live_baseline.py": [
            ('locks.get("catalogueProviderCount") or 96', 'locks.get("catalogueProviderCount") or 46'),
        ],
        "tests/provider_v3_strategy_plan_contract_test.py": [
            ("full 96 catalogue", "hub-only 46 catalogue"),
            ("all 96 canonical Provider Objects remain present for census/recoverability;", "only the 46 hub Provider Objects remain in the executable catalogue;"),
            ("exactly the 46 providers in ``hub-lab-matrix-46.json`` are enabled targets;", "the 46 providers in ``hub-lab-matrix-46.json`` are the complete executable catalogue;"),
            ("the remaining 50 providers stay disabled and Repair must not widen the set;", "non-hub providers survive only as historical ProviderBase bytes and Repair must not resurrect them;"),
            ('assert len(rows) == 96, f"expected full 96-provider catalogue, got {len(rows)}"', 'assert len(rows) == 46, f"expected hub-only 46-provider catalogue, got {len(rows)}"'),
            ('assert len(set(ids)) == 96, "provider ids must be unique after canonical case-fold"', 'assert len(set(ids)) == 46, "provider ids must be unique after canonical case-fold"'),
        ],
    }
    for rel, pairs in replacements.items():
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in pairs:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")


def update_docs() -> None:
    exact = {
        "README.md": [("96 Provider Objects", "46 Hub Provider Objects")],
        "README.fr.md": [("96 Provider Objects", "46 Provider Objects Hub")],
        "ARCHITECTURE.md": [
            ("Le catalogue de travail couvre **les 96 Provider Objects**, providers désactivés compris.", "Le catalogue exécutable couvre **46 Provider Objects Hub**. Les providers hors Hub ne sont plus des lignes OFF : seuls leurs ProviderBase historiques restent archivés sous `provider-bases/`."),
        ],
        "VALIDATION.md": [
            ("couvre les 96 Provider Objects ;", "couvre les 46 Provider Objects Hub ;"),
        ],
        "automation/OPEN-TASKS-20260911.md": [
            ("- Canonical catalogue remains **96 Provider Objects** for census/recoverability.\n- **Exactly the 46 providers listed by `automation/evidence/hub-lab-matrix-46.json -> rows[].manifestId` are enabled.**\n- The other **50 providers remain disabled**. Repair/Learn must not widen this activation set.", "- Canonical executable catalogue is **exactly the 46 providers** listed by `automation/evidence/hub-lab-matrix-46.json -> rows[].manifestId`.\n- Non-hub providers are **not OFF rows anymore**; only their historical ProviderBase bytes remain under `provider-bases/`. Repair/Learn must not resurrect them."),
        ],
    }
    for rel, pairs in exact.items():
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in pairs:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")


def verify(keep_manifest: set[str], keep_registry: set[str], excluded: set[str]) -> None:
    manifest = load(ROOT / "manifest.json")
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    ids = {cid(row.get("id")) for row in rows}
    assert len(rows) == EXPECTED and ids == keep_manifest, (len(rows), sorted(keep_manifest - ids), sorted(ids - keep_manifest))
    assert all(row.get("enabled") is True for row in rows)

    catalog = load(ROOT / "provider_catalog.json")
    cids = {cid(row.get("canonicalId")) for row in catalog.get("providers") or [] if isinstance(row, dict)}
    assert len(cids) == EXPECTED and cids == keep_registry

    overrides = load(ROOT / "provider-overrides.json")
    patches = {cid(k) for k in (overrides.get("provider_patches") or {})}
    assert patches <= keep_registry, sorted(patches - keep_registry)

    material = load(ROOT / "provider-v3-materialization.json")
    mids = {cid(row.get("provider")) for row in material.get("providers") or [] if isinstance(row, dict)}
    assert len(mids) == EXPECTED and mids == keep_registry

    disposition = load(ROOT / "automation/provider-repair-disposition.json")
    dids = {cid(row.get("provider")) for row in disposition.get("providers") or [] if isinstance(row, dict)}
    assert len(dids) == EXPECTED and dids == keep_registry
    assert disposition.get("disabledProviderCount") == 0 and not disposition.get("disabledProviders")

    for slug in excluded:
        assert any((ROOT / "provider-bases").glob(f"{slug}--base--*.js")), f"missing historical ProviderBase for {slug}"
        assert not any((ROOT / "providers").glob(f"{slug}-*.js")), f"excluded generated bundle remains for {slug}"


def main() -> int:
    keep_manifest, keep_registry = targets()

    catalog_path = ROOT / "provider_catalog.json"
    old_registry = filter_provider_catalog(catalog_path, keep_registry)
    excluded = old_registry - keep_registry
    if len(excluded) != 50:
        # Idempotent reruns after the migration naturally see no excluded rows.
        if old_registry != keep_registry:
            raise SystemExit(f"unexpected excluded provider count: {len(excluded)}")
        excluded = set()

    root_manifest = filter_manifest(ROOT / "manifest.json", keep_manifest)
    assert root_manifest is not None
    for rel in ("vf/manifest.json", "no-anime/manifest.json"):
        filter_manifest(ROOT / rel, keep_manifest)

    # Hub projections must follow the current repaired root bytes, not an older snapshot.
    dump(ROOT / "manifest-hub46.json", root_manifest)
    dump(ROOT / "native-hub46/manifest.json", root_manifest)

    filter_keyed_provider_dict(
        ROOT / "provider-overrides.json",
        ("provider_patches", "provider_capabilities"),
        keep_registry,
    )
    filter_keyed_provider_dict(
        ROOT / "automation/provider-v3-static-knowledge.json",
        ("providers",),
        keep_registry,
    )
    filter_materialization(ROOT / "provider-v3-materialization.json", keep_registry)
    filter_disposition(ROOT / "automation/provider-repair-disposition.json", keep_registry)
    filter_named_provider_lists(ROOT / "automation/provider-live-baseline-locks.json", keep_registry)
    filter_named_provider_lists(ROOT / "automation/provider-repair-v6-summary.json", keep_registry)

    deleted = delete_excluded_generated_bundles(excluded)
    patch_contract_counts()
    update_docs()

    # If this is an idempotent rerun, reconstruct the excluded set from ProviderBase-only history
    # solely for verification of no generated resurrection.
    if not excluded:
        all_bases = {
            re.sub(r"--base--[0-9a-f]+\.js$", "", p.name.casefold())
            for p in (ROOT / "provider-bases").glob("*--base--*.js")
        }
        excluded = all_bases - keep_registry

    verify(keep_manifest, keep_registry, excluded)
    print(f"HUB46_CATALOG_PRUNE_OK active={EXPECTED} removed_generated={len(deleted)} providerbase_history_preserved={len(excluded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
