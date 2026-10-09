#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "brain_architecture_force_materializer.py"
spec = importlib.util.spec_from_file_location("arch_force", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

patterns = [
    "scripts/brain_meta_learning.py",
    "scripts/brain_layers/*",
    "tests/brain_*",
]
assert mod.path_allowed(".github/workflows/brain-learning-lab.yml", patterns) is False
assert mod.path_allowed("engine_v2/config/brain-policy.json", patterns) is False

with tempfile.TemporaryDirectory(prefix="brain-arch-force-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")

    edits = [
        {
            "operation": "replace",
            "path": "scripts/brain_meta_learning.py",
            "find": "VALUE = 1",
            "replace": "VALUE = 2",
        },
        {
            "operation": "create",
            "path": "tests/brain_generated_layer_test.py",
            "content": "assert True\n",
        },
    ]
    mod.validate_edits(edits, patterns, root=root)
    changed = mod.apply_edits(edits, root=root)
    assert changed == [
        "scripts/brain_meta_learning.py",
        "tests/brain_generated_layer_test.py",
    ]
    assert target.read_text(encoding="utf-8") == "VALUE = 2\n"

    for forbidden in (
        "providers/foo.js",
        "provider-bases/v3.js",
        "manifest.json",
        "provider-overrides.json",
    ):
        try:
            mod.validate_edits(
                [{"operation": "create", "path": forbidden, "content": "x"}],
                patterns,
                root=root,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"forbidden architecture FORCE path accepted: {forbidden}")

    try:
        mod.validate_edits(
            [{
                "operation": "create",
                "path": "tests/brain_only_test.py",
                "content": "assert True\n",
            }],
            patterns,
            root=root,
        )
    except ValueError as exc:
        assert "executable non-test change" in str(exc)
    else:
        raise AssertionError("test-only architecture FORCE change accepted")

proposal = {
    "strategyBlueprints": [
        {"strategyId": "x", "forcePromotionEligible": False},
        {
            "strategyId": "novel_architecture_layer_synthesis_v1",
            "forcePromotionEligible": True,
            "targetLayer": "unknown-new-layer",
        },
    ]
}
selected = mod.select_blueprint(proposal)
assert selected["strategyId"] == "novel_architecture_layer_synthesis_v1"

ctx = mod.source_context(
    {"targetLayer": "provider"},
    [
        "scripts/brain_meta_learning.py",
        "scripts/brain_repair_runtime.py",
        "scripts/adaptive_runtime/runtime_repair.py",
    ],
)
assert sum(len(v) for v in ctx.values()) <= mod.MAX_TOTAL_SOURCE_CONTEXT
assert all(len(v) <= mod.MAX_SOURCE_SNIPPET for v in ctx.values())

# Architecture FORCE must expose the executable implementation neighborhood,
# not just the beginning of a large runtime file. Otherwise Qwen sees generic
# taxonomies and can materialize a syntactically valid but causally empty edit.
synthetic = (
    "HEADER_ONLY = True\n"
    + ("prefix_value = 1\n" * 500)
    + 'elif new_strategy_id == "route_transition_graph_v1":\n'
    + '    IMPLEMENTATION_SENTINEL = "route graph execution"\n'
    + ("tail_value = 2\n" * 500)
)
focused = mod._focused_source_snippet(
    synthetic,
    {
        "strategyId": "route_transition_graph_v1",
        "repairScope": "route-to-terminal",
        "targetLayer": "core",
    },
    900,
)
assert "IMPLEMENTATION_SENTINEL" in focused
assert not focused.startswith("HEADER_ONLY")

focused_ctx = mod.source_context(
    {
        "strategyId": "route_transition_graph_v1",
        "repairScope": "route-to-terminal",
        "targetLayer": "core",
    },
    [
        "scripts/brain_meta_learning.py",
        "scripts/brain_repair_runtime.py",
        "scripts/adaptive_runtime/runtime_repair.py",
    ],
)
assert 'new_strategy_id == "route_transition_graph_v1"' in focused_ctx[
    "scripts/adaptive_runtime/runtime_repair.py"
]

evolved_patterns = [
    "scripts/brain_repair_runtime.py",
    "engine_v2/scripts/plan-repairs.mjs",
    "scripts/adaptive_runtime/runtime_repair.py",
]
evolved_ctx = mod.source_context(
    {
        "strategyId": "route_transition_graph_v2",
        "evolvesFromStrategyId": "route_transition_graph_v1",
        "requiresNewExecutableRepairProfile": True,
        "repairScope": "route-to-terminal",
        "targetLayer": "core",
    },
    evolved_patterns,
)
assert set(evolved_ctx) == set(mod.NEW_REPAIR_PROFILE_SURFACES), evolved_ctx
assert "route_transition_graph_v1" in evolved_ctx[
    "scripts/adaptive_runtime/runtime_repair.py"
]

# A FORCE evolution that claims a new Repair profile must wire the new strategy
# through the planner, Repair registry and adaptive runtime. Taxonomy-only edits
# are intentionally rejected before any direct-main promotion.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-new-profile-") as tmp:
    root = Path(tmp)
    files = {
        "scripts/brain_repair_runtime.py": 'PROFILES = {"route_transition_graph_v1"}\n',
        "engine_v2/scripts/plan-repairs.mjs": 'const PROFILES = ["route_transition_graph_v1"];\n',
        "scripts/adaptive_runtime/runtime_repair.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v1",\n'
            '}\n'
            'if new_strategy_id == "route_transition_graph_v1":\n'
            '    pass\n'
        ),
    }
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    blueprint = {
        "strategyId": "route_transition_graph_v2",
        "evolvesFromStrategyId": "route_transition_graph_v1",
        "requiresNewExecutableRepairProfile": True,
    }
    incomplete = [{
        "operation": "replace",
        "path": "scripts/brain_repair_runtime.py",
        "find": '{"route_transition_graph_v1"}',
        "replace": '{"route_transition_graph_v1", "route_transition_graph_v2"}',
    }]
    try:
        mod.validate_materialized_edits(
            incomplete,
            root=root,
            blueprint=blueprint,
        )
    except ValueError as exc:
        assert "must wire planner/runtime surfaces" in str(exc), exc
    else:
        raise AssertionError("taxonomy/registry-only evolved profile unexpectedly accepted")

    shared_parent_guard = [
        {
            "operation": "replace",
            "path": "scripts/brain_repair_runtime.py",
            "find": '{"route_transition_graph_v1"}',
            "replace": '{"route_transition_graph_v1", "route_transition_graph_v2"}',
        },
        {
            "operation": "replace",
            "path": "engine_v2/scripts/plan-repairs.mjs",
            "find": '["route_transition_graph_v1"]',
            "replace": '["route_transition_graph_v1", "route_transition_graph_v2"]',
        },
        {
            "operation": "replace",
            "path": "scripts/adaptive_runtime/runtime_repair.py",
            "find": 'if new_strategy_id == "route_transition_graph_v1":\n    pass',
            "replace": 'if new_strategy_id in {"route_transition_graph_v1", "route_transition_graph_v2"}:\n    pass',
        },
    ]
    try:
        mod.validate_materialized_edits(
            shared_parent_guard,
            root=root,
            blueprint=blueprint,
        )
    except ValueError as exc:
        assert "preserve evolved strategy parent guard" in str(exc), exc
    else:
        raise AssertionError("shared v1/v2 runtime guard unexpectedly accepted")

    complete = [
        {
            "operation": "replace",
            "path": "scripts/brain_repair_runtime.py",
            "find": '{"route_transition_graph_v1"}',
            "replace": '{"route_transition_graph_v1", "route_transition_graph_v2"}',
        },
        {
            "operation": "replace",
            "path": "engine_v2/scripts/plan-repairs.mjs",
            "find": '["route_transition_graph_v1"]',
            "replace": '["route_transition_graph_v1", "route_transition_graph_v2"]',
        },
        {
            "operation": "replace",
            "path": "scripts/adaptive_runtime/runtime_repair.py",
            "find": 'if new_strategy_id == "route_transition_graph_v1":\n    pass',
            "replace": (
                'if new_strategy_id == "route_transition_graph_v1":\n'
                '    pass\n'
                'elif new_strategy_id == "route_transition_graph_v2":\n'
                '    pass'
            ),
        },
    ]
    mod.validate_edits(complete, evolved_patterns, root=root)
    changed = mod.validate_materialized_edits(
        complete,
        root=root,
        blueprint=blueprint,
    )
    assert set(changed) == set(mod.NEW_REPAIR_PROFILE_SURFACES)
    assert all(
        "route_transition_graph_v2" not in (root / path).read_text(encoding="utf-8")
        for path in mod.NEW_REPAIR_PROFILE_SURFACES
    )

assert mod.MAX_MODEL_TOKENS <= 512
assert mod.MODEL_TIMEOUT_SECONDS == 180
assert mod.RETRY_MODEL_TOKENS <= 640
assert mod.RETRY_MODEL_TIMEOUT_SECONDS == 240
assert mod.VALIDATION_RETRY_MODEL_TOKENS <= 512
assert mod.VALIDATION_RETRY_TIMEOUT_SECONDS == 180
assert mod.RETRY_SOURCE_CONTEXT <= 3600
assert mod.MINIMAL_SOURCE_CONTEXT <= 1800
assert mod.MATERIALIZED_CORRECTION_ROUNDS == 3
assert mod.MAX_MATERIALIZED_FAILURE_CONTEXT <= 3200

fmt = mod._response_format()
assert fmt["type"] == "json_object"
assert fmt["schema"]["required"] == ["edits"]
assert fmt["schema"]["properties"]["edits"]["minItems"] == 1
assert fmt["schema"]["properties"]["edits"]["maxItems"] == mod.MAX_EDITS
assert fmt["schema"]["properties"]["edits"]["items"]["additionalProperties"] is False

# Model output parsing is resilient to the common bounded formatting defects
# observed in FORCE: prose/fences, trailing commas and Python-style dicts.
assert mod._parse_model_value({
    "choices": [{"message": {"content": 'Here is the result:\n{"edits":[{"operation":"create","path":"scripts/brain_layers/x.py","content":"X=1\\n",}],}'}}]
})["edits"][0]["path"] == "scripts/brain_layers/x.py"
assert mod._parse_model_value({
    "choices": [{"message": {"content": "{'edits':[{'operation':'create','path':'scripts/brain_layers/y.py','content':'Y=1\\n'}]}"}}]
})["edits"][0]["path"] == "scripts/brain_layers/y.py"
try:
    mod._parse_model_value({"choices": [{"message": {"content": "not an object"}}]})
except ValueError:
    pass
else:
    raise AssertionError("invalid model output unexpectedly parsed")

compact = mod._compact_payload({
    "sources": {"a": "x" * 4000, "b": "y" * 4000, "c": "z" * 4000},
    "architectureLayers": [
        {"id": "meta_learning_gap_synthesis"},
        {"id": "force_architecture_promotion"},
    ],
})
assert sum(len(v) for v in compact["sources"].values()) <= mod.RETRY_SOURCE_CONTEXT
assert [row["id"] for row in compact["architectureLayers"]] == [
    "meta_learning_gap_synthesis"
]

new_profile_payload = {
    "blueprint": {
        "strategyId": "route_transition_graph_v2",
        "evolvesFromStrategyId": "route_transition_graph_v1",
        "requiresNewExecutableRepairProfile": True,
    },
    "allowedPaths": list(mod.NEW_REPAIR_PROFILE_SURFACES),
    "contract": {"requireExecutableDiff": True},
    "sources": {
        path: (path + "\n") * 400
        for path in mod.NEW_REPAIR_PROFILE_SURFACES
    },
}
new_profile_compact = mod._new_repair_profile_payload(new_profile_payload)
runtime_path = mod.NEW_REPAIR_PROFILE_SURFACES[2]
assert set(new_profile_compact["sources"]) == {runtime_path}
assert new_profile_compact["exactAllowedPaths"] == [runtime_path]
assert new_profile_compact["existingAllowedPaths"] == [runtime_path]
assert new_profile_compact["deterministicWiring"] == list(mod.NEW_REPAIR_PROFILE_SURFACES[:2])
assert all(
    len(text) <= mod.NEW_PROFILE_SOURCE_CONTEXT_PER_SURFACE
    for text in new_profile_compact["sources"].values()
)

# Before Qwen authors an entirely new Repair strategy, the Brain must reuse
# verified negative execution signatures from THIS provider, without leaking
# URLs/secrets or treating prior failures as playable proof.
with tempfile.TemporaryDirectory(prefix="brain-force-negative-evidence-") as tmp:
    evidence_root = Path(tmp)
    (evidence_root / "automation").mkdir(parents=True)
    (evidence_root / "automation/provider-census-status.json").write_text(
        json.dumps({"providers": [
            {"provider": "4khdhub", "status": "ROUTE PROVEN",
             "dominantIssue": "provider_network_zero_result×2", "repairEligible": True},
            {"provider": "other", "status": "FULL OK", "dominantIssue": ""},
        ]}), encoding="utf-8",
    )
    (evidence_root / "automation/brain-repair-memory.json").write_text(
        json.dumps({"entries": [
            {"providerId": "4khdhub", "executionObserved": True,
             "lastOutcome": "rejected", "profile": "route_transition_graph_v2",
             "failureClass": "route_proven_gap", "observedPipelineStage": "player",
             "lastReason": "required_category_playable_proof:movie,tv"},
            {"providerId": "4khdhub", "executionObserved": True,
             "lastOutcome": "rejected", "profile": "secret_override",
             "lastReason": "https://private.example/token=bad"},
            {"providerId": "other", "executionObserved": True,
             "lastOutcome": "rejected", "profile": "unrelated",
             "lastReason": "other-provider-failure"},
        ]}), encoding="utf-8",
    )
    causal_payload = mod._new_repair_profile_payload(
        {
            **new_profile_payload,
            "blueprint": {
                **new_profile_payload["blueprint"],
                "providers": ["4khdhub"],
            },
        }, root=evidence_root,
    )
    causal = causal_payload["causalNegativeEvidence"]
    assert causal["authority"] == "sanitized-negatives-only-not-playback-proof"
    assert causal["currentProviderObservations"][0]["dominantFailure"] == "provider_network_zero_resultx2"
    assert causal["previouslyExecutedFailures"] == [{
        "provider": "4khdhub",
        "profile": "route_transition_graph_v2",
        "failureClass": "route_proven_gap",
        "pipelineStage": "player",
        "observedFailure": "required_category_playable_proof:movie,tv",
    }], causal
    assert "private.example" not in json.dumps(causal)
    assert "other-provider-failure" not in json.dumps(causal)

profile_calls = []
original_request = mod._model_request
try:
    def fake_profile_request(endpoint, model, payload, *, max_tokens, timeout, compact=False):
        profile_calls.append((payload, max_tokens, timeout, compact))
        assert set(payload["sources"]) == {runtime_path}
        assert payload["exactAllowedPaths"] == [runtime_path]
        if len(profile_calls) == 1:
            raise TimeoutError("synthetic new-profile timeout")
        import json
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "edits": [
                            {
                                "operation": "replace",
                                "path": path,
                                "find": "route_transition_graph_v1",
                                "replace": "route_transition_graph_v1 route_transition_graph_v2",
                            }
                            for path in [runtime_path]
                        ]
                    })
                }
            }]
        }

    mod._model_request = fake_profile_request
    profile_result = mod.call_model(
        "http://127.0.0.1:8080",
        "demo",
        new_profile_payload,
    )
    assert len(profile_result["edits"]) == 1
    assert profile_result["edits"][0]["path"] == runtime_path
    assert profile_calls[0][1:] == (
        mod.NEW_PROFILE_MODEL_TOKENS,
        mod.NEW_PROFILE_MODEL_TIMEOUT_SECONDS,
        True,
    )
    assert profile_calls[1][1:] == (
        mod.NEW_PROFILE_RETRY_MODEL_TOKENS,
        mod.NEW_PROFILE_RETRY_TIMEOUT_SECONDS,
        True,
    )
    assert all(
        len(text) <= 1800
        for text in profile_calls[1][0]["sources"].values()
    )
finally:
    mod._model_request = original_request

profile_retry = mod._validation_retry_payload(
    new_profile_payload,
    ValueError("materialized contract validation failed"),
    [{
        "operation": "replace",
        "path": "scripts/adaptive_runtime/runtime_repair.py",
        "find": "route_transition_graph_v1",
        "replace": "route_transition_graph_v2",
    }],
    extra_exact_paths=list(mod.NEW_REPAIR_PROFILE_SURFACES),
    restrict_to_extra_paths=True,
)
assert set(profile_retry["sources"]) == {runtime_path}
assert profile_retry["exactAllowedPaths"] == [runtime_path]
assert profile_retry["correctionContract"]["preferSingleSmallReplace"] is True
assert profile_retry["correctionContract"]["mustPreserveEvolvesFromStrategy"] is True
assert profile_retry["correctionContract"]["mustUseAllRequiredRepairProfileSurfaces"] is False
assert profile_retry["correctionContract"]["modelEditsRuntimeOnly"] is True
assert profile_retry["correctionContract"]["plannerAndRegistryAutowired"] is True
assert profile_retry["correctionContract"]["requiredRepairProfileSurfaces"] == list(
    mod.NEW_REPAIR_PROFILE_SURFACES
)

calls = []
original_request = mod._model_request
try:
    def fake_request(endpoint, model, payload, *, max_tokens, timeout, compact=False):
        calls.append((max_tokens, timeout, compact, sum(len(v) for v in (payload.get("sources") or {}).values())))
        if len(calls) == 1:
            raise TimeoutError("synthetic timeout")
        import json
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "edits": [{
                            "operation": "create",
                            "path": "scripts/brain_layers/demo.py",
                            "content": "VALUE = 1\n",
                        }]
                    })
                }
            }]
        }

    mod._model_request = fake_request
    result = mod.call_model(
        "http://127.0.0.1:8080",
        "demo",
        {
            "sources": {"a": "x" * 4000, "b": "y" * 4000},
            "architectureLayers": [{"id": "meta_learning_gap_synthesis"}],
        },
    )
    assert result["edits"][0]["path"] == "scripts/brain_layers/demo.py"
    assert calls[0][:3] == (mod.MAX_MODEL_TOKENS, mod.MODEL_TIMEOUT_SECONDS, True)
    assert calls[0][3] <= mod.RETRY_SOURCE_CONTEXT
    assert calls[1][:3] == (mod.RETRY_MODEL_TOKENS, mod.RETRY_MODEL_TIMEOUT_SECONDS, True)
    assert calls[1][3] <= mod.MINIMAL_SOURCE_CONTEXT
    assert mod.MAX_MODEL_TOKENS <= 512
    assert mod.MODEL_TIMEOUT_SECONDS == 180
    assert mod.RETRY_MODEL_TOKENS <= 640
    assert mod.RETRY_MODEL_TIMEOUT_SECONDS == 240
finally:
    mod._model_request = original_request

# A syntactically incomplete primary answer is recoverable just like a timeout:
# retry once with the minimal architecture payload instead of failing the whole
# targeted Learning cohort.
calls = []
original_request = mod._model_request
try:
    def fake_invalid_then_valid(endpoint, model, payload, *, max_tokens, timeout, compact=False):
        calls.append((max_tokens, timeout, compact, sum(len(v) for v in (payload.get("sources") or {}).values())))
        if len(calls) == 1:
            return {"choices": [{"message": {"content": '{"edits":[{"operation":"create","path":"scripts/brain_layers/truncated.py","content":"X='}}]}
        import json
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "edits": [{
                            "operation": "create",
                            "path": "scripts/brain_layers/recovered.py",
                            "content": "VALUE = 2\n",
                        }]
                    })
                }
            }]
        }

    mod._model_request = fake_invalid_then_valid
    recovered = mod.call_model(
        "http://127.0.0.1:8080",
        "demo",
        {
            "blueprint": {"strategyId": "demo"},
            "allowedPaths": ["scripts/brain_layers/*"],
            "contract": {"requireExecutableDiff": True},
            "sources": {"a": "x" * 4000, "b": "y" * 4000},
            "architectureLayers": [{"id": "meta_learning_gap_synthesis"}],
        },
    )
    assert recovered["edits"][0]["path"] == "scripts/brain_layers/recovered.py"
    assert len(calls) == 2
    assert calls[1][3] <= mod.MINIMAL_SOURCE_CONTEXT
finally:
    mod._model_request = original_request


# FORCE Qwen only has to produce an executable runtime sibling. The Brain must
# fill planner/registry on current bytes, then validate/rollback all three.
with tempfile.TemporaryDirectory(prefix="brain-force-autowire-runtime-only-") as tmp:
    root = Path(tmp)
    baseline = {
        "scripts/brain_repair_runtime.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v1",\n'
            '}\n'
        ),
        "engine_v2/scripts/plan-repairs.mjs": (
            'const POST_EXHAUSTION_STRATEGIES = {\n'
            '  route_proven_gap: [\n'
            '    { profile: "route_transition_graph_v1", method: "existing" },\n'
            '  ],\n'
            '};\n'
        ),
        runtime_path: (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v1",\n'
            '}\n'
            'if new_strategy_id == "route_transition_graph_v1":\n'
            '    pass\n'
        ),
    }
    for path, content in baseline.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    blueprint = dict(new_profile_payload["blueprint"])
    blueprint["repairScope"] = "route-to-terminal"
    runtime_edit = {
        "operation": "replace",
        "path": runtime_path,
        "find": baseline[runtime_path],
        "replace": (
            baseline[runtime_path]
            + 'elif new_strategy_id == "route_transition_graph_v2":\n'
            + '    pass\n'
        ),
    }
    filled = mod.complete_evolved_profile_wiring([runtime_edit], blueprint, root=root)
    assert set(edit["path"] for edit in filled) == set(mod.NEW_REPAIR_PROFILE_SURFACES), filled
    mod.validate_edits(filled, evolved_patterns, root=root)
    assert set(mod.validate_materialized_edits(filled, root=root, blueprint=blueprint)) == set(baseline)
    assert all((root / path).read_text(encoding="utf-8") == content for path, content in baseline.items())
    assert mod.complete_evolved_profile_wiring(
        [{"operation": "replace", "path": "scripts/brain_repair_runtime.py",
          "find": "route_transition_graph_v1", "replace": "route_transition_graph_v2"}],
        blueprint, root=root,
    ) == [{
        "operation": "replace", "path": "scripts/brain_repair_runtime.py",
        "find": "route_transition_graph_v1", "replace": "route_transition_graph_v2"
    }], "taxonomy-only model edits must never be converted into fake executable repairs"

# The runtime snippet may be centered well inside the original focused source.
# A second prefix slice must not silently discard the parent executor branch.
long_runtime = ("START\n" * 650) + (
    'elif new_strategy_id == "route_transition_graph_v1":\n'
    '    EXECUTION_BRANCH_SENTINEL = 1\n'
) + ("END\n" * 650)
focused_payload = mod._new_repair_profile_payload({
    **new_profile_payload,
    "sources": {runtime_path: long_runtime},
})
assert "EXECUTION_BRANCH_SENTINEL" in focused_payload["sources"][runtime_path]

# Qwen must author only new algorithm statements: Brain deterministically
# wraps them in a separate sibling guard WITHOUT touching old runtime bytes.
with tempfile.TemporaryDirectory(prefix="brain-force-body-only-") as tmp:
    root = Path(tmp)
    fixtures = {
        "scripts/brain_repair_runtime.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v2",\n'
            '}\n'
        ),
        "engine_v2/scripts/plan-repairs.mjs": (
            'const POST_EXHAUSTION_STRATEGIES = {\n'
            '  route_proven_gap: [\n'
            '    { profile: "route_transition_graph_v2", method: "previous" },\n'
            '  ],\n'
            '};\n'
        ),
        "scripts/adaptive_runtime/runtime_repair.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v2",\n'
            '}\n'
            'if new_strategy_id == "route_transition_graph_v2":\n'
            '    search_paths = ["old-route"]\n'
            'elif new_strategy_id == "route_peer_transition_replay_v1":\n'
            '    search_paths = ["peer-route"]\n'
        ),
    }
    for relative, data in fixtures.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
    blueprint = {
        "strategyId": "route_transition_graph_v3",
        "evolvesFromStrategyId": "route_transition_graph_v2",
        "repairScope": "route-to-terminal",
        "requiresNewExecutableRepairProfile": True,
    }
    payload = {"blueprint": blueprint}
    body = 'search_paths = _unique_routes(configured_search, learned_search, limit=16)\nrequest_recipes = _unique_request_recipes(current_request_recipes, limit=24)\n'
    output = mod._model_edits({"branchBody": body}, payload, root=root)
    assert len(output) == 1 and output[0]["path"] == mod.NEW_REPAIR_PROFILE_SURFACES[2]
    assert 'elif new_strategy_id == "route_transition_graph_v3":' in output[0]["replace"]
    assert 'if new_strategy_id == "route_transition_graph_v2":' not in output[0]["find"]
    complete = mod.complete_evolved_profile_wiring(output, blueprint, root=root)
    assert len(complete) == 3
    mod.validate_edits(complete, list(mod.NEW_REPAIR_PROFILE_SURFACES), root=root)
    assert set(mod.validate_materialized_edits(complete, root=root, blueprint=blueprint)) == set(fixtures)
    assert all((root / k).read_text(encoding="utf-8") == v for k, v in fixtures.items())
    # 7B sometimes wraps its valid code in the generated child's guard.
    # Brain must remove ONLY that guard, never mutate the parent.
    wrapped_body = (
        'elif new_strategy_id == "route_transition_graph_v3":\n'
        '    search_paths = _unique_routes(configured_search, learned_search, limit=16)\n'
        '    request_recipes = _unique_request_recipes(current_request_recipes, limit=24)\n'
    )
    wrapped_edits = mod._model_edits({"branchBody": wrapped_body}, payload, root=root)
    assert wrapped_edits == output, "a valid child-only wrapper must normalize to the same guarded bytes"
    for bad_wrapper in (
        'elif new_strategy_id == "route_transition_graph_v2":\n    search_paths = []\n',
        'elif new_strategy_id == "route_transition_graph_v3":\n'
        '    search_paths = []\n'
        'else:\n'
        '    search_paths = ["/unsafe-fallback"]\n',
        'elif new_strategy_id == "route_transition_graph_v3":\n'
        '    search_paths = []\n'
        'elif new_strategy_id == "route_transition_graph_v2":\n'
        '    search_paths = []\n',
    ):
        try:
            mod._model_edits({"branchBody": bad_wrapper}, payload, root=root)
        except ValueError:
            pass
        else:
            raise AssertionError("multi-branch, parent or fallback guard accepted")

    # A rejected branchBody must be retried by the Brain, not abort the whole
    # Learning cohort outside the materializer's correction loop.
    original_correction = mod._request_corrected_plan
    correction_calls = []
    try:
        def fake_body_correction(endpoint, model, retry_payload):
            correction_calls.append(retry_payload)
            assert retry_payload["correctionReason"] == "branch-body-validation"
            assert retry_payload["correctionContract"]["branchBodyOnly"] is True
            return {"branchBody": body}
        mod._request_corrected_plan = fake_body_correction
        corrected, corrected_edits = mod._validated_generated_edits(
            "http://127.0.0.1:8080", "mock-7b", payload,
            {"branchBody": 'if new_strategy_id == "route_transition_graph_v2":\n    search_paths = []\n'},
            root=root,
        )
        assert corrected == {"branchBody": body}
        assert corrected_edits == output
        assert len(correction_calls) == 1
    finally:
        mod._request_corrected_plan = original_correction

    for bad_body in ("pass\n", "new_strategy_id = 'route_transition_graph_v3'\n", "if :(\n"):
        try:
            mod._model_edits({"branchBody": bad_body}, payload, root=root)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe or no-op generated executor body accepted")
    bad_root = root / "scripts/adaptive_runtime/runtime_repair.py"
    bad_root.write_text(fixtures["scripts/adaptive_runtime/runtime_repair.py"].replace(
        'elif new_strategy_id == "route_peer_transition_replay_v1":\n',
        ''
    ), encoding="utf-8")
    try:
        mod._model_edits({"branchBody": body}, payload, root=root)
    except ValueError as exc:
        assert "subsequent runtime sibling missing" in str(exc), exc
    else:
        raise AssertionError("new strategy inserted without distinct sibling anchor")

# A repeated textual find is not automatically a model failure when Brain can
# bind it to the exact focused snippet that was supplied to the model. The
# resolver must widen unchanged real source context until the anchor is unique.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-anchor-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    source = (
        "def unrelated():\n"
        "    VALUE = 1\n"
        "    return VALUE\n\n"
        "def target_strategy():\n"
        "    MARKER = 'route graph execution'\n"
        "    VALUE = 1\n"
        "    return VALUE\n"
    )
    target.write_text(source, encoding="utf-8")
    focused = (
        "def target_strategy():\n"
        "    MARKER = 'route graph execution'\n"
        "    VALUE = 1\n"
        "    return VALUE\n"
    )
    raw = [{
        "operation": "replace",
        "path": "scripts/brain_meta_learning.py",
        "find": "VALUE = 1",
        "replace": "VALUE = 2",
    }]
    resolved = mod._resolve_non_unique_replace_edits(
        raw,
        {"sources": {"scripts/brain_meta_learning.py": focused}},
        patterns,
        root=root,
    )
    assert resolved[0]["find"] != "VALUE = 1"
    assert source.count(resolved[0]["find"]) == 1
    mod.validate_edits(resolved, patterns, root=root)
    mod.apply_edits(resolved, root=root)
    changed = target.read_text(encoding="utf-8")
    assert changed.count("VALUE = 1") == 1
    assert changed.count("VALUE = 2") == 1
    assert "def unrelated():\n    VALUE = 1" in changed
    assert "def target_strategy():" in changed

# FORCE 37646660891 failed because the model's replace text occurred more than
# once inside the exact runtime_repair.py focus snippet. When the blueprint's
# evolved strategy id uniquely identifies one occurrence, Brain must bind that
# occurrence instead of burning corrective turns on the same ambiguous find.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-runtime-anchor-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "adaptive_runtime" / "runtime_repair.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    source = (
        "def runtime_strategy():\n"
        "    handler = build_transition()\n"
        "    unrelated_a = 1\n"
        "    unrelated_b = 2\n"
        "    unrelated_c = 3\n"
        "    route_transition_graph_v1 = legacy_profile\n"
        "    handler = build_transition()\n"
        "    return handler\n"
    )
    target.write_text(source, encoding="utf-8")
    raw = [{
        "operation": "replace",
        "path": "scripts/adaptive_runtime/runtime_repair.py",
        "find": "handler = build_transition()",
        "replace": "handler = build_transition_v2()",
    }]
    runtime_patterns = patterns + ["scripts/adaptive_runtime/runtime_repair.py"]
    resolved = mod._resolve_non_unique_replace_edits(
        raw,
        {
            "blueprint": {
                "strategyId": "route_transition_graph_v2",
                "evolvesFromStrategyId": "route_transition_graph_v1",
            },
            "sources": {
                "scripts/adaptive_runtime/runtime_repair.py": source,
            },
        },
        runtime_patterns,
        root=root,
    )
    assert resolved[0]["find"] != "handler = build_transition()", resolved
    assert source.count(resolved[0]["find"]) == 1, resolved
    mod.validate_edits(resolved, runtime_patterns, root=root)
    mod.apply_edits(resolved, root=root)
    changed = target.read_text(encoding="utf-8")
    assert changed.count("handler = build_transition()") == 1
    assert changed.count("handler = build_transition_v2()") == 1
    assert (
        "route_transition_graph_v1 = legacy_profile\n"
        "    handler = build_transition_v2()"
    ) in changed

# The real FORCE source context can be truncated during corrective turns. The
# resolver must still bind a repeated find to the exact prior strategy block in
# the full file, but only when that block contains the find exactly once.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-runtime-block-fallback-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "adaptive_runtime" / "runtime_repair.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    source = (
        "def choose(new_strategy_id):\n"
        "    if new_strategy_id == \"positive_program_v1\":\n"
        "        direct_paths = build_paths()\n"
        "        return direct_paths\n"
        "    elif new_strategy_id == \"route_transition_graph_v1\":\n"
        "        direct_paths = build_paths()\n"
        "        request_recipes = build_recipes()\n"
        "        return direct_paths\n"
        "    elif new_strategy_id == \"route_peer_transition_replay_v1\":\n"
        "        direct_paths = build_paths()\n"
        "        return direct_paths\n"
    )
    target.write_text(source, encoding="utf-8")
    raw = [{
        "operation": "replace",
        "path": "scripts/adaptive_runtime/runtime_repair.py",
        "find": "direct_paths = build_paths()",
        "replace": "direct_paths = build_paths_v2()",
    }]
    resolved = mod._resolve_non_unique_replace_edits(
        raw,
        {
            "blueprint": {
                "strategyId": "route_transition_graph_v2",
                "evolvesFromStrategyId": "route_transition_graph_v1",
            },
            # Simulates a compact corrective payload that no longer contains
            # the target branch at all.
            "sources": {
                "scripts/adaptive_runtime/runtime_repair.py":
                    "def choose(new_strategy_id):\n"
                    "    if new_strategy_id == \"positive_program_v1\":\n"
            },
        },
        runtime_patterns,
        root=root,
    )
    assert resolved[0]["find"] != "direct_paths = build_paths()", resolved
    assert source.count(resolved[0]["find"]) == 1, resolved
    mod.validate_edits(resolved, runtime_patterns, root=root)
    mod.apply_edits(resolved, root=root)
    changed = target.read_text(encoding="utf-8")
    assert changed.count("direct_paths = build_paths()") == 2
    assert changed.count("direct_paths = build_paths_v2()") == 1
    assert (
        'elif new_strategy_id == "route_transition_graph_v1":\n'
        "        direct_paths = build_paths_v2()"
    ) in changed

# FORCE 37680228320 reached a different repeated-find family in the Python
# Repair registry. The full-file fallback must bind generic repeated text to the
# uniquely nearest parent strategy entry, not only to runtime if/elif blocks.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-registry-fallback-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_repair_runtime.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    source = (
        "POST_EXHAUSTION_STRATEGY_PROFILES = {\n"
        '    "provider_positive_program_replay_v1",\n'
        '    "route_transition_graph_v1",\n'
        '    "route_peer_transition_replay_v1",\n'
        "}\n\n"
        "OTHER = {\n"
        '    "provider_positive_program_replay_v1",\n'
        '    "route_peer_transition_replay_v1",\n'
        "}\n"
    )
    target.write_text(source, encoding="utf-8")
    registry_patterns = patterns + ["scripts/brain_repair_runtime.py"]
    raw = [{
        "operation": "replace",
        "path": "scripts/brain_repair_runtime.py",
        "find": '    "route_peer_transition_replay_v1",',
        "replace": (
            '    "route_transition_graph_v2",\n'
            '    "route_peer_transition_replay_v1",'
        ),
    }]
    resolved = mod._resolve_non_unique_replace_edits(
        raw,
        {
            "blueprint": {
                "strategyId": "route_transition_graph_v2",
                "evolvesFromStrategyId": "route_transition_graph_v1",
            },
            # Simulate compact context that misses the registry target entirely.
            "sources": {
                "scripts/brain_repair_runtime.py": "POST_EXHAUSTION_STRATEGY_PROFILES = {\n"
            },
        },
        registry_patterns,
        root=root,
    )
    assert resolved[0]["find"] != raw[0]["find"], resolved
    assert source.count(resolved[0]["find"]) == 1, resolved
    mod.validate_edits(resolved, registry_patterns, root=root)
    mod.apply_edits(resolved, root=root)
    changed = target.read_text(encoding="utf-8")
    assert (
        '"route_transition_graph_v1",\n'
        '    "route_transition_graph_v2",\n'
        '    "route_peer_transition_replay_v1",'
    ) in changed
    assert changed.count('"route_transition_graph_v2"') == 1

# Corrective rounds may receive candidate bytes that no longer occur in the
# rollback baseline. The resolver must use materializedBaselineSources to bind
# a repeated find to the exact location that was rejected.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-anchor-baseline-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    source = (
        "def unrelated():\n"
        "    VALUE = 1\n"
        "    return VALUE\n\n"
        "def target_strategy():\n"
        "    MARKER = 'moviebox-category-gap'\n"
        "    VALUE = 1\n"
        "    return VALUE\n"
    )
    target.write_text(source, encoding="utf-8")
    baseline_focus = (
        "def target_strategy():\n"
        "    MARKER = 'moviebox-category-gap'\n"
        "    VALUE = 1\n"
        "    return VALUE\n"
    )
    rejected_focus = baseline_focus.replace("VALUE = 1", "VALUE = 9")
    raw = [{
        "operation": "replace",
        "path": "scripts/brain_meta_learning.py",
        "find": "VALUE = 1",
        "replace": "VALUE = 2",
    }]
    resolved = mod._resolve_non_unique_replace_edits(
        raw,
        {
            "sources": {"scripts/brain_meta_learning.py": "VALUE = 1\n"},
            "materializedFailureSources": {
                "scripts/brain_meta_learning.py": rejected_focus,
            },
            "materializedBaselineSources": {
                "scripts/brain_meta_learning.py": baseline_focus,
            },
        },
        patterns,
        root=root,
    )
    assert resolved[0]["find"] != "VALUE = 1", resolved
    assert source.count(resolved[0]["find"]) == 1, resolved
    mod.validate_edits(resolved, patterns, root=root)

# Failure context must be centered on changed bytes rather than truncating the
# start of a large architecture file.
before = ("HEADER = 0\n" * 400) + "TARGET = 1\n" + ("TAIL = 0\n" * 400)
after = before.replace("TARGET = 1", "TARGET = 2")
after_ctx = mod._materialized_failure_snippet(before, after, 320)
before_ctx = mod._materialized_failure_snippet(after, before, 320)
assert "TARGET = 2" in after_ctx and "TARGET = 1" not in after_ctx
assert "TARGET = 1" in before_ctx and "TARGET = 2" not in before_ctx
assert not after_ctx.startswith("HEADER = 0\n" * 10)

# If the focused snippet itself does not uniquely identify one repeated find,
# the resolver must leave the edit untouched so normal validation fails closed.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-anchor-ambiguous-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    source = "VALUE = 1\nVALUE = 1\n"
    target.write_text(source, encoding="utf-8")
    raw = [{
        "operation": "replace",
        "path": "scripts/brain_meta_learning.py",
        "find": "VALUE = 1",
        "replace": "VALUE = 2",
    }]
    unresolved = mod._resolve_non_unique_replace_edits(
        raw,
        {"sources": {"scripts/brain_meta_learning.py": source}},
        patterns,
        root=root,
    )
    assert unresolved[0]["find"] == "VALUE = 1"
    try:
        mod.validate_edits(unresolved, patterns, root=root)
    except ValueError as exc:
        assert "exactly once" in str(exc)
    else:
        raise AssertionError("ambiguous architecture FORCE anchor unexpectedly accepted")

# A schema-valid plan can still hallucinate a non-allowlisted repository path.
# FORCE must ask the model once to correct its own plan with the exact validation
# error and allowedPaths, then fail closed if the correction is still invalid.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-correct-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")
    original_call_model = mod.call_model
    original_request = mod._model_request
    correction_calls = []
    try:
        def fake_plan(endpoint, model, payload):
            return {
                "edits": [{
                    "operation": "replace",
                    "path": "engine_v2/scripts/brain_meta_learning.py",
                    "find": "VALUE = 1",
                    "replace": "VALUE = 2",
                }]
            }

        def fake_correction(endpoint, model, payload, *, max_tokens, timeout, compact=False):
            correction_calls.append((payload, max_tokens, timeout))
            assert "outside allowlist" in payload["validationError"]
            assert "scripts/brain_meta_learning.py" in payload["allowedPaths"]
            assert payload["exactAllowedPaths"] == ["scripts/brain_meta_learning.py"]
            assert payload["correctionContract"]["pathMustBeOneOfExactAllowedPaths"] is True
            assert payload["correctionContract"]["doNotInventPaths"] is True
            assert payload["correctionContract"]["doNotRelocatePaths"] is True
            assert payload["correctionContract"]["preferSingleSmallReplace"] is True
            assert "path" not in payload["rejectedEditIntent"][0]
            if len(correction_calls) == 1:
                return {
                    "choices": [{
                        "message": {
                            "content": '{"edits":[{"operation":"replace","path":"scripts/brain_meta_learning.py","find":"VALUE = 1","replace":"VALUE = 2"'
                        }
                    }]
                }
            import json
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "edits": [{
                                "operation": "replace",
                                "path": "scripts/brain_meta_learning.py",
                                "find": "VALUE = 1",
                                "replace": "VALUE = 2",
                            }]
                        })
                    }
                }]
            }

        mod.call_model = fake_plan
        mod._model_request = fake_correction
        _, corrected_edits = mod.validated_model_plan(
            "http://127.0.0.1:8080",
            "demo",
            {
                "blueprint": {"strategyId": "demo"},
                "allowedPaths": patterns,
                "contract": {"requireExecutableDiff": True},
                "sources": {"scripts/brain_meta_learning.py": "VALUE = 1\n"},
                "architectureLayers": [],
            },
            patterns,
            root=root,
        )
        assert corrected_edits[0]["path"] == "scripts/brain_meta_learning.py"
        assert len(correction_calls) == 2
        assert correction_calls[0][1:] == (
            mod.VALIDATION_RETRY_MODEL_TOKENS,
            mod.VALIDATION_RETRY_TIMEOUT_SECONDS,
        )
        assert correction_calls[1][1:] == (
            mod.VALIDATION_FORMAT_RETRY_MODEL_TOKENS,
            mod.VALIDATION_FORMAT_RETRY_TIMEOUT_SECONDS,
        )
    finally:
        mod.call_model = original_call_model
        mod._model_request = original_request


# A first corrective plan can still violate operation/path semantics. This
# reproduces FORCE 37525886424: the original replace was invalid, then Qwen
# tried to create an allowlisted Brain file that already existed. Brain must
# feed that exact second validation error back into one more bounded correction
# round instead of terminating the whole FORCE run.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-edit-retry-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")
    original_call_model = mod.call_model
    original_request = mod._model_request
    edit_corrections = []
    try:
        mod.call_model = lambda endpoint, model, payload: {
            "edits": [{
                "operation": "replace",
                "path": "scripts/brain_meta_learning.py",
                "find": "VALUE = 9",
                "replace": "VALUE = 2",
            }]
        }

        def repair_invalid_edit_plan(endpoint, model, payload, *, max_tokens, timeout, compact=False):
            edit_corrections.append(payload)
            import json
            if len(edit_corrections) == 1:
                assert "replace find must occur exactly once" in payload["validationError"]
                assert payload["existingAllowedPaths"] == ["scripts/brain_meta_learning.py"]
                assert payload["newAllowedPaths"] == []
                assert payload["correctionContract"]["existingPathsMustUseReplace"] is True
                assert payload["correctionContract"]["editValidationCorrectionRound"] == 1
                return {
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "edits": [{
                                    "operation": "create",
                                    "path": "scripts/brain_meta_learning.py",
                                    "content": "VALUE = 2\n",
                                }]
                            })
                        }
                    }]
                }
            assert "create target already exists" in payload["validationError"]
            assert payload["correctionContract"]["editValidationCorrectionRound"] == 2
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "edits": [{
                                "operation": "replace",
                                "path": "scripts/brain_meta_learning.py",
                                "find": "VALUE = 1",
                                "replace": "VALUE = 2",
                            }]
                        })
                    }
                }]
            }

        mod._model_request = repair_invalid_edit_plan
        _, corrected_edits = mod.validated_model_plan(
            "http://127.0.0.1:8080",
            "demo",
            {
                "blueprint": {"strategyId": "demo"},
                "allowedPaths": patterns,
                "contract": {"requireExecutableDiff": True},
                "sources": {"scripts/brain_meta_learning.py": "VALUE = 1\n"},
                "architectureLayers": [],
            },
            patterns,
            root=root,
        )
        assert corrected_edits[0]["operation"] == "replace"
        assert corrected_edits[0]["replace"] == "VALUE = 2"
        assert len(edit_corrections) == mod.EDIT_VALIDATION_CORRECTION_ROUNDS
        assert target.read_text(encoding="utf-8") == "VALUE = 1\n"
    finally:
        mod.call_model = original_call_model
        mod._model_request = original_request


# A structurally valid model edit can still produce invalid source. FORCE must
# validate the materialized bytes transactionally, restore the baseline on
# failure, and let Qwen correct its own edit using the exact parser error.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-syntax-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")
    original_call_model = mod.call_model
    original_request = mod._model_request
    correction_calls = []
    try:
        def fake_syntax_bad_plan(endpoint, model, payload):
            return {
                "edits": [{
                    "operation": "replace",
                    "path": "scripts/brain_meta_learning.py",
                    "find": "VALUE = 1",
                    "replace": "    VALUE = 2",
                }]
            }

        def fake_syntax_correction(endpoint, model, payload, *, max_tokens, timeout, compact=False):
            correction_calls.append(payload)
            assert "materialized syntax validation failed" in payload["validationError"]
            assert payload["exactAllowedPaths"] == ["scripts/brain_meta_learning.py"]
            assert "path" not in payload["rejectedEditIntent"][0]
            assert payload["correctionReason"] == "materialized-syntax-validation"
            assert payload["correctionContract"]["syntaxRepairOnly"] is True
            assert payload["correctionContract"]["mustPassMaterializedSyntaxValidation"] is True
            assert payload["correctionContract"]["useMaterializedBaselineSources"] is True
            assert payload["correctionContract"]["materializedCorrectionRound"] == 1
            assert payload["materializedFailureSources"]["scripts/brain_meta_learning.py"].startswith("    VALUE = 2")
            assert payload["materializedBaselineSources"]["scripts/brain_meta_learning.py"].startswith("VALUE = 1")
            import json
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "edits": [{
                                "operation": "replace",
                                "path": "scripts/brain_meta_learning.py",
                                "find": "VALUE = 1",
                                "replace": "VALUE = 2",
                            }]
                        })
                    }
                }]
            }

        mod.call_model = fake_syntax_bad_plan
        mod._model_request = fake_syntax_correction
        _, corrected_edits = mod.validated_model_plan(
            "http://127.0.0.1:8080",
            "demo",
            {
                "blueprint": {"strategyId": "demo"},
                "allowedPaths": patterns,
                "contract": {"requireExecutableDiff": True},
                "sources": {"scripts/brain_meta_learning.py": "VALUE = 1\n"},
                "architectureLayers": [],
            },
            patterns,
            root=root,
        )
        assert corrected_edits[0]["replace"] == "VALUE = 2"
        assert len(correction_calls) == 1
        # Validation is a dry-run: invalid and corrected candidate bytes never
        # leak into the checkout before main() performs the final apply.
        assert target.read_text(encoding="utf-8") == "VALUE = 1\n"
        mod.apply_edits(corrected_edits, root=root)
        mod.validate_changed_syntax(["scripts/brain_meta_learning.py"], root=root)
        assert target.read_text(encoding="utf-8") == "VALUE = 2\n"
    finally:
        mod.call_model = original_call_model
        mod._model_request = original_request



# A syntax-valid architecture edit can still violate the Brain contracts. The
# materializer must catch that inside its transactional dry-run so the same run
# can feed the exact contract failure back to Qwen instead of applying first and
# failing only in the workflow afterwards.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-contract-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")
    contract = root / "tests" / "brain_meta_learning_gap_synthesis_test.py"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        "from pathlib import Path\n"
        "source=Path('scripts/brain_meta_learning.py').read_text()\n"
        "assert 'DUPLICATE' not in source, source\n",
        encoding="utf-8",
    )
    original_call_model = mod.call_model
    original_request = mod._model_request
    correction_calls = []
    try:
        mod.call_model = lambda endpoint, model, payload: {
            "edits": [{
                "operation": "replace",
                "path": "scripts/brain_meta_learning.py",
                "find": "VALUE = 1",
                "replace": "VALUE = 1\nDUPLICATE = True",
            }]
        }

        def fix_contract(endpoint, model, payload, *, max_tokens, timeout, compact=False):
            correction_calls.append(payload)
            assert "materialized contract validation failed" in payload["validationError"]
            assert payload["correctionReason"] == "materialized-source-validation"
            assert payload["correctionContract"]["mustPassMaterializedContractValidation"] is True
            import json
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "edits": [{
                                "operation": "replace",
                                "path": "scripts/brain_meta_learning.py",
                                # Correct relative to the rejected candidate,
                                # not the restored baseline. This is the exact
                                # failure shape observed in FORCE 37520931361.
                                "find": "DUPLICATE = True",
                                "replace": "FIXED = True",
                            }]
                        })
                    }
                }]
            }

        mod._model_request = fix_contract
        _, corrected_edits = mod.validated_model_plan(
            "http://127.0.0.1:8080",
            "demo",
            {
                "blueprint": {"strategyId": "demo"},
                "allowedPaths": patterns,
                "contract": {"requireExecutableDiff": True},
                "sources": {"scripts/brain_meta_learning.py": "VALUE = 1\n"},
                "architectureLayers": [],
            },
            patterns,
            root=root,
        )
        assert "FIXED = True" in corrected_edits[0]["replace"]
        assert "DUPLICATE = True" not in corrected_edits[0]["replace"]
        assert len(correction_calls) == 1
        assert target.read_text(encoding="utf-8") == "VALUE = 1\n"
        mod.apply_edits(corrected_edits, root=root)
        assert target.read_text(encoding="utf-8") == "VALUE = 1\nFIXED = True\n"
    finally:
        mod.call_model = original_call_model
        mod._model_request = original_request

# A second syntactically invalid response fails closed and still restores the
# exact original bytes instead of leaving a broken architecture file behind.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-syntax-fail-") as tmp:
    root = Path(tmp)
    target = root / "scripts" / "brain_meta_learning.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")
    original_call_model = mod.call_model
    original_request = mod._model_request
    invalid_correction_calls = []
    try:
        mod.call_model = lambda endpoint, model, payload: {
            "edits": [{
                "operation": "replace",
                "path": "scripts/brain_meta_learning.py",
                "find": "VALUE = 1",
                "replace": "    VALUE = 2",
            }]
        }

        def still_invalid(endpoint, model, payload, *, max_tokens, timeout, compact=False):
            invalid_correction_calls.append(payload)
            import json
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "edits": [{
                                "operation": "replace",
                                "path": "scripts/brain_meta_learning.py",
                                "find": "VALUE = 1",
                                "replace": "    VALUE = 3",
                            }]
                        })
                    }
                }]
            }

        mod._model_request = still_invalid
        try:
            mod.validated_model_plan(
                "http://127.0.0.1:8080",
                "demo",
                {
                    "blueprint": {"strategyId": "demo"},
                    "allowedPaths": patterns,
                    "contract": {"requireExecutableDiff": True},
                    "sources": {"scripts/brain_meta_learning.py": "VALUE = 1\n"},
                    "architectureLayers": [],
                },
                patterns,
                root=root,
            )
        except ValueError as exc:
            assert "materialized syntax validation failed" in str(exc)
        else:
            raise AssertionError("second syntax-invalid FORCE edit unexpectedly accepted")
        assert target.read_text(encoding="utf-8") == "VALUE = 1\n"
        assert len(invalid_correction_calls) == mod.MATERIALIZED_CORRECTION_ROUNDS
        assert [p["correctionContract"]["materializedCorrectionRound"] for p in invalid_correction_calls] == list(range(1, mod.MATERIALIZED_CORRECTION_ROUNDS + 1))
        assert invalid_correction_calls[1]["materializedFailureSources"]["scripts/brain_meta_learning.py"].startswith("    VALUE = 3")
        assert invalid_correction_calls[1]["materializedBaselineSources"]["scripts/brain_meta_learning.py"].startswith("VALUE = 1")
    finally:
        mod.call_model = original_call_model
        mod._model_request = original_request

schema = mod._response_format([
    "scripts/brain_meta_learning.py",
    "scripts/brain_repair_runtime.py",
])
path_schema = schema["schema"]["properties"]["edits"]["items"]["properties"]["path"]
assert path_schema["enum"] == [
    "scripts/brain_meta_learning.py",
    "scripts/brain_repair_runtime.py",
]

minimal = mod._minimal_payload({
    "blueprint": {"strategyId": "demo"},
    "architectureLayers": [{"id": "unused"}],
    "allowedPaths": ["scripts/brain_layers/*"],
    "sources": {"a": "x" * 3000, "b": "y" * 3000},
    "contract": {"requireExecutableDiff": True},
})
assert minimal["blueprint"]["strategyId"] == "demo"
assert "architectureLayers" not in minimal
assert sum(len(v) for v in minimal["sources"].values()) <= mod.MINIMAL_SOURCE_CONTEXT

# Materialized corrections must stay on the file that actually failed. Unrelated
# architecture source snippets are useful for planning, but must not remain
# alternate edit targets once transactional validation has rejected one path.
with tempfile.TemporaryDirectory(prefix="brain-arch-force-restrict-") as tmp:
    root = Path(tmp)
    for name in ("brain_meta_learning.py", "brain_repair_runtime.py"):
        target = root / "scripts" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("VALUE = 1\n", encoding="utf-8")
    retry = mod._validation_retry_payload(
        {
            "blueprint": {"strategyId": "demo"},
            "allowedPaths": patterns,
            "contract": {"requireExecutableDiff": True},
            "sources": {
                "scripts/brain_meta_learning.py": "VALUE = 1\n",
                "scripts/brain_repair_runtime.py": "VALUE = 1\n",
            },
        },
        ValueError("materialized syntax validation failed"),
        [{
            "operation": "replace",
            "path": "scripts/brain_meta_learning.py",
            "find": "VALUE = 1",
            "replace": "VALUE = 2",
        }],
        extra_exact_paths=["scripts/brain_meta_learning.py"],
        restrict_to_extra_paths=True,
        root=root,
    )
    assert retry["exactAllowedPaths"] == ["scripts/brain_meta_learning.py"]
    assert list(retry["sources"]) == ["scripts/brain_meta_learning.py"]
    assert retry["existingAllowedPaths"] == ["scripts/brain_meta_learning.py"]


# The 7B LLM may emit only the genuinely new runtime executor. Registry and
# planner boilerplate are deterministically wired by Brain, NOT provider edits.
# This unlocks realistic one-shot code generation within the bounded token
# budget while retaining three-surface compilation/validation and rollback.
with tempfile.TemporaryDirectory(prefix="brain-arch-runtime-only-autowire-") as tmp:
    root = Path(tmp)
    fixtures = {
        "scripts/brain_repair_runtime.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v2",\n'
            '}\n'
        ),
        "engine_v2/scripts/plan-repairs.mjs": (
            'const POST_EXHAUSTION_STRATEGIES = {\n'
            '  route_proven_gap: [\n'
            '    { profile: "html_class_token_exact_v1", method: "html-class" },\n'
            '    { profile: "route_transition_graph_v2", method: "same-provider-salvage" },\n'
            '  ],\n'
            '};\n'
        ),
        "scripts/adaptive_runtime/runtime_repair.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v2",\n'
            '}\n'
            'if new_strategy_id == "route_transition_graph_v2":\n'
            '    executor = "retained-graph"\n'
        ),
    }
    for path, content in fixtures.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    blueprint = {
        "strategyId": "route_transition_graph_v3",
        "evolvesFromStrategyId": "route_transition_graph_v2",
        "repairScope": "route-to-terminal",
        "requiresNewExecutableRepairProfile": True,
    }
    runtime_only = [{
        "operation": "replace",
        "path": "scripts/adaptive_runtime/runtime_repair.py",
        "find": '    executor = "retained-graph"\n',
        "replace": (
            '    executor = "retained-graph"\n'
            'elif new_strategy_id == "route_transition_graph_v3":\n'
            '    executor = "fresh-observed-transition"\n'
        ),
    }]
    complete = mod.complete_evolved_profile_wiring(runtime_only, blueprint, root=root)
    assert len(complete) == 3, complete
    assert {row["path"] for row in complete} == set(mod.NEW_REPAIR_PROFILE_SURFACES), complete
    assert 'route_transition_graph_v3' in next(
        row["replace"] for row in complete
        if row["path"] == "engine_v2/scripts/plan-repairs.mjs"
    )
    mod.validate_edits(complete, list(mod.NEW_REPAIR_PROFILE_SURFACES), root=root)
    original_validate = mod.validate_blueprint_implementation
    registration_observed = []
    try:
        def verify_runtime_registration(changed, blueprint, *, root, baseline_sources=None):
            runtime_body = (root / "scripts/adaptive_runtime/runtime_repair.py").read_text(encoding="utf-8")
            header = runtime_body.split("POST_EXHAUSTION_STRATEGY_PROFILES = {", 1)[1].split("\n}", 1)[0]
            assert '    "route_transition_graph_v3",' in header, "generated strategy not selectable"
            assert header.count('    "route_transition_graph_v3",') == 1, "duplicate runtime registration"
            assert '    "route_transition_graph_v2",' in header, "exhausted parent registration lost"
            registration_observed.append(True)
            return original_validate(changed, blueprint, root=root, baseline_sources=baseline_sources)
        mod.validate_blueprint_implementation = verify_runtime_registration
        changed = mod.validate_materialized_edits(
            complete, root=root, blueprint=blueprint,
        )
    finally:
        mod.validate_blueprint_implementation = original_validate
    assert registration_observed, "fourth runtime selection gate was not exercised"
    assert set(changed) == set(mod.NEW_REPAIR_PROFILE_SURFACES), changed
    assert all((root / path).read_text(encoding="utf-8") == content for path, content in fixtures.items())
    # The Brain cannot autowire a made-up family and must never substitute a
    # generic source change for a fully wired, executable strategy.
    try:
        mod.complete_evolved_profile_wiring(
            runtime_only, {**blueprint, "repairScope": "unproven-local-guess"},
            root=root,
        )
    except ValueError as exc:
        assert "unknown planner repair scope" in str(exc), exc
    else:
        raise AssertionError("unknown repair family unexpectedly scaffolded")

# A one-executor FORCE workflow must never instruct the 7B advisor to
# provide three edits and one edit simultaneously (real model loop failure).
materializer_prompt = SCRIPT.read_text(encoding="utf-8")
assert "Return exactly 3 replace edits" not in materializer_prompt
assert "Return JSON ONLY with exactly one string field branchBody" in materializer_prompt
assert "Brain will insert the code in its own distinct sibling guard" in materializer_prompt
assert mod._branch_body_response_format()["schema"]["required"] == ["branchBody"]

print("Brain architecture FORCE materializer tests passed")
