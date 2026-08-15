#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / ".github/triggers/nuvio-client-lab.json").read_text(encoding="utf-8"))
SCRIPT = ROOT / "scripts/rank_provider_portfolio.cjs"
POLICY = json.loads((ROOT / ".github/provider-portfolio-policy.json").read_text(encoding="utf-8"))


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def emit(log: list[str], client: str, fixture_slug: str, provider: str, title: str, duration_seconds: int) -> None:
    log.append(
        "FIELD_NATIVE_RESULT "
        f"client={client} fixture={fixture_slug} provider64={b64(provider)} enabled=true duration_ms=2500 count=1"
    )
    log.append(
        "FIELD_NATIVE_ROW "
        f"client={client} fixture={fixture_slug} provider64={b64(provider)} index=0 "
        f"host64={b64('media.example')} media_hint64={b64('master.m3u8')} "
        f"title64={b64(title)} name64={b64(provider)} quality64={b64('1080p')} language64={b64('fr')} type64={b64('hls')}"
    )
    log.append(
        "FIELD_NATIVE_TRANSPORT "
        f"client={client} fixture={fixture_slug} provider64={b64(provider)} state=ok kind=hls status=200 "
        f"content_type64={b64('application/vnd.apple.mpegurl')} extm3u=true duration_seconds={duration_seconds} "
        f"host64={b64('media.example')} media_hint64={b64('master.m3u8')}"
    )


with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    lines: list[str] = []
    for row in CONFIG["fixtures"]:
        fixture = row["fixture"]
        duration = int(fixture.get("expectedDurationMinutes") or 1) * 60
        for client in ("desktop", "mobile", "tv"):
            emit(lines, client, row["slug"], "streamzo", fixture["title"], duration)
            # A high-response provider that serves unrelated content must never
            # survive the portfolio selector just because its catalogue looks big.
            emit(lines, client, row["slug"], "1shows", "Ben 10 Ultimate Alien", duration)
            # A provider with correct content but a native runtime defect is a
            # repair target, not an unsafe-content quarantine candidate.
            emit(lines, client, row["slug"], "runtime-flaky", fixture["title"], duration)
    lines.append(
        "FIELD_NATIVE_ERROR "
        f"client=tv fixture=mon-ninja-et-moi-3 provider64={b64('runtime-flaky')} error64={b64('native bridge timeout')}"
    )
    (tmp_path / "desktop-native-corpus-synthetic.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    output = tmp_path / "portfolio.json"
    result = subprocess.run(
        ["node", str(SCRIPT), "--dir", str(tmp_path), "--output", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(output.read_text(encoding="utf-8"))
    providers = {row["provider"]: row for row in data["providers"]}

    assert providers["streamzo"]["qualityEligible"] is True, providers["streamzo"]
    assert providers["streamzo"]["recommendation"] == "active_core", providers["streamzo"]
    assert providers["streamzo"]["catalogueCoverageRate"] == 1, providers["streamzo"]
    assert providers["streamzo"]["crossPlatformFixtureRate"] == 1, providers["streamzo"]

    assert providers["1shows"]["identityContradictions"] > 0, providers["1shows"]
    assert providers["1shows"]["contentSafetyEligible"] is False, providers["1shows"]
    assert providers["1shows"]["safetyEligible"] is False, providers["1shows"]
    assert providers["1shows"]["recommendation"] == "quarantine_unsafe", providers["1shows"]
    assert "1shows" not in data["selected"], data["selected"]

    flaky = providers["runtime-flaky"]
    assert flaky["identityContradictions"] == 0, flaky
    assert flaky["contentSafetyEligible"] is True, flaky
    assert flaky["safetyEligible"] is True, flaky
    assert flaky["nativeReliabilityEligible"] is False, flaky
    assert flaky["runtimeErrors"] == 1, flaky
    assert flaky["qualityEligible"] is False, flaky
    assert flaky["recommendation"] == "repair_runtime_or_transport", flaky
    assert "runtime-flaky" not in data["selected"], data["selected"]

    # 36/45 remains the normal compact portfolio target. The larger emergency
    # ceiling is only available to the coverage-preservation layer when a safe
    # provider carries catalogue/VF value the normal core cannot replace.
    target = int(POLICY["portfolio"]["target_unique_active"])
    normal_max = int(POLICY["portfolio"]["normal_max_unique_active"])
    hard_max = int(POLICY["portfolio"]["hard_max_unique_active"])
    assert target < 50
    assert normal_max <= 45
    assert hard_max >= normal_max
    assert POLICY["coverage_preservation"]["allow_active_above_normal_max_when_needed"] is True
    assert POLICY["coverage_preservation"]["never_delete_for_redundancy_without_coverage_evidence"] is True
    assert POLICY["coverage_preservation"]["repair_before_retire_when_unique_or_vf"] is True

    # The six-work native corpus is a strong regression/runtime gate, not enough
    # evidence by itself to retire a provider with potentially unique catalogue.
    retirement = POLICY["retirement_guard"]
    assert retirement["portfolio_ranking_is_advisory"] is True
    assert retirement["automatic_deactivation_from_portfolio"] is False
    assert retirement["require_broad_catalogue_evidence_before_redundancy_deactivation"] is True
    assert int(retirement["minimum_breadth_fixtures_before_redundancy_deactivation"]) >= 20
    assert retirement["require_no_unique_fixture_coverage"] is True
    assert retirement["require_no_unique_vf_fixture_coverage"] is True
    assert retirement["runtime_or_transport_failure_means_repair_not_unsafe"] is True

print("provider portfolio quality-first ranking tests passed")
