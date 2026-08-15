#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/protect_provider_coverage.cjs"
POLICY = json.loads((ROOT / ".github/provider-portfolio-policy.json").read_text(encoding="utf-8"))


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def result_line(client: str, fixture: str, provider: str, count: int) -> str:
    return (
        "FIELD_NATIVE_RESULT "
        f"client={client} fixture={fixture} provider64={b64(provider)} "
        f"enabled=true duration_ms=2500 count={count}"
    )


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    lines: list[str] = []
    for client in ("desktop", "mobile", "tv"):
        lines.append(result_line(client, "interstellar", "broad", 1))
        lines.append(result_line(client, "mon-ninja-et-moi-3", "rare-vf", 1))
        lines.append(result_line(client, "mon-ninja-et-moi-3", "unsafe-vf", 1))
    lines.append(result_line("desktop", "mon-ninja-et-moi-3", "broken-vf", 1))
    lines.append(result_line("mobile", "mon-ninja-et-moi-3", "broken-vf", 0))
    lines.append(result_line("tv", "mon-ninja-et-moi-3", "broken-vf", 0))
    (root / "desktop-native-corpus-synthetic.log").write_text("\n".join(lines) + "\n", encoding="utf-8")

    portfolio = {
        "schemaVersion": 1,
        "currentlyActiveObserved": 4,
        "recommendedActive": 1,
        "selected": ["broad"],
        "providers": [
            {
                "provider": "broad",
                "vf": False,
                "safetyEligible": True,
                "evidenceEnough": True,
                "score": 100,
                "catalogueCoverageRate": 1,
                "recommendation": "active_core",
            },
            {
                "provider": "rare-vf",
                "vf": True,
                "safetyEligible": True,
                "evidenceEnough": False,
                "score": 20,
                "catalogueCoverageRate": 0.2,
                "recommendation": "lab_only_insufficient_evidence",
            },
            {
                "provider": "broken-vf",
                "vf": True,
                "safetyEligible": True,
                "evidenceEnough": False,
                "score": 10,
                "catalogueCoverageRate": 0.05,
                "recommendation": "lab_only_insufficient_evidence",
            },
            {
                "provider": "unsafe-vf",
                "vf": True,
                "safetyEligible": False,
                "evidenceEnough": True,
                "score": 99,
                "catalogueCoverageRate": 1,
                "recommendation": "quarantine_unsafe",
            },
        ],
    }
    portfolio_path = root / "provider-portfolio.json"
    portfolio_path.write_text(json.dumps(portfolio), encoding="utf-8")

    run = subprocess.run(
        ["node", str(SCRIPT), "--dir", str(root), "--portfolio", str(portfolio_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    data = json.loads(portfolio_path.read_text(encoding="utf-8"))
    rows = {row["provider"]: row for row in data["providers"]}

    assert "rare-vf" in data["selected"], data
    assert rows["rare-vf"]["recommendation"] == "active_coverage_guard", rows["rare-vf"]
    assert "mon-ninja-et-moi-3:general_redundancy" in rows["rare-vf"]["coverageProtectionFixtures"], rows["rare-vf"]
    assert "broken-vf" not in data["selected"], data
    assert rows["broken-vf"]["recommendation"] == "repair_priority_unique_coverage", rows["broken-vf"]
    assert "mon-ninja-et-moi-3" in rows["broken-vf"]["repairPriorityFixtures"], rows["broken-vf"]
    assert "unsafe-vf" not in data["selected"], data
    assert rows["unsafe-vf"]["recommendation"] == "quarantine_unsafe", rows["unsafe-vf"]

assert POLICY["coverage_preservation"]["never_delete_for_redundancy_without_coverage_evidence"] is True
assert POLICY["coverage_preservation"]["allow_active_above_normal_max_when_needed"] is True
assert POLICY["selection"]["rare_partial_platform_coverage_becomes_repair_priority"] is True

print("provider coverage preservation tests passed")
