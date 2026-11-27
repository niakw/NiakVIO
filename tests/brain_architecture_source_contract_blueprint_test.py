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

mixed_family_queue={
    **queue,
    "sourceContractFamilyExecutableStatus":"mixed_source_contract_frontier",
    "sourceContractProviderStates":{
        "sample-anime":"new_family_required",
        "another-sibling":"new_family_required",
        "advanced-sibling":"player_target_observed",
    },
}
mixed_family_summary={
    **summary,
    "sourceContractFamilyExecutableStatus":"mixed_source_contract_frontier",
    "sourceContractProviderStates":{
        "sample-anime":"new_family_required",
        "another-sibling":"new_family_required",
        "advanced-sibling":"player_target_observed",
    },
}
mixed_family=arch.source_contract_family_blueprint(
    mixed_family_queue,mixed_family_summary,installed_source_family=False
)
assert mixed_family is not None,mixed_family
bad_mixed_family={
    **mixed_family_queue,
    "sourceContractProviderStates":{
        **mixed_family_queue["sourceContractProviderStates"],
        "another-sibling":"player_target_observed",
    },
}
assert arch.source_contract_family_blueprint(
    bad_mixed_family,mixed_family_summary,installed_source_family=False
) is None

resolver_queue={
    **queue,
    "sourceContractFamilyExecutableStatus":"resolver_family_required",
    "sourceContractResolverProviders":["sample-anime","another-sibling"],
    "sourceContractResolverProviderCount":2,
    "sourceContractResolverContract":"same-origin-api-lien-j-l-v1",
}
resolver_summary={
    **summary,
    "sourceContractFamilyExecutableStatus":"resolver_family_required",
    "sourceContractResolverProviders":["another-sibling","sample-anime"],
    "sourceContractResolverProviderCount":2,
    "sourceContractResolverContract":"same-origin-api-lien-j-l-v1",
}
resolver_blueprint=arch.source_contract_resolver_blueprint(
    resolver_queue,resolver_summary,installed_parser=True,installed_resolver=False
)
assert resolver_blueprint is not None
assert resolver_blueprint["strategyId"]=="catalogue_inline_token_resolver_v2"
assert resolver_blueprint["evolvesFromStrategyId"]=="runtime_response_salvage_v1"
assert resolver_blueprint["requiresNewExecutableRepairProfile"] is True
assert resolver_blueprint["requiresNewSourceFamilyLego"] is False
assert resolver_blueprint["sourceCompilerContract"]=="opaque-token-resolver-v1"
assert resolver_blueprint["resolverContract"]=="same-origin-api-lien-j-l-v1"
assert resolver_blueprint["forcePromotionEligible"] is True
mixed_resolver_queue={
    **resolver_queue,
    "sourceContractFamilyExecutableStatus":"mixed_source_contract_frontier",
    "sourceContractProviderStates":{
        "sample-anime":"resolver_family_required",
        "another-sibling":"resolver_family_required",
        "parser-only":"parser_installed_replay_required",
    },
}
mixed_resolver_summary={
    **resolver_summary,
    "sourceContractFamilyExecutableStatus":"mixed_source_contract_frontier",
    "sourceContractProviderStates":{
        "sample-anime":"resolver_family_required",
        "another-sibling":"resolver_family_required",
        "parser-only":"parser_installed_replay_required",
    },
}
mixed_resolver=arch.source_contract_resolver_blueprint(
    mixed_resolver_queue,mixed_resolver_summary,
    installed_parser=True,installed_resolver=False,
)
assert mixed_resolver is not None,mixed_resolver
bad_mixed_resolver={
    **mixed_resolver_queue,
    "sourceContractProviderStates":{
        **mixed_resolver_queue["sourceContractProviderStates"],
        "sample-anime":"player_target_observed",
    },
}
assert arch.source_contract_resolver_blueprint(
    bad_mixed_resolver,mixed_resolver_summary,
    installed_parser=True,installed_resolver=False,
) is None

assert arch.source_contract_resolver_blueprint(
    resolver_queue,resolver_summary,installed_parser=False,installed_resolver=False
) is None
assert arch.source_contract_resolver_blueprint(
    resolver_queue,resolver_summary,installed_parser=True,installed_resolver=True
) is None
for forged in (
    {"sourceContractResolverContract":"other"},
    {"sourceContractResolverProviders":[]},
    {"sourceContractFamilyExecutableStatus":"parser_installed_replay_required"},
):
    bad={**resolver_queue,**forged}
    assert arch.source_contract_resolver_blueprint(
        bad,resolver_summary,installed_parser=True,installed_resolver=False
    ) is None
print("Brain architecture source contract: novel family selected only before install; installed parser suppresses duplicate FORCE")
