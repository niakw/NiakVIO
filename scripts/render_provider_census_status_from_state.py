#!/usr/bin/env python3
"""Render PROVIDER_CENSUS_STATUS.md from the already-authoritative census state.

Unlike the full census renderer this module does not interpret probe results.
It is safe for transport-only overlays: provider proof depth and queue membership
have already been decided by Repair/merge_waf_census_transport.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import render_provider_census_status as census

STATUS_ORDER = [
    "FULL OK",
    "PARTIAL OK",
    "CANDIDATE OK",
    "ROUTE PROVEN",
    "CHAIN REACHED",
    "NO PROOF",
    "HARNESS MISMATCH",
    "CLIENT TRANSPORT GAP",
    "HARNESS/ENV BLOCKED",
    "PROVIDER NETWORK BLOCKED",
    "PROVIDER JS BROKEN",
    "PROVIDER JS FULLY BROKEN",
    "REGRESSION PROVIDER JS",
    "REGRESSION PROVIDER",
    "DISABLED",
]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def joined(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "—"
    rows = [str(item).strip() for item in value if str(item).strip()]
    return "; ".join(rows) if rows else "—"


def cell(value: object) -> str:
    text = str(value or "—").strip() or "—"
    return text.replace("|", "\\|").replace("\n", " ")



def residential_probe_cell(state: dict[str, Any], row: dict[str, Any]) -> str:
    residential = state.get("residentialExitNodeEvidence")
    status = str(row.get("status") or "")
    if status not in census.ENVIRONMENT_ONLY_STATES:
        return "—"
    if not isinstance(residential, dict) or residential.get("enabled") is not True:
        return "—"
    if residential.get("available") is not True:
        return "⚠️ unavailable · GitHub-only"
    transport = str(row.get("harnessTransportClass") or "")
    if transport.startswith("residential-exit-"):
        return "✅ compared"
    return "residential available · no matched lane"



def residential_replay_cell(row: dict[str, Any]) -> str:
    replay_class = str(row.get("residentialProviderReplayClass") or "").strip()
    if not replay_class:
        return "—"
    if row.get("residentialProviderReplayPromoted") is True:
        lanes = joined(row.get("currentVerifiedLanes"))
        return f"✅ {replay_class}" + (f" · {lanes}" if lanes else "")
    return replay_class


def network_differential_cell(row: dict[str, Any]) -> str:
    if str(row.get("status") or "") != "PROVIDER NETWORK BLOCKED":
        return "—"
    value = str(row.get("networkDifferentialClass") or "").strip()
    return value or "not compared"


def render(state: dict[str, Any]) -> str:
    counts = state.get("counts") if isinstance(state.get("counts"), dict) else {}
    providers = [row for row in state.get("providers") or [] if isinstance(row, dict)]
    rank = {status: index for index, status in enumerate(STATUS_ORDER)}
    providers.sort(key=lambda row: (
        rank.get(str(row.get("status") or ""), len(rank)),
        str(row.get("provider") or ""),
    ))

    count_parts = []
    for status in STATUS_ORDER:
        count = int(counts.get(status) or 0)
        if count <= 0:
            continue
        emoji = census.STATUS_META.get(status, ("⚪", ""))[0]
        count_parts.append(f"{emoji} {count} {status}")
    for status in sorted(set(counts) - set(STATUS_ORDER)):
        count = int(counts.get(status) or 0)
        if count > 0:
            emoji = census.STATUS_META.get(status, ("⚪", ""))[0]
            count_parts.append(f"{emoji} {count} {status}")

    run_id = str(state.get("runId") or "unknown")
    sha = str(state.get("triggerSha") or "unknown")
    transport_run = str(state.get("harnessEvidenceRunId") or "")
    evidence_line = f"Evidence authority: Repair census run {run_id} · SHA {sha[:12]}"
    if transport_run:
        evidence_line += f" · transport overlay {transport_run}"

    harness_mismatch_queue = state.get("harnessMismatchQueue")
    if not isinstance(harness_mismatch_queue, list):
        harness_mismatch_queue = [
            str(row.get("provider") or "")
            for row in providers
            if str(row.get("status") or "") == "HARNESS MISMATCH"
            and row.get("authorityRepairEligible") is not False
        ]
    client_transport_gap_queue = state.get("clientTransportGapQueue")
    if not isinstance(client_transport_gap_queue, list):
        client_transport_gap_queue = [
            str(row.get("provider") or "")
            for row in providers
            if str(row.get("status") or "") == "CLIENT TRANSPORT GAP"
            and row.get("authorityRepairEligible") is not False
        ]
    environment_blocked_queue = state.get("environmentBlockedQueue")
    if not isinstance(environment_blocked_queue, list):
        environment_blocked_queue = [
            str(row.get("provider") or "")
            for row in providers
            if str(row.get("status") or "") == "HARNESS/ENV BLOCKED"
            and row.get("authorityRepairEligible") is not False
        ]

    residential = state.get("residentialExitNodeEvidence") if isinstance(state.get("residentialExitNodeEvidence"), dict) else {}
    residential_notice = ""
    attempt = state.get("lastRepairAttempt") if isinstance(state.get("lastRepairAttempt"), dict) else {}
    attempt_notice = ""
    if attempt:
        attempt_notice = (
            "Latest Repair/FORCE attempt: **run "
            + str(attempt.get("runId") or "unknown")
            + "** · selected **"
            + str(len(attempt.get("selectedProviders") or []))
            + "** · candidates **"
            + str(len(attempt.get("candidateProviders") or []))
            + "** · validated **"
            + str(len(attempt.get("validatedProviders") or []))
            + "** · Learning debt recorded **"
            + str(len(attempt.get("deferredToLearningSlotProviders") or []))
            + "** · result **"
            + str(attempt.get("noProgressReason") or ("validated" if attempt.get("publicationAllowed") is True else "no validated publication"))
            + "**."
        )
    if residential.get("enabled") is True:
        if residential.get("available") is True:
            residential_notice = "Residential harness: **available** · private exit compared where matched."
        else:
            residential_notice = "⚠️ Residential harness: **unavailable** · this overlay used GitHub-hosted transport only."

    lines = [
        "# NiakVIO Provider Census Status",
        "",
        "> Auto-generated from automation/provider-census-status.json. Probe interpretation belongs to Repair; WAF overlays are transport-only.",
        "",
        "Latest provider census state: **" + " · ".join(count_parts) + f"** across **{len(providers)} providers**.",
        evidence_line + ".",
        *([attempt_notice] if attempt_notice else []),
        f"Symptomatic providers: **{len(state.get('symptomaticProviders') or [])}** · automated repair queue: **{len(state.get('repairQueue') or [])}** · lifecycle disabled: **{len(state.get('lifecycleDisabledQueue') or [])}** · authority rediscovery: **{len(state.get('authorityRediscoveryQueue') or [])}** · harness mismatch: **{len(harness_mismatch_queue)}** · client transport gap: **{len(client_transport_gap_queue)}** · environment blocked: **{len(environment_blocked_queue)}**.",
        *([residential_notice] if residential_notice else []),
        "",
        "## Status semantics",
        "",
    ]
    for status in STATUS_ORDER:
        if status not in census.STATUS_META:
            continue
        emoji, description = census.STATUS_META[status]
        lines.append(f"- {emoji} **{status}** — {description}.")
    lines.extend([
        "",
        "**Important:** browser/OkHttp reachability is transport evidence only. It never promotes playback status and never authorizes provider-code mutation by itself.",
        "",
        "| Provider | Status | Run | Declared lanes | Verified lanes | Retained proof | Candidate proof | Route proof | Authority | Corpus progress | Evidence depth | Harness transport | Residential probe | Residential replay | Network differential | Latest lane verdicts | Dominant issue | Next action |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    for row in providers:
        status = str(row.get("status") or "")
        emoji = str(row.get("color") or census.STATUS_META.get(status, ("⚪", ""))[0])
        lines.append("| " + " | ".join([
            f"**{cell(row.get('provider'))}**",
            f"{emoji} **{cell(status)}**",
            "tested" if row.get("testedThisRun") is True else "carried",
            cell(joined(row.get("declaredLanes"))),
            cell(joined(row.get("currentVerifiedLanes"))),
            cell(joined(row.get("historicalProof"))),
            cell(joined(row.get("candidateProof"))),
            cell(joined(row.get("routeProof"))),
            cell(
                f"{row.get('authorityAction') or 'UNCLASSIFIED'} / {row.get('authorityClass') or 'unclassified'}"
                + (" / blocked" if row.get("authorityRepairEligible") is False else "")
            ),
            cell(joined(row.get("searchProgress"))),
            cell(joined(row.get("evidenceDepth"))),
            cell(row.get("harnessTransportClass") or "—"),
            cell(residential_probe_cell(state, row)),
            cell(residential_replay_cell(row)),
            cell(network_differential_cell(row)),
            cell(joined(row.get("latestLaneVerdicts"))),
            cell(row.get("dominantIssue") or "none"),
            cell(row.get("action") or "—"),
        ]) + " |")
    lines.extend([
        "",
        "Playback/route/candidate/history depth is owned by the latest Repair census. Harness transport overlays may refine providers already in the environment queue; exact failed-route network differentials are annotations only. Only a full provider replay with playable, identity-verified, contradiction-free media can promote functional status.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = render(load(args.status))
    args.output.write_text(text, encoding="utf-8")
    print(f"FIELD_PROVIDER_CENSUS_STATE_MARKDOWN output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
