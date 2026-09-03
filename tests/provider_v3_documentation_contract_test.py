#!/usr/bin/env python3
"""Fail closed when documentation/workflows drift back to pre-Provider-v3 ownership."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
readme_fr = (ROOT / "README.fr.md").read_text(encoding="utf-8")
health = (ROOT / "HEALTH-CHECK.md").read_text(encoding="utf-8")
contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
install = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
upstreams = (ROOT / "UPSTREAMS.md").read_text(encoding="utf-8")
engine = (ROOT / "engine_v2/README.md").read_text(encoding="utf-8")
sync = (ROOT / ".github/workflows/sync.yml").read_text(encoding="utf-8")
manual = (ROOT / ".github/workflows/provider-v3-reconstruct-all.yml").read_text(encoding="utf-8")
machine = json.loads((ROOT / "automation/provider-v3-architecture.json").read_text(encoding="utf-8"))

for required in (
    "NIAKVIO_PROVIDER_BASE_OWNED_V3",
    "STARTFIX:<ID>",
    "CLOSEFIX:<ID>",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
    "provider-v3-reconstruct-all.yml",
    "TVAndroid",
    "MobileAndroid",
    "MobileIOS",
    "DesktopMACOS",
    "DesktopWindows",
    "Quick/Deep ne réparent ni ne reconstruisent les providers",
):
    assert required in architecture, required

for text, label in (
    (architecture, "ARCHITECTURE"),
    (readme, "README"),
    (readme_fr, "README.fr"),
    (health, "HEALTH-CHECK"),
    (contributing, "CONTRIBUTING"),
    (install, "INSTALL"),
    (security, "SECURITY"),
    (upstreams, "UPSTREAMS"),
    (engine, "engine_v2/README"),
):
    for forbidden in (
        "NIAKVIO_PROVIDER_BASE_OWNED_V2",
        "core-media-finalize-main.yml",
        ".github/triggers/deep-provider-repair",
        "Quick est une maintenance **réparatrice",
        "Quick handles routine maintenance such as hub/domain refresh, canonical provider validation and bounded repairs",
        "canonical production control plane",
        "maintenance courante, repair-first",
        "Une correction générique appartient à ARCHI 2",
    ):
        assert forbidden not in text, f"{label}: stale architecture contract: {forbidden}"

assert "FIELD_PROVIDER_VERIFY_MODE mode=$MODE repair=false reconstruction=false" in sync
assert "python scripts/materialize_provider_v3_all.py" not in sync
assert "run_adaptive_quick_repair.py" not in sync
assert "run_adaptive_deep_repair.py" not in sync

assert "NUVIO_PROVIDER_V3_CONTEXT: workspace" in manual
assert 'GITHUB_REF_NAME}" != "main"' in manual
assert "python scripts/materialize_provider_v3_all.py" in manual
assert "python scripts/verify_provider_v3_reverse_rebuild.py" in manual

assert machine["schema_version"] >= 2
source = machine["provider_source_of_truth"]
assert source["canonical_provider_base_marker"] == "NIAKVIO_PROVIDER_BASE_OWNED_V3"
assert source["legacy_provider_js_seed_allowed"] is False
assert source["upstream_provider_js_seed_allowed"] is False
assert source["published_provider_js_is_reconstruction_seed"] is False
assert machine["routine"]["quick"]["repair_allowed"] is False
assert machine["routine"]["quick"]["provider_reconstruction_allowed"] is False
assert machine["routine"]["deep"]["repair_allowed"] is False
assert machine["routine"]["deep"]["provider_reconstruction_allowed"] is False
assert machine["manual_reconstruction"]["main_write_allowed"] is False
assert machine["native_labs"] == [
    "TVAndroid",
    "MobileAndroid",
    "MobileIOS",
    "DesktopMACOS",
    "DesktopWindows",
]
assert machine["minifier"]["enabled_in_production"] is False
assert machine["minifier"]["phase"] == "audit-only"
assert machine["minifier"]["audit_tool"] == "scripts/provider_v3_minimizer.py"
assert machine["minifier"]["transformations_enabled"] == []
assert machine["minifier"]["terser_allowed"] is False
assert machine["reference_reconstruction"]["retry"] == 21
assert machine["reference_reconstruction"]["generation"] == "9ddd9f969838d444"
assert machine["reference_reconstruction"]["reconstruction_sha"] == "8e3f40c318d923e83b1dc49320fc1e4b68efe2cd"
assert machine["reference_reconstruction"]["reverse_byte_identical"] == "96/96"
assert machine["reference_reconstruction"]["release_integrity"] is True
lab = machine["native_lab_contract"]
assert lab["provider_count"] == 96
assert lab["declared_routes"] == 214
assert lab["declared_routes_by_type"] == {"movie": 82, "tv": 92, "anime": 40}
assert lab["coverage_is_blocking"] is True
assert lab["reader_outcomes_are_observational"] is True
assert lab["external_nuvio_repo_repairs_allowed"] is False

# Dead orchestration trigger from the old repair world must not silently return.
assert "exactement cinq Labs" in install
assert "8 jours" in install
assert "ProviderBase v3 + structured DATA + owned Lego" in security
assert "ne sont **pas** rafraîchis par CORE Deep" in upstreams
assert "jamais une seed JavaScript exécutable" in upstreams
assert not (ROOT / ".github/triggers/deep-provider-repair").exists()

# Active workflows may use bounded repair primitives only in the Learning world;
# Quick/Deep/native acceptance must never call the old adaptive repair orchestrators.
for path in (ROOT / ".github/workflows").glob("*.yml"):
    text = path.read_text(encoding="utf-8")
    if path.name == "brain-learning-lab.yml":
        continue
    assert "run_adaptive_quick_repair.py" not in text, path.name
    assert "run_adaptive_deep_repair.py" not in text, path.name

print("Provider v3 documentation and workflow ownership contract passed")
