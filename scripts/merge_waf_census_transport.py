#!/usr/bin/env python3
"""Merge WAF/native-transport diagnostics into an existing provider census.

This is intentionally NOT a census renderer. The Repair census remains authority
for playback/route/candidate/history depth. WAF diagnostics may update only the
transport classification of providers that were already in the harness queue.

That prevents a narrow transport probe from downgrading unrelated FULL/PARTIAL/
CANDIDATE/ROUTE/CHAIN evidence or expanding the provider-code repair queue.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

import render_provider_census_status as census


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value



def network_differential(waf: dict[str, Any], provider: str) -> dict[str, Any]:
    wanted = str(provider or "").strip().casefold()
    rows = [
        row for row in waf.get("rows") or []
        if isinstance(row, dict)
        and str(row.get("provider") or "").strip().casefold() == wanted
        and str(row.get("seedKind") or "") == "network-failure-replay"
    ]
    if not rows:
        return {"classification": "no-network-differential-evidence", "evidence": []}

    evidence: list[str] = []
    residential_native = False
    residential_browser = False
    residential_present = False
    residential_blocked = False
    github_native = False
    github_browser = False

    for row in rows:
        lane = str(row.get("lane") or "unknown").strip().casefold() or "unknown"
        direct = row.get("directHttpProfile") if isinstance(row.get("directHttpProfile"), dict) else {}
        okhttp = row.get("okHttpJvmProfile") if isinstance(row.get("okHttpJvmProfile"), dict) else {}
        g_direct = str(direct.get("outcome") or "")
        g_okhttp = str(okhttp.get("outcome") or "")
        g_browser = str(row.get("outcome") or "")
        if g_direct == "direct_http_content_reached" or g_okhttp == "okhttp_jvm_content_reached":
            github_native = True
        if g_browser == "browser_content_reached":
            github_browser = True

        residential = row.get("residentialExitNodeProfile") if isinstance(row.get("residentialExitNodeProfile"), dict) else {}
        r_browser = ""
        r_direct = ""
        r_okhttp = ""
        if residential:
            residential_present = True
            r_browser = str(residential.get("outcome") or "")
            r_direct_row = residential.get("directHttpProfile") if isinstance(residential.get("directHttpProfile"), dict) else {}
            r_okhttp_row = residential.get("okHttpJvmProfile") if isinstance(residential.get("okHttpJvmProfile"), dict) else {}
            r_direct = str(r_direct_row.get("outcome") or "")
            r_okhttp = str(r_okhttp_row.get("outcome") or "")
            if r_direct == "direct_http_content_reached" or r_okhttp == "okhttp_jvm_content_reached":
                residential_native = True
            if r_browser == "browser_content_reached":
                residential_browser = True
            blocked_values = [value for value in (r_browser, r_direct, r_okhttp) if value]
            if blocked_values and all(
                ("challenge_persisted" in value) or value.endswith("_timeout") or value.endswith("_error")
                for value in blocked_values
            ):
                residential_blocked = True

        evidence.append(
            f"{lane}: github-browser={g_browser or 'unknown'}, "
            f"github-okhttp={g_okhttp or 'unknown'}, github-direct={g_direct or 'unknown'}, "
            f"residential-browser={r_browser or 'unavailable'}, "
            f"residential-okhttp={r_okhttp or 'unavailable'}, "
            f"residential-direct={r_direct or 'unavailable'}"
        )

    if residential_native and not github_native:
        classification = "residential-native-route-reachable"
    elif github_native:
        classification = "github-native-route-reachable"
    elif residential_browser and not github_browser:
        classification = "residential-browser-route-reachable"
    elif residential_present and residential_blocked:
        classification = "residential-route-still-blocked"
    elif not residential_present:
        classification = "residential-unavailable"
    else:
        classification = "network-route-inconclusive"
    return {"classification": classification, "evidence": evidence}


def merge_transport(
    baseline: dict[str, Any],
    waf: dict[str, Any],
    *,
    evidence_run_id: str = "",
    evidence_sha: str = "",
) -> dict[str, Any]:
    out = copy.deepcopy(baseline)
    providers = out.get("providers")
    if not isinstance(providers, list):
        raise ValueError("baseline census providers must be a list")

    baseline_environment = {
        str(value or "").strip().casefold()
        for value in (baseline.get("environmentQueue") or baseline.get("harnessQueue") or [])
        if str(value or "").strip()
    }
    waf_providers = {
        str(row.get("provider") or "").strip().casefold()
        for row in waf.get("rows") or []
        if isinstance(row, dict) and str(row.get("provider") or "").strip()
    }
    allowed = baseline_environment & waf_providers
    baseline_network = {
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and str(row.get("status") or "") == "PROVIDER NETWORK BLOCKED"
        and str(row.get("provider") or "").strip()
    }
    network_allowed = baseline_network & waf_providers

    changed: list[str] = []
    network_changed: list[str] = []
    replay_summary = waf.get("residentialProviderReplay") if isinstance(waf.get("residentialProviderReplay"), dict) else {}
    replay_rows = replay_summary.get("rows") if isinstance(replay_summary.get("rows"), list) else []
    replay_by_provider: dict[str, list[dict[str, Any]]] = {}
    for replay_row in replay_rows:
        if not isinstance(replay_row, dict):
            continue
        replay_provider = str(replay_row.get("provider") or "").strip().casefold()
        if replay_provider:
            replay_by_provider.setdefault(replay_provider, []).append(replay_row)
    for row in providers:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip().casefold()
        provider_replay_rows = replay_by_provider.get(provider) or []
        if provider_replay_rows:
            verified_lanes = sorted({
                str(value.get("lane") or "")
                for value in provider_replay_rows
                if int(value.get("verified") or 0) > 0 and str(value.get("lane") or "")
            })
            playable_lanes = sorted({
                str(value.get("lane") or "")
                for value in provider_replay_rows
                if int(value.get("playable") or 0) > 0 and str(value.get("lane") or "")
            })
            row["residentialProviderReplayClass"] = (
                "verified" if verified_lanes
                else "playable-unverified" if playable_lanes
                else "no-verified-media"
            )
            row["residentialProviderReplayEvidence"] = [
                f"{str(value.get('lane') or 'unknown')}: status={str(value.get('status') or 'unknown')}, "
                f"stage={str(value.get('debugStage') or 'unknown')}, raw={int(value.get('raw') or 0)}, "
                f"playable={int(value.get('playable') or 0)}, verified={int(value.get('verified') or 0)}, "
                f"identitySafe={str(value.get('identitySafe') is True).lower()}"
                for value in provider_replay_rows
            ]
        if provider in network_allowed:
            differential = network_differential(waf, provider)
            if differential["classification"] != "no-network-differential-evidence":
                row["networkDifferentialClass"] = differential["classification"]
                row["networkDifferentialEvidence"] = list(differential["evidence"])
                network_changed.append(provider)
        if provider not in allowed:
            continue
        diagnostic = census.harness_transport_diagnostic(waf, provider)
        status = census.browser_harness_status(waf, provider)
        row["status"] = status
        row["color"] = census.STATUS_META[status][0]
        row["harnessTransportClass"] = diagnostic["classification"]
        row["harnessTransportEvidence"] = list(diagnostic["evidence"])
        row["action"] = census._harness_action(status, diagnostic["classification"])
        row["brainCheckRequired"] = True
        row["repairEligible"] = False
        # WAF transport diagnostics are not provider playback probes.
        row["testedThisRun"] = bool(row.get("testedThisRun", False)) and False
        changed.append(provider)

    # Membership authority is preserved. Transport diagnostics may move a member
    # between HARNESS MISMATCH and HARNESS/ENV BLOCKED, but may not add providers
    # to Repair or remove unrelated evidence.
    out["repairQueue"] = list(baseline.get("repairQueue") or [])
    out["environmentQueue"] = list(baseline.get("environmentQueue") or [])
    out["harnessQueue"] = list(baseline.get("harnessQueue") or out["environmentQueue"])
    out["symptomaticProviders"] = list(baseline.get("symptomaticProviders") or [])
    out["brainQueue"] = list(baseline.get("brainQueue") or out["symptomaticProviders"])

    out["counts"] = dict(sorted(Counter(
        str(row.get("status") or "")
        for row in providers
        if isinstance(row, dict) and str(row.get("status") or "")
    ).items()))
    out["harnessEvidenceRunId"] = str(evidence_run_id or waf.get("runId") or "")
    out["harnessEvidenceSha"] = str(evidence_sha or waf.get("triggerSha") or "")
    out["harnessTransportUpdatedProviders"] = sorted(changed)
    out["networkDifferentialUpdatedProviders"] = sorted(network_changed)
    residential = waf.get("residentialExitNodeEvidence")
    if isinstance(residential, dict):
        out["residentialExitNodeEvidence"] = copy.deepcopy(residential)
    if replay_summary:
        out["residentialProviderReplay"] = copy.deepcopy(replay_summary)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--waf", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--sha", default="")
    args = ap.parse_args()

    baseline = load(args.status)
    merged = merge_transport(
        baseline,
        load(args.waf),
        evidence_run_id=args.run_id,
        evidence_sha=args.sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_WAF_CENSUS_TRANSPORT_MERGE "
        f"repair_queue={len(merged.get('repairQueue') or [])} "
        f"environment_queue={len(merged.get('environmentQueue') or [])} "
        f"updated={len(merged.get('harnessTransportUpdatedProviders') or [])} "
        f"network_differential={len(merged.get('networkDifferentialUpdatedProviders') or [])} "
        f"counts={json.dumps(merged.get('counts') or {}, sort_keys=True)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
