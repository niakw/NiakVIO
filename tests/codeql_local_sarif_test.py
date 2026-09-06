#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/codeql_local_sarif.py"

payload = {
    "runs": [
        {
            "tool": {
                "driver": {
                    "rules": [
                        {"id": "py/high", "name": "High rule", "properties": {"security-severity": "8.1"}},
                        {"id": "py/medium", "name": "Medium rule", "properties": {"security-severity": "5.4"}},
                    ]
                }
            },
            "results": [
                {"ruleId": "py/high"},
                {"ruleId": "py/medium"},
                {"ruleId": "py/medium"},
            ],
        }
    ]
}

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / "python.sarif").write_text(json.dumps(payload), encoding="utf-8")

    probe = subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert probe.returncode == 0, probe.stderr
    assert "CODEQL_RESULT_COUNT=3" in probe.stdout
    assert "NIAKVIO_CODEQL_LOCAL_EXTENDED results=3 high_or_critical=1 sarif=1" in probe.stdout
    assert "CODEQL_RULE_COUNT py/medium=2" in probe.stdout
    assert "CODEQL_RULE_COUNT py/high=1" in probe.stdout

    gated = subprocess.run(
        [sys.executable, str(SCRIPT), str(root), "--fail-high"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert gated.returncode != 0
    assert "OPEN_LOCAL_HIGH_ALERT py/high|8.1|High rule" in gated.stdout

with tempfile.TemporaryDirectory() as tmp:
    empty = subprocess.run(
        [sys.executable, str(SCRIPT), tmp],
        text=True,
        capture_output=True,
        check=False,
    )
    assert empty.returncode != 0
    assert "produced no SARIF" in (empty.stdout + empty.stderr)

print("CodeQL local SARIF evidence contract passed")
