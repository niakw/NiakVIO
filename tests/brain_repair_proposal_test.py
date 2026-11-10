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
                "uhdmovies": {"profiles": []},
            },
            "patch_profiles": {"metadata_context_recovery": {"phase": "runtime"}},
            "runtime_repair": {
                "learned_skills": {
                    "search_gap:adaptive_runtime_recovery": {
                        "id": "search_gap:adaptive_runtime_recovery",
                        "failureClass": "search_gap",
                        "profile": "adaptive_runtime_recovery",
                        "actions": ["apply validated adaptive strategy"],
                        "capabilities": ["search", "routes"],
                        "providers": ["foo", "bar"],
                        "successCount": 2,
                        "failureCount": 0,
                        "validated": True,
                        "confidence": 1.0,
                        "maturity": "candidate",
                        "autoApply": False,
                        "lastValidatedMode": "learning",
                    }
                }
            },
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
                {
                    "key": "aio:uhdmovies",
                    "canonical_id": "uhdmovies",
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
                        "reason": "strict_playable_stream_improvement",
                        "durable_promotion_eligible": True,
                        "identity_strict_reason": "positive_content_identity_proof",
                    },
                    {
                        "parent_key": "yoru:bar",
                        "profile": "metadata_context_recovery",
                        "sha256": "bar-sha",
                        "status_before": "runtime_error",
                        "status_after": "healthy",
                        "streams_playable_before": 0,
                        "streams_playable_after": 1,
                        "reason": "strict_playable_stream_improvement",
                        "durable_promotion_eligible": True,
                        "identity_strict_reason": "positive_content_identity_proof",
                    },
                    {
                        "parent_key": "aio:uhdmovies",
                        "profile": "route_transition_graph_v6",
                        "status_before": "no_streams",
                        "status_after": "healthy",
                        "streams_playable_before": 0,
                        "streams_playable_after": 2,
                        "reason": "provisional_quick_runtime_improvement",
                        "durable_promotion_eligible": False,
                        "identity_strict_reason": "identity_gate:no_positive_content_identity_proof",
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
        assert proposed["provider_patches"]["uhdmovies"]["profiles"] == []
        assert any(row.get("providerId") == "uhdmovies"
                   and row.get("reason") == "quick_candidate_not_terminal_verified"
                   for row in proposal["skipped"]), proposal["skipped"]
        assert proposal["baselineSource"] == "input-file"
        assert proposal["proposalCount"] == 3
        assert proposal["providerProposalCount"] == 2
        assert proposal["learnedSkillProposalCount"] == 1
        assert proposal["providers"] == ["bar", "foo"]
        learned = proposed["runtime_repair"]["learned_skills"]["search_gap:adaptive_runtime_recovery"]
        assert learned["maturity"] == "candidate"
        assert learned["successCount"] == 2
        assert learned["providers"] == ["bar", "foo"]
        assert proposal["policy"]["pullRequestOnly"] is True
        assert proposal["policy"]["requiresHumanMerge"] is True
        assert proposal["policy"]["publicationAllowed"] is False


if __name__ == "__main__":
    main()
