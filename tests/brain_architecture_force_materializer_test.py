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
assert mod.MAX_MODEL_TOKENS <= 800
assert mod.MODEL_TIMEOUT_SECONDS == 180
assert mod.RETRY_MODEL_TOKENS == 500

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
    assert calls[0][:3] == (mod.MAX_MODEL_TOKENS, mod.MODEL_TIMEOUT_SECONDS, False)
    assert calls[1][:3] == (mod.RETRY_MODEL_TOKENS, 120, True)
    assert calls[1][3] <= mod.RETRY_SOURCE_CONTEXT
finally:
    mod._model_request = original_request

print("Brain architecture FORCE materializer tests passed")
