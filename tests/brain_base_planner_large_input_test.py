#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "brain_base_large_input", ROOT / "scripts" / "brain_repair_runtime.py"
)
assert spec and spec.loader
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)

candidate = {"canonical_id": "large-input-demo", "metadata": {"supportedTypes": ["movie"]}}
result = {
    "status": "no_streams",
    "evidence": {"streams_playable": 0, "streams_returned": 0},
    "tests": [{
        "fixture": {"mediaType": "movie", "category": "movie"},
        "status": "no_streams",
        "failure_class": "content_lookup_completed_no_streams",
        "network_observations": [{"status": 200, "ok": True, "stage": "search"}],
    }],
}
items = [{
    "key": "published:large-input-demo",
    "candidate": candidate,
    "result": result,
    "state": {},
}]
# More than the historical production memory payload: all rows must reach Node
# without pruning evidence or retrying a partially read synchronous stdin pipe.
memory = [{
    "providerId": f"unrelated-{index}",
    "profile": "adaptive_runtime_recovery",
    "failureClass": "search_gap",
    "signature": "x" * 1024,
    "failures": 1,
    "executionObserved": True,
} for index in range(1500)]
real_run = subprocess.run
paths: list[Path] = []


def inspect_run(args, **kwargs):
    input_path = Path(kwargs["env"]["NUVIO_BRAIN_PLANNER_INPUT_FILE"])
    paths.append(input_path)
    raw = input_path.read_bytes()
    payload = json.loads(raw)
    assert len(raw) > 1_000_000, len(raw)
    assert payload["negativeMemory"] == memory
    assert payload["items"][0]["key"] == "published:large-input-demo"
    assert kwargs["input"] == b""
    return real_run(args, **kwargs)


with (
    patch.object(brain, "policy", return_value={}),
    patch.object(brain, "planner_learned_skills", return_value={}),
    patch.object(brain, "planner_historical_solutions", return_value=[]),
    patch.object(brain, "planner_llm_guidance", return_value=[]),
    patch.object(brain, "planner_negative_memory", return_value=memory),
    patch.object(brain, "planner_transient_negative_memory", return_value=[]),
    patch.dict(os.environ, {"NUVIO_BRAIN_PLANNER_INPUT_FILE": "/missing/inherited-input.json"}),
    patch.object(brain.subprocess, "run", side_effect=inspect_run),
):
    plans = brain._execute_planner(items, "repair")
    assert plans["published:large-input-demo"]["providerId"] == "large-input-demo", plans
    replanned = brain.replan_observation(
        candidate, result, plan_key="published:large-input-demo", mode="repair"
    )
    assert replanned["providerId"] == "large-input-demo", replanned
    assert os.environ["NUVIO_BRAIN_PLANNER_INPUT_FILE"] == "/missing/inherited-input.json"
    assert all(not path.exists() for path in paths)

    # The temporary payload is also removed when the actual Node process fails;
    # diagnostics must preserve exit status without exposing stderr URLs.
    with tempfile.TemporaryDirectory() as directory:
        failing = Path(directory) / "failing.mjs"
        failing.write_text(
            'process.stderr.write("https://example.test/private?token=secret"); process.exit(7);\n',
            encoding="utf-8",
        )
        with patch.object(brain, "PLAN_SCRIPT", failing):
            try:
                brain._execute_planner(items, "repair")
            except RuntimeError as error:
                assert "exit=7" in str(error), error
                assert "example.test" not in str(error), error
                assert "secret" not in str(error), error
            else:
                raise AssertionError("a failed planner must remain an error")
    assert all(not path.exists() for path in paths)

assert len(paths) == 3, paths
print("brain base planner large-input transport: ok")
