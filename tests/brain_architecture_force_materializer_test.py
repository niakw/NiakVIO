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

print("Brain architecture FORCE materializer tests passed")
