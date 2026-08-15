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


def row_line(client: str, fixture: str, provider: str, language: str, title: str = "Mon ninja et moi 3") -> str:
    return (
        "FIELD_NATIVE_ROW "
        f"client={client} fixture={fixture} provider64={b64(provider)} index=0 "
        f"host64={b64('media.example')} media_hint64={b64('master.m3u8')} "
        f"title64={b64(title)} name64={b64(provider)} quality64={b64('1080p')} "
        f"language64={b64(language)} type64={b64('hls')}"
    )


def error_line(client: str, fixture: str, provider: str) -> str:
    return (
        "FIELD_NATIVE_ERROR "
        f"client={client} fixture={fixture} provider64={b64(provider)} "
        f"error64={b64('native bridge timeout')}"
    )


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    lines: list[str] = []
    for client in ("desktop", "mobile", "tv"):
        lines.append(result_line(client, "interstellar", "broad", 1))
        lines.append(row_line(client, "interstellar", "broad", "en", "Interstellar"))

        lines.append(result_line(client, "mon-ninja-et-moi-3", "subtitle-only", 1))
        lines.append(row_line(client, "mon-ninja-et-moi-3", "subtitle-only", "vostfr", "Mon ninja et moi 3 VOSTFR"))

        lines.append(result_line(client, "mon-ninja-et-moi-3", "rare-vf", 1))
        lines.append(row_line(client, "mon-ninja-et-moi-3", "rare-vf", "fr"))

        lines.append(result_line(client, "mon-ninja-et-moi-3", "unsafe-vf", 1))
        lines.append(row_line(client, "mon-ninja-et-moi-3", "unsafe-vf", "fr"))

        # The provider appears to return a row everywhere, but TV reports a
        # native runtime failure. TV must therefore not count as usable coverage.
        lines.append(result_line(client, "mon-ninja-et-moi-3", "runtime-vf", 1))
        lines.append(row_line(client, "mon-ninja-et-moi-3", "runtime-vf", "fr"))

    lines.append(error_line("tv", "mon-ninja-et-moi-3", "runtime-vf"))

    lines.append(result_line("desktop", "mon-ninja-et-moi-3", "broken-vf", 1))
    lines.append(row_line("desktop", "mon-ninja-et-moi-3", "broken-vf", "fr"))
    lines.append(result_line("mobile", "mon-ninja-et-moi-3", "broken-vf", 0))
    lines.append(result_line("tv", "mon-ninja-et-moi-3", "broken-vf", 0))
    (root / "desktop-native-corpus-synthetic.log").write_text("\n".join(lines) + "\n", encoding="utf-8")

    portfolio = {
        "schemaVersion": 2,
        "currentlyActiveObserved": 6,
        "recommendedActive": 1,
        "selected": ["broad"],
        "providers": [
            {
                "provider": "broad",
                "vf": False,
                "contentSafetyEligible": True,
                "safetyEligible": True,
                "evidenceEnough": True,
                "score": 100,
                "catalogueCoverageRate": 1,
                "recommendation": "active_core",
            },
            {
                "provider": "subtitle-only",
                "vf": True,
                "contentSafetyEligible": True,
                "safetyEligible": True,
                "evidenceEnough": True,
                "score": 80,
                "catalogueCoverageRate": 0.5,
                "recommendation": "lab_only_redundant",
            },
            {
                "provider": "rare-vf",
                "vf": True,
                "contentSafetyEligible": True,
                "safetyEligible": True,
                "evidenceEnough": False,
                "score": 20,
                "catalogueCoverageRate": 0.2,
                "recommendation": "lab_only_insufficient_evidence",
            },
            {
                "provider": "runtime-vf",
                "vf": True,
                "contentSafetyEligible": True,
                "nativeReliabilityEligible": False,
                "safetyEligible": True,
                "evidenceEnough": True,
                "score": 15,
                "catalogueCoverageRate": 0.15,
                "recommendation": "repair_runtime_or_transport",
            },
            {
                "provider": "broken-vf",
                "vf": True,
                "contentSafetyEligible": True,
                "safetyEligible": True,
                "evidenceEnough": False,
                "score": 10,
                "catalogueCoverageRate": 0.05,
                "recommendation": "lab_only_insufficient_evidence",
            },
            {
                "provider": "unsafe-vf",
                "vf": True,
                "contentSafetyEligible": False,
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

    # VOSTFR helps general catalogue redundancy but never satisfies the VF-audio objective.
    assert "subtitle-only" in data["selected"], data
    assert rows["subtitle-only"]["fullCrossPlatformVfFixtures"] == [], rows["subtitle-only"]

    # A genuinely French rare provider remains protected even with weak global coverage.
    assert "rare-vf" in data["selected"], data
    assert rows["rare-vf"]["recommendation"] == "active_coverage_guard", rows["rare-vf"]
    assert "mon-ninja-et-moi-3" in rows["rare-vf"]["fullCrossPlatformVfFixtures"], rows["rare-vf"]
    assert "mon-ninja-et-moi-3" in rows["rare-vf"]["vfCoverageProtectionFixtures"], rows["rare-vf"]
    assert "rare-vf" in data["protectedVfCoverageProviders"], data

    # A count>0 row with a TV runtime error is only two-client usable coverage.
    assert "mon-ninja-et-moi-3" not in rows["runtime-vf"]["fullCrossPlatformCoverageFixtures"], rows["runtime-vf"]
    assert "mon-ninja-et-moi-3" not in rows["runtime-vf"]["fullCrossPlatformVfFixtures"], rows["runtime-vf"]
    assert rows["runtime-vf"]["recommendation"] == "repair_priority_unique_coverage", rows["runtime-vf"]
    assert "mon-ninja-et-moi-3" in rows["runtime-vf"]["repairPriorityFixtures"], rows["runtime-vf"]

    # A rare French provider that only works on one native client is also repair priority.
    assert "broken-vf" not in data["selected"], data
    assert rows["broken-vf"]["recommendation"] == "repair_priority_unique_coverage", rows["broken-vf"]
    assert "mon-ninja-et-moi-3" in rows["broken-vf"]["repairPriorityFixtures"], rows["broken-vf"]

    # Safety remains absolute: wrong/unsafe content never receives a coverage exception.
    assert "unsafe-vf" not in data["selected"], data
    assert rows["unsafe-vf"]["recommendation"] == "quarantine_unsafe", rows["unsafe-vf"]

assert POLICY["coverage_preservation"]["never_delete_for_redundancy_without_coverage_evidence"] is True
assert POLICY["coverage_preservation"]["allow_active_above_normal_max_when_needed"] is True
assert POLICY["selection"]["rare_partial_platform_coverage_becomes_repair_priority"] is True

print("provider coverage preservation tests passed")
