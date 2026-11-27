#!/usr/bin/env python3
"""A native-attested source contract becomes a novel Brain architecture blueprint.

This does NOT authorize changing provider JS or publishing a stream.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts/build_brain_architecture_proposal.py"
FORCE = ROOT / "scripts/brain_architecture_force_materializer.py"
spec = importlib.util.spec_from_file_location("source_blueprint_arch", SRC)
assert spec and spec.loader
arch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arch)

f_spec = importlib.util.spec_from_file_location("source_blueprint_force", FORCE)
assert f_spec and f_spec.loader
force = importlib.util.module_from_spec(f_spec)
f_spec.loader.exec_module(force)

AUTH = "native-parent-and-independent-source-exact-current-js-diagnostic-only"
queue = {
    "sourceContractFamilyExecutableStatus": "new_family_required",
    "sourceContractFamilyEvidenceAuthority": AUTH,
    "sourceContractFamilyDeferredProviders": ["sample-anime", "another-sibling"],
    "sourceContractFamilyDeferredProviderCount": 2,
    "deferredRepairProviders": ["sample-anime", "another-sibling", "unrelated"],
}
summary = {
    "sourceContractFamilyExecutableStatus": "new_family_required",
    "sourceContractFamilyDeferredProviders": ["another-sibling", "sample-anime"],
    "sourceContractFamilyDeferredProviderCount": 2,
}
blueprint = arch.source_contract_family_blueprint(
    queue, summary, installed_source_family=False
)
assert blueprint is not None
assert blueprint["strategyId"] == "catalogue_inline_token_episode_source_family_v1"
assert blueprint["failureFamily"] == "catalogue_inline_episode_source"
assert blueprint["gapKind"] == "missing_source_contract_family_executable"
assert blueprint["providers"] == ["another-sibling", "sample-anime"]
assert blueprint["forcePromotionEligible"] is True
assert blueprint["requiresNewExecutableRepairProfile"] is False
assert blueprint["requiresNewSourceFamilyLego"] is True
assert blueprint["productionWritesAllowed"] is False
assert blueprint["providerPublicationAuthority"] is False
assert blueprint["targetLayer"] == "brain"
assert "official NuvioTV" in " ".join(blueprint["acceptanceProof"])
selected = force.select_blueprint(
    {"strategyBlueprints": [
        {"strategyId": "old-generic-traversal",
         "providers": ["sample-anime"], "forcePromotionEligible": True},
        blueprint,
    ]},
    target_provider="another-sibling",
)
assert selected["strategyId"] == blueprint["strategyId"]
assert "https://" not in json.dumps(blueprint)
assert "epsJeton" in blueprint["causalTrigger"]

def rejects(mod: dict, extra_summary: dict | None = None) -> bool:
    data = dict(queue)
    data.update(mod)
    return arch.source_contract_family_blueprint(
        data, summary if extra_summary is None else extra_summary,
        installed_source_family=False,
    ) is None

for bad in (
    {"sourceContractFamilyExecutableStatus": "unknown"},
    {"sourceContractFamilyEvidenceAuthority": "github-runner-is-native"},
    {"sourceContractFamilyDeferredProviders": ["unrelated"]},
    {"sourceContractFamilyDeferredProviders": ["../escape", "sample-anime"]},
    {"sourceContractFamilyDeferredProviders": ["sample-anime", "sample-anime"]},
    {"sourceContractFamilyDeferredProviders": ["sample-anime", "https://secret.invalid"]},
    {"sourceContractFamilyDeferredProviders": []},
    {"sourceContractFamilyDeferredProviderCount": 3},
    {"deferredRepairProviders": []},
):
    assert rejects(bad), bad
assert rejects({}, {
    "sourceContractFamilyExecutableStatus": "not_attested",
    "sourceContractFamilyDeferredProviders": ["another-sibling", "sample-anime"],
    "sourceContractFamilyDeferredProviderCount": 2,
})
assert rejects({}, {
    "sourceContractFamilyExecutableStatus": "new_family_required",
    "sourceContractFamilyDeferredProviders": ["another-sibling", "unrelated"],
    "sourceContractFamilyDeferredProviderCount": 2,
})
assert arch.source_contract_family_blueprint(
    queue, summary, installed_source_family=True
) is None
print("Brain architecture source contract: novel family selected only before install; installed parser suppresses duplicate FORCE")
