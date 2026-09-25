#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/apply_brain_llm_force_mutations.py"

spec = importlib.util.spec_from_file_location("force_mutations", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "automation").mkdir(parents=True)
    (root / "scripts/provider_patches").mkdir(parents=True)

    patch = root / "scripts/provider_patches/demo_runtime_v1.py"
    patch.write_text("def apply(value):\n    return value\n", encoding="utf-8")

    overrides = {
        "schema_version": 7,
        "provider_patches": {
            "demo": {
                "capability": "html_scraper",
                "learned_routes": ["/old"],
                "provider_lego_scripts": [
                    "scripts/provider_patches/demo_runtime_v1.py"
                ],
            },
            "healthy": {
                "capability": "html_scraper",
                "learned_routes": ["/healthy"],
            },
        },
    }
    (root / "provider-overrides.json").write_text(
        json.dumps(overrides, indent=2) + "\n",
        encoding="utf-8",
    )

    mod.ROOT = root
    mod.source_drift = lambda *_args, **_kwargs: ([], set())

    mutations = [
        {
            "scope": "provider_data",
            "operation": "append",
            "path": "learned_routes",
            "value": "/new",
        }
    ]
    payload = {
        "schemaVersion": 1,
        "sourceNiakvioSha": "a" * 40,
        "brainLlmSha": "b" * 40,
        "sandboxMutationAuthority": True,
        "publicationAuthority": False,
        "proofAuthority": False,
        "privateContentRetained": False,
        "rows": [
            {
                "providerId": "demo",
                "mutations": mutations,
                "mutationFingerprint": mod._fingerprint(mutations),
            },
            {
                "providerId": "healthy",
                "mutations": mutations,
                "mutationFingerprint": mod._fingerprint(mutations),
            },
        ],
    }

    report = mod.apply_payload(
        payload,
        current_sha="c" * 40,
        selected={"demo"},
    )
    assert report["appliedProviders"] == ["demo"], report
    assert any(
        row["provider"] == "healthy"
        and row["reason"] == "outside-current-repair-scope"
        for row in report["skipped"]
    ), report
    updated = json.loads((root / "provider-overrides.json").read_text())
    assert updated["provider_patches"]["demo"]["learned_routes"] == ["/old", "/new"]
    assert updated["provider_patches"]["healthy"]["learned_routes"] == ["/healthy"]

    unsafe = {
        "scope": "provider_patch",
        "operation": "unified_diff",
        "path": "scripts/provider_patches/other_runtime_v1.py",
        "diff": (
            "--- a/scripts/provider_patches/other_runtime_v1.py\n"
            "+++ b/scripts/provider_patches/other_runtime_v1.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        ),
    }
    try:
        mod._apply_file_mutation(
            "demo",
            updated["provider_patches"]["demo"],
            unsafe,
        )
    except ValueError as exc:
        assert "not a registered Bloc" in str(exc)
    else:
        raise AssertionError("unregistered provider Bloc mutation was accepted")

    mod.source_drift = lambda *_args, **_kwargs: ([], {"demo"})
    unchanged = json.loads((root / "provider-overrides.json").read_text())
    report = mod.apply_payload(
        {
            **payload,
            "rows": [payload["rows"][0]],
        },
        current_sha="c" * 40,
        selected={"demo"},
    )
    assert report["appliedProviderCount"] == 0, report
    assert report["skipped"][0]["reason"] == "provider-drift-since-guidance"
    assert json.loads((root / "provider-overrides.json").read_text()) == unchanged

print("Brain LLM Force mutation bridge tests passed")
