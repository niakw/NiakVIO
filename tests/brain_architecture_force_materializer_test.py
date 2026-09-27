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
assert mod.MAX_MODEL_TOKENS <= 512
assert mod.MODEL_TIMEOUT_SECONDS <= 100
assert mod.RETRY_MODEL_TOKENS <= 640
assert mod.RETRY_MODEL_TIMEOUT_SECONDS <= 120
assert mod.VALIDATION_RETRY_MODEL_TOKENS <= 512
assert mod.VALIDATION_RETRY_TIMEOUT_SECONDS <= 100
assert mod.RETRY_SOURCE_CONTEXT <= 3600
assert mod.MINIMAL_SOURCE_CONTEXT <= 1800
assert mod.MATERIALIZED_CORRECTION_ROUNDS == 2
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
    assert mod.MODEL_TIMEOUT_SECONDS <= 100
    assert mod.RETRY_MODEL_TOKENS <= 640
    assert mod.RETRY_MODEL_TIMEOUT_SECONDS <= 120
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
            assert payload["correctionReason"] == "materialized-source-validation"
            assert payload["correctionContract"]["mustPassMaterializedSyntaxValidation"] is True
            assert payload["correctionContract"]["materializedCorrectionRound"] == 1
            assert payload["materializedFailureSources"]["scripts/brain_meta_learning.py"].startswith("    VALUE = 2")
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
        assert [p["correctionContract"]["materializedCorrectionRound"] for p in invalid_correction_calls] == [1, 2]
        assert invalid_correction_calls[1]["materializedFailureSources"]["scripts/brain_meta_learning.py"].startswith("    VALUE = 3")
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

print("Brain architecture FORCE materializer tests passed")
