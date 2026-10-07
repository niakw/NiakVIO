#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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
            "find": 'new_strategy_id == "route_transition_graph_v1"',
            "replace": 'new_strategy_id in {"route_transition_graph_v1", "route_transition_graph_v2"}',
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
assert set(new_profile_compact["sources"]) == set(mod.NEW_REPAIR_PROFILE_SURFACES)
assert new_profile_compact["exactAllowedPaths"] == list(mod.NEW_REPAIR_PROFILE_SURFACES)
assert new_profile_compact["existingAllowedPaths"] == list(mod.NEW_REPAIR_PROFILE_SURFACES)
assert all(
    len(text) <= mod.NEW_PROFILE_SOURCE_CONTEXT_PER_SURFACE
    for text in new_profile_compact["sources"].values()
)

profile_calls = []
original_request = mod._model_request
try:
    def fake_profile_request(endpoint, model, payload, *, max_tokens, timeout, compact=False):
        profile_calls.append((payload, max_tokens, timeout, compact))
        assert set(payload["sources"]) == set(mod.NEW_REPAIR_PROFILE_SURFACES)
        assert payload["exactAllowedPaths"] == list(mod.NEW_REPAIR_PROFILE_SURFACES)
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
                            for path in mod.NEW_REPAIR_PROFILE_SURFACES
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
    assert len(profile_result["edits"]) == 3
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
assert set(profile_retry["sources"]) == set(mod.NEW_REPAIR_PROFILE_SURFACES)
assert profile_retry["correctionContract"]["preferSingleSmallReplace"] is False
assert profile_retry["correctionContract"]["mustPreserveEvolvesFromStrategy"] is True
assert profile_retry["correctionContract"]["mustUseAllRequiredRepairProfileSurfaces"] is True
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

print("Brain architecture FORCE materializer tests passed")
