#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_brain_architecture_proposal.py"
POLICY = ROOT / "engine_v2" / "config" / "brain-policy.json"
SELF = ROOT / "engine_v2" / "config" / "brain-self-evolution.json"
WORKFLOW = ROOT / ".github" / "workflows" / "brain-learning-lab.yml"

with tempfile.TemporaryDirectory(prefix="brain-self-arch-") as tmp:
    tmp = Path(tmp)
    learning = {
        "unresolvedFailureCounts": {"unknown_failure": 3},
        "experimentMemory": {
            "entries": [
                {"providerId": "demo", "profile": "p1", "successes": 0, "consecutiveFailures": 2},
                {"providerId": "demo", "profile": "p2", "successes": 0, "consecutiveFailures": 2},
                {"providerId": "demo", "profile": "p3", "successes": 0, "consecutiveFailures": 2},
            ]
        },
        "proposals": [],
    }
    lab = {
        "status": "partial_failure",
        "providerId": "demo",
        "clients": {
            "desktop": {
                "runtimeStreams": 60,
                "probedStreams": 40,
                "playableProbes": 30,
                "unplayableProbes": 10,
                "inconclusiveProbes": 0,
                "identityContradictions": 0,
                "probeCoverageComplete": False,
            }
        },
    }
    selection = {
        "provider": "demo",
        "status": "healthy",
        "needs_route_search": True,
    }

    paths = {}
    for name, value in {
        "learning.json": learning,
        "lab.json": lab,
        "selection.json": selection,
        "route.json": {},
        "fallback.json": {},
    }.items():
        path = tmp / name
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        paths[name] = path

    proposed = tmp / "policy.json"
    summary = tmp / "summary.json"
    markdown = tmp / "summary.md"

    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--learning-state", str(paths["learning.json"]),
            "--policy", str(POLICY),
            "--self-config", str(SELF),
            "--workflow", str(WORKFLOW),
            "--targeted-lab", str(paths["lab.json"]),
            "--target-selection", str(paths["selection.json"]),
            "--route-report", str(paths["route.json"]),
            "--route-fallback", str(paths["fallback.json"]),
            "--output-policy", str(proposed),
            "--summary", str(summary),
            "--markdown", str(markdown),
        ],
        cwd=ROOT,
        check=True,
    )

    data = json.loads(summary.read_text(encoding="utf-8"))
    next_policy = json.loads(proposed.read_text(encoding="utf-8"))

    kinds = {row.get("evolutionKind") for row in data.get("proposals") or []}
    assert "missing_repair_capability" in kinds
    assert "lab_self_limit" in kinds
    assert "core_sampling_blind_spot" in kinds
    assert "route_discovery_blind_spot" in kinds
    assert "method_exhaustion" in kinds

    assert data["policy"]["publicationAllowed"] is False
    assert data["policy"]["productionWritesAllowed"] is False
    assert data["policy"]["pullRequestOnly"] is True
    assert data["policy"]["requiresHumanMerge"] is True

    current = json.loads(POLICY.read_text(encoding="utf-8"))
    assert next_policy["learningLab"]["allStreamsSafetyCap"] > current["learningLab"]["allStreamsSafetyCap"]
    allow = json.loads(SELF.read_text(encoding="utf-8")).get("autoPatchAllowlist") or {}
    assert "learningLab.maxExploratoryProfilesPerProvider" in allow
    assert next_policy["learningLab"].get("targetProvidersPerRun") == 1
    assert next_policy["learningLab"].get("maxRepairRounds") == 1
    assert markdown.is_file()
    assert "NiakVIO Brain architecture evolution" in markdown.read_text(encoding="utf-8")

print("Brain self-architecture tests passed")
