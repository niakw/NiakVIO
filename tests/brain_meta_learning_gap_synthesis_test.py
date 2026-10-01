#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import brain_meta_learning as meta

# Source-level guard: Python dict construction silently keeps the last duplicate
# key, so runtime equality cannot detect a duplicated failure-family literal.
# Architecture FORCE relies on exact focused source anchors; duplicate taxonomy
# literals make a valid Brain edit intrinsically ambiguous.
_source_tree = ast.parse((SCRIPTS / "brain_meta_learning.py").read_text(encoding="utf-8"))
_taxonomy_keys = []
for _node in _source_tree.body:
    _target = None
    _value = None
    if isinstance(_node, ast.AnnAssign) and isinstance(_node.target, ast.Name):
        _target, _value = _node.target.id, _node.value
    elif isinstance(_node, ast.Assign) and len(_node.targets) == 1 and isinstance(_node.targets[0], ast.Name):
        _target, _value = _node.targets[0].id, _node.value
    if _target == "FAILURE_FAMILY_TAXONOMY" and isinstance(_value, ast.Dict):
        _taxonomy_keys = [
            str(_key.value)
            for _key in _value.keys
            if isinstance(_key, ast.Constant) and isinstance(_key.value, str)
        ]
        break
assert _taxonomy_keys, "FAILURE_FAMILY_TAXONOMY literal not found"
assert len(_taxonomy_keys) == len(set(_taxonomy_keys)), _taxonomy_keys

layer_ids = {row["id"] for row in meta.ARCHITECTURE_LAYERS}
assert {
    "causal_failure_taxonomy",
    "capability_gap_detector",
    "meta_learning_gap_synthesis",
    "architecture_layer_synthesis",
    "verification_contract_synthesis",
    "negative_memory_novelty_guard",
    "force_architecture_promotion",
}.issubset(layer_ids), layer_ids

known = meta.diagnose_gap(
    failure_class="provider_network_zero_result",
    profile="search_contract_inference_v1",
    exhausted_profiles=["search_contract_inference_v1"],
)
assert known.failure_family in {"network_transport", "search_catalogue"}, known
assert known.needs_new_strategy is True, known
assert known.needs_new_layer is False, known

projection = meta.diagnose_gap(
    failure_class="published_bytes_projection_mismatch",
    profile="projection_check",
)
assert projection.failure_family == "materialization_projection", projection
assert projection.target_layer == "materialization", projection

novel = meta.diagnose_gap(
    failure_class="quantum_mux_observer_desync",
    profile="unknown_profile_v99",
    signature="future_protocol_shape_zeta",
    exhausted_profiles=["all_known_profiles"],
)
assert novel.failure_family == "unknown_new_failure", novel
assert novel.target_layer == "unknown-new-layer", novel
assert novel.needs_new_strategy is True, novel
assert novel.needs_new_layer is True, novel

blueprint = meta.synthesize_gap_blueprint(["demo", "demo"], novel)
assert blueprint["strategyId"] == "novel_architecture_layer_synthesis_v1", blueprint
assert blueprint["providers"] == ["demo"], blueprint
assert blueprint["forcePromotionEligible"] is True, blueprint
assert blueprint["productionWritesAllowed"] is False, blueprint
assert blueprint["providerPublicationAuthority"] is False, blueprint
assert "bounded executable implementation exists" in blueprint["acceptanceProof"], blueprint

print("Brain meta-learning gap synthesis tests passed")
