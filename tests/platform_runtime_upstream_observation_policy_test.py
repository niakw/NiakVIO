#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_platform_runtime_policy.py"
spec = importlib.util.spec_from_file_location("validate_platform_runtime_policy", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Result:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode


with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
    os.environ.pop("NUVIO_SKIP_CLIENT_UPSTREAM_GUARD", None)
    os.environ.pop("NUVIO_REQUIRE_CLIENT_UPSTREAM_GUARD", None)
    with patch.object(module.subprocess, "run", return_value=Result(0)) as run:
        assert module.run_client_upstream_guard() == 0
        command = run.call_args.args[0]
        assert "--no-fail" in command, command

with patch.dict(
    os.environ,
    {"GITHUB_ACTIONS": "true", "NUVIO_REQUIRE_CLIENT_UPSTREAM_GUARD": "1"},
    clear=False,
):
    os.environ.pop("NUVIO_SKIP_CLIENT_UPSTREAM_GUARD", None)
    with patch.object(module.subprocess, "run", return_value=Result(2)) as run:
        assert module.run_client_upstream_guard() == 2
        command = run.call_args.args[0]
        assert "--no-fail" not in command, command

with patch.dict(
    os.environ,
    {"GITHUB_ACTIONS": "true", "NUVIO_SKIP_CLIENT_UPSTREAM_GUARD": "1"},
    clear=False,
):
    with patch.object(module.subprocess, "run") as run:
        assert module.run_client_upstream_guard() == 0
        run.assert_not_called()

print("platform runtime upstream observation policy test passed")
