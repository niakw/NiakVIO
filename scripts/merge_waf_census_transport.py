#!/usr/bin/env python3
"""Merge WAF/native-transport diagnostics into an existing provider census.

This is intentionally NOT a census renderer. The Repair census remains authority
for playback/route/candidate/history depth. Narrow WAF diagnostics may update only transport classification. A full current
provider replay through the residential path is different: it may promote a lane
only when playable media is identity-verified with zero contradictions.

That prevents a narrow transport probe from downgrading unrelated FULL/PARTIAL/
CANDIDATE/ROUTE/CHAIN evidence while still allowing real current-byte playback
proof to resolve a false harness/network symptom.
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


def _refresh_authority_rows(
    providers: list[dict[str, Any]],
    authority_status: dict[str, Any] | None,
) -> list[str]:
    """Project current arbiter metadata onto carried census rows.

    WAF remains transport-only: it never invents authority. This only prevents
    a fresh transport overlay from preserving stale authority fields from an
    older census after lifecycle/domain authority has already changed on main.
    """
    if not isinstance(authority_status, dict):
        return []
    authority_by_provider = {
        str(row.get("provider") or "").strip().casefold(): row
        for row in authority_status.get("providers") or []
        if isinstance(row, dict) and str(row.get("provider") or "").strip()
    }
    changed: list[str] = []
    for row in providers:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip().casefold()
        authority = authority_by_provider.get(provider)
        if not authority:
            continue
        fields = {
            "authorityRepairEligible": authority.get("repairEligible") is True,
            "authorityAction": str(authority.get("action") or "UNCLASSIFIED"),
            "authorityClass": str(authority.get("authorityClass") or "unknown"),
            "authorityConfidence": str(authority.get("confidence") or "unknown"),
            "authorityReasons": [
                str(value)
                for value in authority.get("reasons") or []
                if str(value).strip()
            ],
            "authorityKnown": True,
        }
        before = tuple(row.get(key) for key in (
            "authorityRepairEligible", "authorityAction", "authorityClass",
            "authorityConfidence", "authorityReasons", "authorityKnown",
            "statusRepairEligible", "repairEligible", "action",
        ))
        row.update(fields)
        status = str(row.get("status") or "")
        if census._lifecycle_disabled(fields):
            row["underlyingStatus"] = status
            status = "DISABLED"
            row["status"] = status
            row["color"] = census.STATUS_META[status][0]
            row["brainCheckRequired"] = False
        row["statusRepairEligible"] = census.is_repair_eligible_status(status)
        row["repairEligible"] = bool(
            row["statusRepairEligible"] and fields["authorityRepairEligible"]
        )
        row["action"] = census._authority_action(
            status,
            str(row.get("harnessTransportClass") or "not-applicable"),
            fields,
        )
        after = tuple(row.get(key) for key in (
            "authorityRepairEligible", "authorityAction", "authorityClass",
            "authorityConfidence", "authorityReasons", "authorityKnown",
            "statusRepairEligible", "repairEligible", "action",
        ))
        if before != after:
            changed.append(provider)
    return sorted(set(changed))



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


def _post_harness_repair_state(
    row: dict[str, Any],
    diagnostic: dict[str, Any],
    replay_rows: list[dict[str, Any]],
) -> str | None:
    """Return a normal Brain/census state only after native-like transport is proven.

    Residential/browser reachability alone is not enough. The full provider
    runtime must have executed without a WAF/timeout/identity failure and exposed
    a provider/runtime symptom. This is a lane transfer, never a repair proof.
    """
    if str(diagnostic.get("classification") or "") not in {
        "native-policy-reachable",
        "residential-exit-native-reachable",
        "github-native-route-reachable",
        "residential-native-route-reachable",
    }:
        return None
    if not replay_rows:
        return None

    stages = {
        str(item.get("debugStage") or item.get("debug_stage") or "").strip().casefold()
        for item in replay_rows
        if isinstance(item, dict)
    }
    statuses = {
        str(item.get("status") or "").strip().casefold()
        for item in replay_rows
        if isinstance(item, dict)
    }
    if any(int(item.get("playable") or 0) > 0 for item in replay_rows if isinstance(item, dict)):
        return None
    if any(item.get("identitySafe") is False for item in replay_rows if isinstance(item, dict)):
        return None
    if stages & {"provider_waf_challenge", "timeout"} or statuses & {"timeout"}:
        return None

    explicit_network = {
        "provider_network_exception",
        "provider_network_http_error",
        "provider_network_timeout",
    }
    if stages & explicit_network:
        # Native-like transport already reached the provider route. At this
        # point "network blocked" is no longer causal; fall back to the deepest
        # provider proof so the case returns to normal Brain repair.
        depths = {
            str(value or "").split("=", 1)[-1].strip().casefold()
            for value in row.get("evidenceDepth") or []
            if str(value or "").strip()
        }
        if "chain_reached" in depths:
            return "CHAIN REACHED"
        if "lookup_only" in depths or row.get("routeProof"):
            return "ROUTE PROVEN"
        return "NO PROOF"

    normal_zero = {
        "provider_network_zero_result",
        "content_lookup_completed_no_streams",
        "provider_zero_before_provider_network",
        "no_provider_request_observed",
        "no_streams",
    }
    if not (stages & normal_zero):
        return None

    depths = {
        str(value or "").split("=", 1)[-1].strip().casefold()
        for value in row.get("evidenceDepth") or []
        if str(value or "").strip()
    }
    if "chain_reached" in depths:
        return "CHAIN REACHED"
    if "lookup_only" in depths:
        return "ROUTE PROVEN" if row.get("routeProof") else "NO PROOF"
    return "NO PROOF"


def merge_transport(
    baseline: dict[str, Any],
    waf: dict[str, Any],
    *,
    authority_status: dict[str, Any] | None = None,
    evidence_run_id: str = "",
    evidence_sha: str = "",
) -> dict[str, Any]:
    out = copy.deepcopy(baseline)
    providers = out.get("providers")
    if not isinstance(providers, list):
        raise ValueError("baseline census providers must be a list")

    authority_refreshed = _refresh_authority_rows(providers, authority_status)

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
    replay_promoted: set[str] = set()
    replay_reclassified: set[str] = set()
    replay_repairable: set[str] = set()
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
        # This output represents the current WAF run only. Drop any replay/
        # differential annotation inherited from a previous overlay before
        # applying the evidence collected now.
        for field in census.TRANSPORT_OVERLAY_ROW_FIELDS:
            row.pop(field, None)
        provider_replay_rows = replay_by_provider.get(provider) or []
        if row.get("authorityRepairEligible") is False and census._lifecycle_disabled(row):
            row["status"] = "DISABLED"
            row["color"] = census.STATUS_META["DISABLED"][0]
            row["brainCheckRequired"] = False
            row["statusRepairEligible"] = False
            row["repairEligible"] = False
            row["action"] = census._authority_action(
                "DISABLED",
                str(row.get("harnessTransportClass") or "not-applicable"),
                row,
            )
            continue
        if provider_replay_rows:
            verified_lanes = sorted({
                str(value.get("lane") or "").strip().casefold()
                for value in provider_replay_rows
                if int(value.get("verified") or 0) > 0 and str(value.get("lane") or "").strip()
            })
            playable_lanes = sorted({
                str(value.get("lane") or "").strip().casefold()
                for value in provider_replay_rows
                if int(value.get("playable") or 0) > 0 and str(value.get("lane") or "").strip()
            })
            strict_verified_lanes = sorted({
                str(value.get("lane") or "").strip().casefold()
                for value in provider_replay_rows
                if int(value.get("playable") or 0) > 0
                and int(value.get("verified") or 0) == int(value.get("playable") or 0)
                and value.get("identitySafe") is True
                and int(value.get("contradictions") or 0) == 0
                and str(value.get("lane") or "").strip()
            })
            row["residentialProviderReplayClass"] = (
                "verified" if strict_verified_lanes
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
            if strict_verified_lanes:
                declared = {
                    str(value or "").strip().casefold()
                    for value in row.get("declaredLanes") or []
                    if str(value or "").strip()
                }
                current = {
                    str(value or "").strip().casefold()
                    for value in row.get("currentVerifiedLanes") or []
                    if str(value or "").strip()
                }
                current.update(strict_verified_lanes)
                row["currentVerifiedLanes"] = sorted(current)
                new_status = "FULL OK" if declared and declared.issubset(current) else "PARTIAL OK"
                row["status"] = new_status
                row["color"] = census.STATUS_META[new_status][0]
                row["action"] = census._action(new_status)
                row["brainCheckRequired"] = False
                row["repairEligible"] = False
                row["testedThisRun"] = True
                row["residentialProviderReplayPromoted"] = True
                replay_promoted.add(provider)
        if provider in network_allowed:
            differential = network_differential(waf, provider)
            if differential["classification"] != "no-network-differential-evidence":
                row["networkDifferentialClass"] = differential["classification"]
                row["networkDifferentialEvidence"] = list(differential["evidence"])
                network_changed.append(provider)
            if provider not in replay_promoted:
                repair_state = _post_harness_repair_state(row, differential, provider_replay_rows)
                if repair_state:
                    row["status"] = repair_state
                    row["color"] = census.STATUS_META[repair_state][0]
                    row["brainCheckRequired"] = True
                    authority_allowed = row.get("authorityRepairEligible") is not False
                    row["statusRepairEligible"] = census.is_repair_eligible_status(repair_state)
                    row["repairEligible"] = bool(row["statusRepairEligible"] and authority_allowed)
                    row["action"] = (
                        census._action(repair_state)
                        if authority_allowed
                        else census._authority_action(
                            repair_state,
                            str(differential.get("classification") or "not-applicable"),
                            row,
                        )
                    )
                    row["testedThisRun"] = True
                    row["residentialProviderReplayReclassified"] = True
                    replay_reclassified.add(provider)
                    if row["repairEligible"]:
                        replay_repairable.add(provider)
                    changed.append(provider)
                    continue
        if provider not in allowed:
            continue
        diagnostic = census.harness_transport_diagnostic(waf, provider)
        row["harnessTransportClass"] = diagnostic["classification"]
        row["harnessTransportEvidence"] = list(diagnostic["evidence"])
        if provider not in replay_promoted:
            repair_state = _post_harness_repair_state(row, diagnostic, provider_replay_rows)
            if repair_state:
                row["status"] = repair_state
                row["color"] = census.STATUS_META[repair_state][0]
                row["brainCheckRequired"] = True
                authority_allowed = row.get("authorityRepairEligible") is not False
                row["statusRepairEligible"] = census.is_repair_eligible_status(repair_state)
                row["repairEligible"] = bool(row["statusRepairEligible"] and authority_allowed)
                row["action"] = (
                    census._action(repair_state)
                    if authority_allowed
                    else census._authority_action(repair_state, diagnostic["classification"], row)
                )
                row["testedThisRun"] = True
                row["residentialProviderReplayReclassified"] = True
                replay_reclassified.add(provider)
                if row["repairEligible"]:
                    replay_repairable.add(provider)
            else:
                status = census.browser_harness_status(waf, provider)
                row["status"] = status
                row["color"] = census.STATUS_META[status][0]
                row["action"] = census._harness_action(status, diagnostic["classification"])
                row["brainCheckRequired"] = True
                row["repairEligible"] = False
                # Narrow transport diagnostics are not provider playback probes.
                row["testedThisRun"] = bool(row.get("testedThisRun", False)) and False
        changed.append(provider)

    # Membership authority is preserved. Transport diagnostics may move a member
    # between HARNESS MISMATCH and HARNESS/ENV BLOCKED, but may not add providers
    # to Repair or remove unrelated evidence.
    def without_promoted(values: list[Any]) -> list[Any]:
        return [
            value for value in values
            if str(value or "").strip().casefold() not in replay_promoted
        ]

    def normalized(values: list[Any]) -> list[str]:
        return sorted({
            str(value or "").strip().casefold()
            for value in values
            if str(value or "").strip()
        })

    # Recompute Repair from final rows, not from the carried baseline queue.
    # This incorporates both strict residential replay outcomes and any newer
    # arbiter/lifecycle decision projected above.
    out["repairQueue"] = sorted(
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and row.get("repairEligible") is True
        and str(row.get("provider") or "").strip()
    )
    authority_blocked = {
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and row.get("authorityRepairEligible") is False
        and str(row.get("provider") or "").strip()
    }
    out["environmentQueue"] = sorted(
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and str(row.get("status") or "") in census.ENVIRONMENT_ONLY_STATES
        and row.get("authorityRepairEligible") is not False
        and str(row.get("provider") or "").strip()
    )
    out["harnessQueue"] = list(out["environmentQueue"])
    # Exact transport queues are recomputed from final row status after the
    # overlay. Keep environmentQueue/harnessQueue above for compatibility only.
    out["harnessMismatchQueue"] = sorted(
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and str(row.get("status") or "") == "HARNESS MISMATCH"
        and row.get("authorityRepairEligible") is not False
        and str(row.get("provider") or "").strip()
    )
    out["environmentBlockedQueue"] = sorted(
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and str(row.get("status") or "") == "HARNESS/ENV BLOCKED"
        and row.get("authorityRepairEligible") is not False
        and str(row.get("provider") or "").strip()
    )
    out["symptomaticProviders"] = sorted(
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and census.is_symptomatic_status(str(row.get("status") or ""))
        and str(row.get("provider") or "").strip()
    )
    out["brainQueue"] = list(out["symptomaticProviders"])
    lifecycle_disabled_actions = {
        "KEEP_DISABLED",
        "DISABLE_MANUAL_POLICY",
        "DISABLE_SOURCE_REMOVED",
        "DISABLE_AUTHORITY_EXHAUSTED",
    }
    lifecycle_disabled = {
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and (
            str(row.get("authorityAction") or "") in lifecycle_disabled_actions
            or str(row.get("authorityClass") or "") in {
                "disabled", "manual-off", "source-removed", "stale-direct"
            }
        )
        and str(row.get("provider") or "").strip()
    }
    authority_rediscovery = {
        str(row.get("provider") or "").strip().casefold()
        for row in providers
        if isinstance(row, dict)
        and row.get("brainCheckRequired") is True
        and row.get("authorityRepairEligible") is False
        and str(row.get("provider") or "").strip().casefold() not in lifecycle_disabled
        and str(row.get("provider") or "").strip()
    }
    out["lifecycleDisabledQueue"] = sorted(lifecycle_disabled)
    out["authorityRediscoveryQueue"] = sorted(authority_rediscovery)
    out["authorityBlockedQueue"] = sorted(lifecycle_disabled | authority_rediscovery)

    out["counts"] = dict(sorted(Counter(
        str(row.get("status") or "")
        for row in providers
        if isinstance(row, dict) and str(row.get("status") or "")
    ).items()))
    out["harnessEvidenceRunId"] = str(evidence_run_id or waf.get("runId") or "")
    out["harnessEvidenceSha"] = str(evidence_sha or waf.get("triggerSha") or "")
    out["authorityRefreshedProviders"] = authority_refreshed
    out["harnessTransportUpdatedProviders"] = sorted(changed)
    out["networkDifferentialUpdatedProviders"] = sorted(network_changed)
    out["residentialProviderReplayPromotedProviders"] = sorted(replay_promoted)
    out["residentialProviderReplayReclassifiedProviders"] = sorted(replay_reclassified)
    out["residentialProviderReplayRepairableProviders"] = sorted(replay_repairable)
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
    ap.add_argument(
        "--authority-status",
        type=Path,
        default=Path("automation/provider-authority-status.json"),
    )
    ap.add_argument("--run-id", default="")
    ap.add_argument("--sha", default="")
    args = ap.parse_args()

    baseline = load(args.status)
    authority_status = load(args.authority_status) if args.authority_status.is_file() else {}
    merged = merge_transport(
        baseline,
        load(args.waf),
        authority_status=authority_status,
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
        f"authority_refreshed={len(merged.get('authorityRefreshedProviders') or [])} "
        f"network_differential={len(merged.get('networkDifferentialUpdatedProviders') or [])} "
        f"counts={json.dumps(merged.get('counts') or {}, sort_keys=True)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
