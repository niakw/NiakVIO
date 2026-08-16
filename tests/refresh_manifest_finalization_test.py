#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")

# ARCHI2 owns the complete quick/deep publication transaction. The old
# provider-refresh-repair workflow is intentionally gone; its finalization
# invariants now belong to sync.yml.
prepare_anchor = "mv manifest.next.json manifest.json"
build = "python scripts/build_provider_runtime_profiles.py"
normalize = "python scripts/reapply_published_overrides.py"
language = "python scripts/generate_language_manifests.py"
catalog = "node engine_v2/scripts/bootstrap-provider-catalog.mjs"
render = "node engine_v2/scripts/render-manifests-from-catalog.mjs"
catalog_test = "node engine_v2/tests/provider-catalog.test.mjs"
fingerprint = "python scripts/release_evidence_fence.py fingerprint"
audit = "python scripts/audit_catalogue_identity_media.py"
coverage = "python scripts/interstellar_nuvio_matrix.py"
hashes = "python scripts/generate_release_hashes.py"
verify = "Verify exact published main"

prepare_pos = workflow.index(prepare_anchor)
build_pos = workflow.index(build, prepare_pos)
normalize_pos = workflow.index(normalize, build_pos)
language_pos = workflow.index(language, normalize_pos)
catalog_pos = workflow.index(catalog, language_pos)
render_pos = workflow.index(render, catalog_pos)
catalog_test_pos = workflow.index(catalog_test, render_pos)
fingerprint_pos = workflow.index(fingerprint, catalog_test_pos)
audit_pos = workflow.index(audit, fingerprint_pos)
coverage_pos = workflow.index(coverage, audit_pos)
hashes_pos = workflow.index(hashes, coverage_pos)
verify_pos = workflow.index(verify, hashes_pos)

assert prepare_pos < build_pos < normalize_pos < language_pos, (
    "promoted manifest must be normalized before language projection"
)
assert language_pos < catalog_pos < render_pos < catalog_test_pos < fingerprint_pos, (
    "candidate manifests must enter the canonical catalog and be re-rendered/tested before evidence"
)
assert fingerprint_pos < audit_pos < coverage_pos < hashes_pos < verify_pos, (
    "content audit and diagnostic coverage must precede release hashes and exact-main verification"
)
assert "--minimum-automatic 10" not in workflow, (
    "coverage diagnostics must not block routine publication"
)
assert "--minimum-automatic 0" in workflow and "continue-on-error: true" in workflow, (
    "Interstellar coverage must be measured without becoming a publication gate"
)
assert "if: github.event_name != 'pull_request'" in workflow, (
    "PR validation must execute the real staging pipeline without publication permission"
)
assert "python scripts/normalize_provider_activation_overrides.py\n" in workflow
assert "python scripts/normalize_provider_activation_overrides.py --check" not in workflow
assert not (ROOT / ".github" / "workflows" / "provider-refresh-repair.yml").exists(), (
    "ARCHI2 must not keep a second refresh/publish orchestrator"
)

# Nuvio Desktop/Mobile/TV preserve a scraper's previous local enabled state when
# the client-visible scraper id is unchanged. A manifest-disabled -> enabled
# recovery therefore MUST receive a new case-only id, while enabled -> enabled
# refreshes must keep the id stable. This protects existing installations from
# remaining stuck on an old local `enabled=false` after a provider is repaired.
activation_script = ROOT / "scripts" / "nuvio_client_activation_ids.py"
spec = importlib.util.spec_from_file_location("nuvio_client_activation_ids_tested", activation_script)
assert spec is not None and spec.loader is not None
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)

with tempfile.TemporaryDirectory(prefix="niakvio-client-id-test-") as temp_dir:
    temp = Path(temp_dir)
    main_path = temp / "manifest.json"
    vf_dir = temp / "vf"
    vf_dir.mkdir()
    vf_path = vf_dir / "manifest.json"
    state_path = temp / "nuvio-client-id-state.json"

    main_payload = {
        "version": "9.9.9",
        "scrapers": [
            {
                "id": "RECOVERED",
                "name": "Recovered",
                "version": "1.2.3",
                "filename": "providers/recovered.js",
                "enabled": True,
                "supportedTypes": ["movie"],
                "contentLanguage": ["en"],
            },
            {
                "id": "STABLE",
                "name": "Stable",
                "version": "2.0.0",
                "filename": "providers/stable.js",
                "enabled": True,
                "supportedTypes": ["movie"],
            },
        ],
    }
    vf_payload = {
        "version": "9.9.9",
        "scrapers": [
            {
                "id": "RECOVERED",
                "name": "Recovered",
                "version": "1.2.3",
                "filename": "../providers/recovered.js",
                "enabled": True,
                "supportedTypes": ["movie"],
            }
        ],
    }
    state_payload = {
        "schema_version": 1,
        "strategy": "case-toggle-on-disabled-to-enabled",
        "providers": {
            "recovered": {"client_id": "RECOVERED", "enabled": False},
            "stable": {"client_id": "STABLE", "enabled": True},
        },
    }

    for path, payload in ((main_path, main_payload), (vf_path, vf_payload), (state_path, state_payload)):
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    activation.MAIN_PATH = main_path
    activation.VF_PATH = vf_path
    activation.STATE_PATH = state_path

    first = activation.apply_policy(bootstrap_active=False)
    first_main = json.loads(main_path.read_text(encoding="utf-8"))
    first_vf = json.loads(vf_path.read_text(encoding="utf-8"))
    first_state = json.loads(state_path.read_text(encoding="utf-8"))
    recovered = next(row for row in first_main["scrapers"] if row["name"] == "Recovered")
    stable = next(row for row in first_main["scrapers"] if row["name"] == "Stable")

    assert first["activation_transitions"] == ["recovered"]
    assert recovered["id"] == "recovered", "disabled->enabled must get a fresh case-only client id"
    assert recovered["version"] == "1.2.4", "reactivation must also invalidate the client code/version cache"
    assert stable["id"] == "STABLE" and stable["version"] == "2.0.0"
    assert first_vf["scrapers"][0]["id"] == recovered["id"]
    assert first_vf["scrapers"][0]["version"] == recovered["version"]
    assert first_vf["scrapers"][0]["filename"] == "../providers/recovered.js"
    assert first_state["providers"]["recovered"] == {"client_id": "recovered", "enabled": True}

    # Re-running an enabled generation must be idempotent: no repeated case
    # flip and no repeated version bump.
    second = activation.apply_policy(bootstrap_active=False)
    second_main = json.loads(main_path.read_text(encoding="utf-8"))
    second_recovered = next(row for row in second_main["scrapers"] if row["name"] == "Recovered")
    assert second["activation_transitions"] == []
    assert second_recovered["id"] == "recovered"
    assert second_recovered["version"] == "1.2.4"

    # A later disable keeps the current id; the next genuine recovery toggles it
    # once again so clients cannot inherit the disabled local state.
    second_recovered["enabled"] = False
    main_path.write_text(json.dumps(second_main, indent=2) + "\n", encoding="utf-8")
    activation.apply_policy(bootstrap_active=False)
    disabled_main = json.loads(main_path.read_text(encoding="utf-8"))
    disabled_recovered = next(row for row in disabled_main["scrapers"] if row["name"] == "Recovered")
    assert disabled_recovered["id"] == "recovered"

    disabled_recovered["enabled"] = True
    main_path.write_text(json.dumps(disabled_main, indent=2) + "\n", encoding="utf-8")
    third = activation.apply_policy(bootstrap_active=False)
    third_main = json.loads(main_path.read_text(encoding="utf-8"))
    third_recovered = next(row for row in third_main["scrapers"] if row["name"] == "Recovered")
    assert third["activation_transitions"] == ["recovered"]
    assert third_recovered["id"] == "RECOVERED"
    assert third_recovered["version"] == "1.2.5"

print("ARCHI2 manifest finalization + Nuvio client reactivation test passed")
