#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_brain_repair_proposal.py"


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def load_script():
    spec = importlib.util.spec_from_file_location("brain_repair_proposal", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_script()
    committed, source = module.load_proposal_baseline(ROOT / "provider-overrides.json")
    expected = json.loads(subprocess.check_output(
        ["git", "show", "HEAD:provider-overrides.json"], cwd=ROOT, text=True
    ))
    assert source == "git-head"
    assert committed == expected

    with tempfile.TemporaryDirectory(prefix="niakvio-brain-proposal-") as tmp:
        root = Path(tmp)
        stage = root / "candidates.json"
        report = root / "repair-report.json"
        overrides = root / "provider-overrides.json"
        output = root / "provider-overrides.proposed.json"
        summary = root / "repair-proposal.json"

        write(overrides, {
            "schema_version": 7,
            "provider_patches": {
                "foo": {"profiles": []},
                "bar": {"profiles": []},
            },
            "patch_profiles": {"metadata_context_recovery": {"phase": "runtime"}},
        })
        write(stage, {
            "candidates": [
                {
                    "key": "gowaru:foo",
                    "canonical_id": "foo",
                    "local_patches": [{
                        "type": "patch_profile",
                        "profile": "adaptive_runtime_recovery",
                        "options": {
                            "provider_name": "Foo",
                            "base_url": "https://foo.invalid",
                            "types": ["movie"],
                            "search_paths": ["/?s={query}"],
                        },
                    }],
                },
                {
                    "key": "yoru:bar",
                    "canonical_id": "bar",
                    "local_patches": [],
                },
            ]
        })
        write(report, {
            "rounds": [{
                "round": 1,
                "attempts": [
                    {
                        "parent_key": "gowaru:foo",
                        "status": "generated",
                        "profile": "adaptive_runtime_recovery",
                        "repair_sha256": "foo-sha",
                    }
                ],
                "accepted": [
                    {
                        "parent_key": "gowaru:foo",
                        "profile": "",
                        "sha256": "foo-sha",
                        "status_before": "no_streams",
                        "status_after": "healthy",
                        "streams_playable_before": 0,
                        "streams_playable_after": 1,
                    },
                    {
                        "parent_key": "yoru:bar",
                        "profile": "metadata_context_recovery",
                        "sha256": "bar-sha",
                        "status_before": "runtime_error",
                        "status_after": "healthy",
                        "streams_playable_before": 0,
                        "streams_playable_after": 1,
                    },
                ],
            }]
        })

        subprocess.run([
            sys.executable, str(SCRIPT),
            "--stage", str(stage),
            "--repair-report", str(report),
            "--overrides", str(overrides),
            "--output", str(output),
            "--summary", str(summary),
        ], cwd=ROOT, check=True)

        proposed = json.loads(output.read_text(encoding="utf-8"))
        proposal = json.loads(summary.read_text(encoding="utf-8"))
        foo = proposed["provider_patches"]["foo"]
        bar = proposed["provider_patches"]["bar"]
        adaptive = "scripts/provider_patches/adaptive_runtime_recovery_v5.py"
        assert adaptive in foo["patch_scripts"]
        assert foo["patch_script_options"][adaptive]["provider_name"] == "Foo"
        assert bar["profiles"] == ["metadata_context_recovery"]
        assert proposal["baselineSource"] == "input-file"
        assert proposal["proposalCount"] == 2
        assert proposal["providers"] == ["bar", "foo"]
        assert proposal["policy"]["pullRequestOnly"] is True
        assert proposal["policy"]["requiresHumanMerge"] is True
        assert proposal["policy"]["publicationAllowed"] is False


if __name__ == "__main__":
    main()
