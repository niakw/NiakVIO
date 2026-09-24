#!/usr/bin/env python3
"""Render a durable provider-state ledger from the full adaptive census.

The renderer deliberately separates "no current catalogue proof" from a broken
provider. Historical positive fixtures are preservation evidence, not permission
to call stale URLs healthy.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

GOOD = "playable_verified"

STATUS_META = {
    "FULL OK": ("🟢", "all declared semantic lanes have current verified playback"),
    "PARTIAL OK": ("🟡", "at least one declared lane has current verified playback"),
    "CANDIDATE OK": ("🟦", "an unpublished repair/reconstruction candidate was live/playback verified, but current published bytes have not reproduced it yet"),
    "ROUTE PROVEN": ("🟪", "live provider routes are qualified for the declared lanes, but terminal media is not currently verified"),
    "NO PROOF": ("🔵", "search/lookup ran but no content-specific chain was reached; keep rotating the corpus"),
    "CHAIN REACHED": ("🟣", "content/detail/episode/player chain was reached, but no terminal media is verified yet"),
    "HARNESS MISMATCH": ("🟧", "CI/Node was challenged but an ordinary browser session reached content; adapt the harness/client transport before touching provider code"),
    "CLIENT TRANSPORT GAP": ("🟧", "browser reachability is reproduced on GitHub and residential egress while native-like/direct transports fail; provider JS is not the causal owner and Core/client transport adaptation is required"),
    "HARNESS/ENV BLOCKED": ("🟫", "the GitHub CI/browser environment is challenged; native TV/mobile compatibility is unresolved and provider breakage is not established"),
    "PROVIDER NETWORK BLOCKED": ("🟤", "last meaningful provider/upstream request failed (HTTP/DNS/TLS/timeout); JS break is not established"),
    "PROVIDER JS BROKEN": ("🟠", "technical/provider implementation failure; repair and retest"),
    "PROVIDER JS FULLY BROKEN": ("🔴", "repeated technical failure without a retained positive proof; BRAIN LEARNING owns it"),
    "REGRESSION PROVIDER JS": ("🟣", "provider/lane was historically positive but current JS/runtime structure regressed"),
    "REGRESSION PROVIDER": ("🔴", "provider was historically positive but current upstream/network no longer answers successfully"),
    "DISABLED": ("⚫", "provider is intentionally lifecycle-disabled and excluded from automatic Retest/Repair"),
}

NO_PROOF_STAGES = {
    "provider_network_zero_result",
}
JS_BROKEN_STAGES = {
    "gate_runtime_plan_missing",
    "gate_source_family_unknown",
    "provider_zero_before_provider_network",
    "provider_runtime_hook_exception",
    "source_plan_core_metadata_leak",
    "runtime_error",
    "audit_error",
    "invalid_probe_output",
    "missing_tmdb_credential",
}
WAF_STAGES = {
    "provider_waf_challenge",
}
NETWORK_BROKEN_STAGES = {
    "provider_network_http_error",
    "provider_network_exception",
    "timeout",
}

HEALTHY_STATES = {"FULL OK", "PARTIAL OK"}
NON_ACTIONABLE_STATES = {"DISABLED"}
ENVIRONMENT_ONLY_STATES = {"HARNESS MISMATCH", "CLIENT TRANSPORT GAP", "HARNESS/ENV BLOCKED", "PROVIDER WAF/ANTIBOT"}

# These fields belong to one concrete WAF/residential overlay run. They must
# never be inherited by the next canonical census merely because a provider row
# was carried from the previous ledger.
TRANSPORT_OVERLAY_ROW_FIELDS = {
    "networkDifferentialClass",
    "networkDifferentialEvidence",
    "residentialProviderReplayClass",
    "residentialProviderReplayEvidence",
    "residentialProviderReplayPromoted",
    "residentialProviderReplayReclassified",
}


def is_symptomatic_status(status: str) -> bool:
    value = str(status or "")
    return value not in HEALTHY_STATES and value not in NON_ACTIONABLE_STATES


def is_repair_eligible_status(status: str) -> bool:
    value = str(status or "")
    return is_symptomatic_status(value) and value not in ENVIRONMENT_ONLY_STATES


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def lane_ok(row: dict[str, Any]) -> bool:
    return (
        str(row.get("status") or "") == GOOD
        and int(row.get("verified") or 0) > 0
        and int(row.get("contradictions") or 0) == 0
    )


def _lane_history(history: dict[str, Any], provider: str, lane: str) -> dict[str, Any]:
    providers = history.get("providers") if isinstance(history.get("providers"), dict) else {}
    row = providers.get(provider) if isinstance(providers.get(provider), dict) else {}
    lanes = row.get("lanes") if isinstance(row.get("lanes"), dict) else {}
    value = lanes.get(lane) if isinstance(lanes.get(lane), dict) else {}
    return value


def historical_proofs(history: dict[str, Any], provider: str, lane: str) -> list[dict[str, Any]]:
    row = _lane_history(history, provider, lane)
    values = row.get("proofs") if isinstance(row.get("proofs"), list) else []
    return [value for value in values if isinstance(value, dict) and isinstance(value.get("fixture"), dict)]


def historical_positive(history: dict[str, Any], provider: str) -> bool:
    providers = history.get("providers") if isinstance(history.get("providers"), dict) else {}
    row = providers.get(provider) if isinstance(providers.get(provider), dict) else {}
    lanes = row.get("lanes") if isinstance(row.get("lanes"), dict) else {}
    return any(historical_proofs(history, provider, lane) for lane in lanes)


def candidate_proofs(candidate_evidence: dict[str, Any], provider: str) -> list[dict[str, str]]:
    ci = candidate_evidence.get("ciEvidence") if isinstance(candidate_evidence.get("ciEvidence"), dict) else {}
    out: list[dict[str, str]] = []
    wanted = provider.strip().casefold()
    for key, row in ci.items():
        if (
            not isinstance(row, dict)
            or str(row.get("scope") or "") not in {"reconstruction-candidate", "repair-candidate"}
        ):
            continue
        verified = {str(v or "").strip().casefold() for v in (row.get("verifiedProviders") or []) if str(v or "").strip()}
        if wanted in verified:
            out.append({"key": str(key), "runId": str(row.get("runId") or ""), "note": str(row.get("note") or "")})
    return out

def merge_candidate_evidence(*values: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {"ciEvidence": {}}
    target = merged["ciEvidence"]
    for value in values:
        if not isinstance(value, dict):
            continue
        rows = value.get("ciEvidence") if isinstance(value.get("ciEvidence"), dict) else {}
        for key, row in rows.items():
            if isinstance(row, dict):
                target[str(key)] = row
    return merged


def _waf_rows(waf_browser_evidence: dict[str, Any], provider: str) -> list[dict[str, Any]]:
    wanted = str(provider or "").strip().casefold()
    return [
        row for row in waf_browser_evidence.get("rows") or []
        if isinstance(row, dict)
        and str(row.get("provider") or "").strip().casefold() == wanted
    ]


def harness_transport_diagnostic(
    waf_browser_evidence: dict[str, Any],
    provider: str,
) -> dict[str, Any]:
    """Summarize transport evidence without promoting it to playback proof.

    Residential exit-node evidence is intentionally identity-free: the report
    carries only bounded transport outcomes, never the private node name,
    Tailscale address or residential public IP.
    """
    rows = _waf_rows(waf_browser_evidence, provider)
    if not rows:
        return {
            "classification": "no-transport-evidence",
            "lanes": [],
            "evidence": [],
        }

    evidence: list[str] = []
    native_reached = False
    browser_only = False
    native_inconclusive = False
    all_challenged = True

    github_browser_reached = False
    residential_attempted = False
    residential_native_reached = False
    residential_browser_reached = False
    residential_inconclusive = False
    residential_all_challenged = True

    for row in rows:
        lane = str(row.get("lane") or "unknown").strip().casefold() or "unknown"
        okhttp = row.get("okHttpJvmProfile") if isinstance(row.get("okHttpJvmProfile"), dict) else {}
        okhttp_outcome = str(okhttp.get("outcome") or "")
        matrix = row.get("clientProfileMatrix") if isinstance(row.get("clientProfileMatrix"), list) else []
        tv_browser = next(
            (
                item for item in matrix
                if isinstance(item, dict)
                and str(item.get("profile") or "") == "nuvio-tv-ua-browser"
            ),
            {},
        )
        tv_browser_outcome = str(tv_browser.get("outcome") or "")
        default_outcome = str(row.get("outcome") or "")
        direct = row.get("directHttpProfile") if isinstance(row.get("directHttpProfile"), dict) else {}
        direct_outcome = str(direct.get("outcome") or "")

        if okhttp_outcome == "okhttp_jvm_content_reached":
            native_reached = True
            all_challenged = False
        elif okhttp_outcome == "okhttp_jvm_inconclusive":
            native_inconclusive = True
            all_challenged = False

        if default_outcome == "browser_content_reached" or tv_browser_outcome == "browser_content_reached":
            github_browser_reached = True
            all_challenged = False
            if okhttp_outcome != "okhttp_jvm_content_reached":
                browser_only = True

        if direct_outcome == "direct_http_content_reached":
            all_challenged = False

        residential = (
            row.get("residentialExitNodeProfile")
            if isinstance(row.get("residentialExitNodeProfile"), dict)
            else {}
        )
        residential_parts = ""
        if residential:
            residential_attempted = True
            residential_matrix = (
                residential.get("clientProfileMatrix")
                if isinstance(residential.get("clientProfileMatrix"), list)
                else []
            )
            residential_tv = next(
                (
                    item for item in residential_matrix
                    if isinstance(item, dict)
                    and str(item.get("profile") or "") == "nuvio-tv-ua-browser"
                ),
                {},
            )
            residential_tv_outcome = str(residential_tv.get("outcome") or "")
            residential_default = str(residential.get("outcome") or "")
            residential_okhttp = (
                residential.get("okHttpJvmProfile")
                if isinstance(residential.get("okHttpJvmProfile"), dict)
                else {}
            )
            residential_okhttp_outcome = str(residential_okhttp.get("outcome") or "")
            residential_direct = (
                residential.get("directHttpProfile")
                if isinstance(residential.get("directHttpProfile"), dict)
                else {}
            )
            residential_direct_outcome = str(residential_direct.get("outcome") or "")

            if residential_okhttp_outcome == "okhttp_jvm_content_reached":
                residential_native_reached = True
                residential_all_challenged = False
            if (
                residential_default == "browser_content_reached"
                or residential_tv_outcome == "browser_content_reached"
                or residential_direct_outcome == "direct_http_content_reached"
            ):
                residential_browser_reached = True
                residential_all_challenged = False
            residential_outcomes = {
                residential_default,
                residential_tv_outcome,
                residential_okhttp_outcome,
                residential_direct_outcome,
            }
            if any(
                value.endswith("_inconclusive")
                or value.endswith("_timeout")
                or value.endswith("_error")
                or value.endswith("_unavailable")
                for value in residential_outcomes
                if value
            ):
                residential_inconclusive = True
                residential_all_challenged = False

            residential_parts = (
                f", residential-browser={residential_default or 'unknown'}, "
                f"residential-tv-browser={residential_tv_outcome or 'unknown'}, "
                f"residential-okhttp={residential_okhttp_outcome or 'unknown'}, "
                f"residential-direct={residential_direct_outcome or 'unknown'}"
            )

        evidence.append(
            f"{lane}: browser={default_outcome or 'unknown'}, "
            f"tv-browser={tv_browser_outcome or 'unknown'}, "
            f"okhttp={okhttp_outcome or 'unknown'}, "
            f"direct={direct_outcome or 'unknown'}"
            f"{residential_parts}"
        )

    # Residential labels are DIFFERENTIAL labels, not a second way of
    # describing reachability already proved on the GitHub runner.
    if residential_native_reached and not native_reached:
        classification = "residential-exit-native-reachable"
    elif residential_browser_reached and not github_browser_reached and not native_reached:
        classification = "residential-exit-browser-reachable"
    elif native_reached:
        classification = "native-policy-reachable"
    elif github_browser_reached or browser_only:
        classification = "browser-profile-only"
    elif native_inconclusive:
        classification = "native-policy-inconclusive"
    elif residential_attempted and residential_all_challenged:
        classification = "residential-exit-all-challenged"
    elif residential_attempted and residential_inconclusive:
        classification = "residential-exit-inconclusive"
    elif all_challenged:
        classification = "github-all-transports-challenged"
    else:
        classification = "transport-mixed-unresolved"

    return {
        "classification": classification,
        "lanes": sorted({
            str(row.get("lane") or "").strip().casefold()
            for row in rows
            if str(row.get("lane") or "").strip()
        }),
        "evidence": evidence,
    }


def browser_harness_status(waf_browser_evidence: dict[str, Any], provider: str) -> str:
    """Classify CI/browser evidence without blaming provider code."""
    diagnostic = harness_transport_diagnostic(waf_browser_evidence, provider)
    if diagnostic["classification"] in {
        "residential-exit-native-reachable",
        "residential-exit-browser-reachable",
        "native-policy-reachable",
        "browser-profile-only",
        "native-policy-inconclusive",
        "transport-mixed-unresolved",
    }:
        return "HARNESS MISMATCH"
    return "HARNESS/ENV BLOCKED"


def _harness_action(status: str, transport_class: str) -> str:
    if status not in ENVIRONMENT_ONLY_STATES:
        return _action(status)
    return {
        "residential-exit-native-reachable": (
            "GitHub-hosted IP/environment differential confirmed by private residential exit; "
            "keep provider JS unchanged and reproduce with native transport/playback before any code blame"
        ),
        "residential-exit-browser-reachable": (
            "private residential exit improves reachability but native-like transport is not yet proven; "
            "treat as harness/client differential, not provider-code failure"
        ),
        "native-policy-reachable": (
            "replay provider-owned route with NuvioTV-like/native transport; "
            "do not mutate provider JS unless route/playback still fails causally"
        ),
        "browser-profile-only": (
            "compare browser/JS challenge resolution with native fetch/TLS/IP; "
            "provider JS mutation is not justified by CI challenge"
        ),
        "browser-profile-only-both-networks": (
            "browser succeeds on both GitHub and residential egress while direct/OkHttp fail; "
            "route to Core/client transport adaptation and LLM architecture diagnosis, never provider mutation"
        ),
        "native-policy-inconclusive": (
            "probe provider-owned search/detail route with representative native transport; "
            "current HTTP 200 is not playback proof"
        ),
        "residential-exit-all-challenged": (
            "private residential exit is also challenged; GitHub IP reputation alone does not explain the block"
        ),
        "residential-exit-inconclusive": (
            "private residential exit probe was inconclusive; keep provider code untouched until transport evidence is decisive"
        ),
        "github-all-transports-challenged": (
            "require real native-device/IP transport evidence before blaming provider code"
        ),
        "transport-mixed-unresolved": (
            "resolve harness/client transport differential before provider repair"
        ),
    }.get(transport_class, _action(status))


def route_proof(provider_overrides: dict[str, Any], provider: str) -> dict[str, Any] | None:
    patches = provider_overrides.get("provider_patches") if isinstance(provider_overrides.get("provider_patches"), dict) else {}
    patch = patches.get(provider) if isinstance(patches.get(provider), dict) else {}
    gate = patch.get("live_route_gate") if isinstance(patch.get("live_route_gate"), dict) else {}
    if str(gate.get("completion_state") or "") != "declared-types-qualified":
        return None
    required = [str(v or "").strip().casefold() for v in gate.get("required_types") or [] if str(v or "").strip()]
    validated = [str(v or "").strip().casefold() for v in gate.get("validated_types") or [] if str(v or "").strip()]
    missing = [str(v or "").strip().casefold() for v in gate.get("missing_types") or [] if str(v or "").strip()]
    live_routes = int(gate.get("live_validated_route_count") or 0)
    if not required or missing or not set(required).issubset(set(validated)) or live_routes <= 0:
        return None
    return {
        "requiredTypes": required,
        "validatedTypes": validated,
        "liveValidatedRouteCount": live_routes,
        "providerRequestCount": int(gate.get("provider_request_count") or 0),
    }

def _fixture_key(fixture: dict[str, Any]) -> tuple[str, str, str, int, int]:
    def integer(value: object) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0
    return (
        str(fixture.get("slug") or ""),
        str(fixture.get("tmdbId") or ""),
        str(fixture.get("mediaType") or fixture.get("category") or ""),
        integer(fixture.get("season")),
        integer(fixture.get("episode")),
    )


def _historical_proof_replayed(history: dict[str, Any], provider: str, row: dict[str, Any]) -> bool:
    lane = str(row.get("semantic_type") or "")
    proof_keys = {
        _fixture_key(proof.get("fixture") or {})
        for proof in historical_proofs(history, provider, lane)
    }
    if not proof_keys:
        return False
    for sample in row.get("samples") or []:
        if not isinstance(sample, dict):
            continue
        fixture = sample.get("fixture") if isinstance(sample.get("fixture"), dict) else {}
        if _fixture_key(fixture) in proof_keys:
            return True
    return False


def _technical_run_count(history: dict[str, Any], provider: str, rows: list[dict[str, Any]]) -> int:
    values = []
    for row in rows:
        lane = str(row.get("semantic_type") or "")
        state = _lane_history(history, provider, lane)
        values.append(int(state.get("consecutiveTechnicalRuns") or 0))
    return max(values or [0])


def provider_state(
    provider: str,
    rows: list[dict[str, Any]],
    history: dict[str, Any],
    candidate_evidence: dict[str, Any] | None = None,
    provider_overrides: dict[str, Any] | None = None,
    waf_browser_evidence: dict[str, Any] | None = None,
) -> str:
    if not rows:
        return "PROVIDER JS BROKEN"

    good = sum(1 for row in rows if lane_ok(row))
    if good == len(rows):
        return "FULL OK"
    if good:
        return "PARTIAL OK"

    stages = {
        str(row.get("debug_stage") or row.get("status") or "unknown")
        for row in rows
    }
    has_history = historical_positive(history, provider)
    has_candidate = bool(candidate_proofs(candidate_evidence or {}, provider))
    retained_route = route_proof(provider_overrides or {}, provider)
    repeated = _technical_run_count(history, provider, rows) >= 3
    if has_candidate:
        return "CANDIDATE OK"

    # A clean HTTP/runtime success with zero streams is a catalogue miss, not a
    # broken provider when we have never proved a matching work. If a retained
    # winning fixture was replayed and also stopped matching, that is the exact
    # regression-provider condition the ledger exists to expose.
    if stages and stages.issubset(NO_PROOF_STAGES):
        if has_history and any(_historical_proof_replayed(history, provider, row) for row in rows):
            return "REGRESSION PROVIDER"
        if any(str(row.get("debug_progress_stage") or "") == "chain_reached" for row in rows):
            return "CHAIN REACHED"
        if retained_route:
            return "ROUTE PROVEN"
        return "NO PROOF"

    if stages & JS_BROKEN_STAGES:
        if has_history:
            return "REGRESSION PROVIDER JS"
        return "PROVIDER JS FULLY BROKEN" if repeated else "PROVIDER JS BROKEN"

    if stages & WAF_STAGES:
        # GitHub/Node/browser challenge evidence is an environment signal, not a
        # provider-code verdict. Historical positives strengthen that conclusion
        # rather than turning it into a provider regression.
        return browser_harness_status(waf_browser_evidence or {}, provider)

    if stages & NETWORK_BROKEN_STAGES:
        if has_history:
            return "REGRESSION PROVIDER"
        # HTTP/DNS/timeout proves only that the current transport path failed.
        # Without a retained positive proof it does not establish a Provider JS
        # defect, even after repeated censuses.
        return "PROVIDER NETWORK BLOCKED"

    # Wrong content, unplayable output and other post-runtime failures are
    # implementation failures unless an older retained proof makes them a JS
    # regression.
    return "REGRESSION PROVIDER JS" if has_history else (
        "PROVIDER JS FULLY BROKEN" if repeated else "PROVIDER JS BROKEN"
    )


def dominant_issue(rows: list[dict[str, Any]]) -> str:
    failed = [row for row in rows if not lane_ok(row)]
    if not failed:
        return "none"
    counts = Counter(str(row.get("debug_stage") or row.get("status") or "unknown") for row in failed)
    return ", ".join(
        stage if count == 1 else f"{stage}×{count}"
        for stage, count in counts.most_common(3)
    )


def _history_label(history: dict[str, Any], provider: str, lane: str) -> str:
    proofs = historical_proofs(history, provider, lane)
    if not proofs:
        return "—"
    labels = []
    for proof in proofs[:2]:
        fixture = proof.get("fixture") or {}
        title = str(fixture.get("title") or fixture.get("label") or fixture.get("slug") or "").strip()
        if title and title not in labels:
            labels.append(title)
    return " / ".join(labels) or "retained proof"


def _search_progress(history: dict[str, Any], provider: str, row: dict[str, Any]) -> str:
    lane = str(row.get("semantic_type") or "")
    state = _lane_history(history, provider, lane)
    misses = state.get("misses") if isinstance(state.get("misses"), list) else []
    chain_hits = state.get("chainHits") if isinstance(state.get("chainHits"), list) else []
    this_run = int(row.get("sample_count") or 1)
    total_misses = len(misses)
    suffix = f" / {len(chain_hits)} retained chain hit" + ("s" if len(chain_hits) != 1 else "") if chain_hits else ""
    return f"{lane}: {this_run} works tested / {total_misses} retained misses{suffix}"


def _authority_row(authority_status: dict[str, Any], provider: str) -> dict[str, Any]:
    wanted = str(provider or "").strip().casefold()
    for row in authority_status.get("providers") or []:
        if (
            isinstance(row, dict)
            and str(row.get("provider") or "").strip().casefold() == wanted
        ):
            return row
    return {}


def _authority_fields(authority_status: dict[str, Any], provider: str) -> dict[str, Any]:
    row = _authority_row(authority_status, provider)
    if not row:
        # Renderer unit tests and historical local invocations may not carry an
        # authority artifact. Missing authority is "unknown", not an implicit
        # production block; main/Repair always provides the persisted arbiter.
        return {
            "authorityRepairEligible": True,
            "authorityAction": "UNCLASSIFIED",
            "authorityClass": "unclassified",
            "authorityConfidence": "unknown",
            "authorityReasons": [],
            "authorityKnown": False,
        }
    return {
        "authorityRepairEligible": row.get("repairEligible") is True,
        "authorityAction": str(row.get("action") or "UNCLASSIFIED"),
        "authorityClass": str(row.get("authorityClass") or "unknown"),
        "authorityConfidence": str(row.get("confidence") or "unknown"),
        "authorityReasons": [
            str(value) for value in row.get("reasons") or [] if str(value).strip()
        ],
        "authorityKnown": True,
    }


LIFECYCLE_DISABLED_ACTIONS = {
    "KEEP_DISABLED",
    "DISABLE_MANUAL_POLICY",
    "DISABLE_SOURCE_REMOVED",
    "DISABLE_AUTHORITY_EXHAUSTED",
}


def _lifecycle_disabled(authority: dict[str, Any]) -> bool:
    return (
        str(authority.get("authorityAction") or "") in LIFECYCLE_DISABLED_ACTIONS
        or str(authority.get("authorityClass") or "") in {
            "disabled", "manual-off", "source-removed", "stale-direct"
        }
    )


def _authority_action(status: str, transport_class: str, authority: dict[str, Any]) -> str:
    if authority.get("authorityRepairEligible") is not False:
        return _harness_action(status, transport_class)
    action = str(authority.get("authorityAction") or "")
    if action.startswith("REDISCOVER"):
        return (
            "Domain/authority rediscovery required before Repair; search remains "
            "supplementary evidence only and cannot authorize provider mutation"
        )
    if action in LIFECYCLE_DISABLED_ACTIONS:
        return (
            "provider lifecycle/authority blocks Repair; keep disabled until a "
            "new authoritative provider address/backend is qualified"
        )
    return "provider authority blocks Repair; resolve address/backend authority first"


def _ok_lanes_from_verdicts(verdicts: list[str]) -> set[str]:
    output: set[str] = set()
    for verdict in verdicts:
        text = str(verdict or "")
        if "=" not in text:
            continue
        lane, value = text.split("=", 1)
        if value.strip().upper().startswith("OK"):
            output.add(lane.strip().casefold())
    return output


def _carried_non_green_status(carried: dict[str, Any], provider: str, waf_browser_evidence: dict[str, Any]) -> str:
    issue = str(carried.get("dominantIssue") or "").casefold()
    candidate = bool(carried.get("candidateProof"))
    route = bool(carried.get("routeProof"))
    depth = {str(value or "").casefold() for value in carried.get("evidenceDepth") or []}
    historical = bool(carried.get("historicalProof"))

    if "provider_waf_challenge" in issue:
        return browser_harness_status(waf_browser_evidence, provider)
    if any(value in issue for value in ("provider_network_http_error", "provider_network_exception", "timeout")):
        return "REGRESSION PROVIDER" if historical else "PROVIDER NETWORK BLOCKED"
    if "provider_network_zero_result" in issue:
        if candidate:
            return "CANDIDATE OK"
        if any("chain_reached" in value for value in depth):
            return "CHAIN REACHED"
        if route:
            return "ROUTE PROVEN"
        return "NO PROOF"
    if any(value in issue for value in JS_BROKEN_STAGES):
        return "REGRESSION PROVIDER JS" if historical else "PROVIDER JS BROKEN"
    return "REGRESSION PROVIDER JS" if historical else "PROVIDER JS BROKEN"


def _reconcile_carried_green(
    carried: dict[str, Any],
    provider: str,
    waf_browser_evidence: dict[str, Any],
) -> dict[str, Any]:
    status = str(carried.get("status") or "")
    if status not in HEALTHY_STATES:
        return carried
    declared = {
        str(value or "").strip().casefold()
        for value in carried.get("declaredLanes") or []
        if str(value or "").strip()
    }
    verdicts = [str(value) for value in carried.get("latestLaneVerdicts") or []]
    if not verdicts:
        return carried
    ok_lanes = _ok_lanes_from_verdicts(verdicts)
    verified = [
        str(value or "").strip().casefold()
        for value in carried.get("currentVerifiedLanes") or []
        if str(value or "").strip().casefold() in ok_lanes
    ]
    carried["currentVerifiedLanes"] = verified

    if declared and set(verified) == declared:
        carried["status"] = "FULL OK"
    elif verified:
        carried["status"] = "PARTIAL OK"
    else:
        carried["status"] = _carried_non_green_status(carried, provider, waf_browser_evidence)
        carried["reconciledFromCarriedGreen"] = True
        carried["consistencyNote"] = "carried green contradicted by its latest lane verdict"
    carried["color"] = STATUS_META[str(carried["status"])][0]
    return carried


def _action(status: str) -> str:
    return {
        "FULL OK": "protect + replay retained proof",
        "PARTIAL OK": "protect green lanes; BRAIN checks missing lanes",
        "CANDIDATE OK": "replay candidate proof against current bytes; publish only after current verified media",
        "ROUTE PROVEN": "replay qualified route fixtures and finish terminal extraction/validation",
        "NO PROOF": "continue corpus proof search; BRAIN checks",
        "CHAIN REACHED": "finish terminal extractor/validation; do not promote before verified media",
        "HARNESS MISMATCH": "replay with representative TV/mobile transport; align harness headers/session/fetch stack before provider repair",
        "HARNESS/ENV BLOCKED": "compare GitHub Node/Chromium with native TV/mobile transport; provider JS mutation is not justified by CI challenge alone",
        "PROVIDER WAF/ANTIBOT": "legacy status: migrate to harness/environment classification",
        "PROVIDER NETWORK BLOCKED": "verify domain/upstream transport; repair JS only with implementation evidence",
        "PROVIDER JS BROKEN": "repair + retest; BRAIN checks",
        "PROVIDER JS FULLY BROKEN": "BRAIN LEARNING slot",
        "REGRESSION PROVIDER JS": "A/B against retained proof; restore JS/runtime",
        "REGRESSION PROVIDER": "re-run retained proof + verify upstream/provider state",
        "DISABLED": "lifecycle disabled; exclude from automatic Retest/Repair until authority re-enables it",
    }.get(status, "BRAIN checks")


def build_status_rows(
    report: dict[str, Any],
    history: dict[str, Any] | None = None,
    baseline: dict[str, Any] | None = None,
    candidate_evidence: dict[str, Any] | None = None,
    provider_overrides: dict[str, Any] | None = None,
    waf_browser_evidence: dict[str, Any] | None = None,
    authority_status: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    history = history or {}
    baseline = baseline or {}
    candidate_evidence = candidate_evidence or {}
    provider_overrides = provider_overrides or {}
    waf_browser_evidence = waf_browser_evidence or {}
    authority_status = authority_status or {}
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in report.get("rows") or []:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider_id") or "").strip().casefold()
        if provider:
            by[provider].append(row)

    expected = int(report.get("provider_count") or len(by))
    if len(by) != expected:
        raise ValueError(f"census provider mismatch: expected={expected} actual={len(by)}")

    out = []
    for provider, rows in by.items():
        ordered = sorted(rows, key=lambda row: str(row.get("semantic_type") or ""))
        status = provider_state(
            provider,
            ordered,
            history,
            candidate_evidence,
            provider_overrides,
            waf_browser_evidence,
        )
        declared = [str(row.get("semantic_type") or "") for row in ordered]
        verified = [str(row.get("semantic_type") or "") for row in ordered if lane_ok(row)]
        verdicts = []
        proof_labels = []
        candidate_labels = []
        progress = []
        evidence_depth = []
        for row in ordered:
            lane = str(row.get("semantic_type") or "")
            row_status = str(row.get("status") or "unknown")
            stage = str(row.get("debug_stage") or "")
            if lane_ok(row):
                verdicts.append(f"{lane}=OK")
            else:
                verdicts.append(f"{lane}={row_status}" + (f"/{stage}" if stage and stage != row_status else ""))
            label = _history_label(history, provider, lane)
            if label != "—":
                proof_labels.append(f"{lane}: {label}")
            progress.append(_search_progress(history, provider, row))
            evidence_depth.append(f"{lane}={str(row.get('debug_progress_stage') or 'none')}")
        candidate_labels = [f"run {x['runId']}" if x.get("runId") else x.get("key", "candidate") for x in candidate_proofs(candidate_evidence, provider)]
        route = route_proof(provider_overrides, provider)
        route_labels = ([f"{route['liveValidatedRouteCount']} live routes / {', '.join(route['validatedTypes'])}"] if route else [])
        harness_diag = (
            harness_transport_diagnostic(waf_browser_evidence, provider)
            if status in ENVIRONMENT_ONLY_STATES
            else {"classification": "not-applicable", "evidence": [], "lanes": []}
        )
        authority = _authority_fields(authority_status, provider)
        underlying_status = status
        if _lifecycle_disabled(authority):
            status = "DISABLED"
        status_repair_eligible = is_repair_eligible_status(status)
        out.append({
            "provider": provider,
            "status": status,
            "underlyingStatus": underlying_status if status == "DISABLED" else "",
            "color": STATUS_META[status][0],
            "declaredLanes": declared,
            "currentVerifiedLanes": verified,
            "historicalProof": proof_labels,
            "candidateProof": candidate_labels,
            "routeProof": route_labels,
            "latestLaneVerdicts": verdicts,
            "dominantIssue": dominant_issue(ordered),
            "searchProgress": progress,
            "evidenceDepth": evidence_depth,
            "harnessTransportClass": harness_diag["classification"],
            "harnessTransportEvidence": harness_diag["evidence"],
            **authority,
            "action": _authority_action(status, harness_diag["classification"], authority),
            "brainCheckRequired": is_symptomatic_status(status),
            "statusRepairEligible": status_repair_eligible,
            "repairEligible": status_repair_eligible and authority["authorityRepairEligible"],
            "testedThisRun": True,
        })

    # Unresolved-scope runs intentionally omit known FULL/PARTIAL providers.
    # Carry their previous ledger rows forward rather than manufacturing an
    # incomplete "global" table.
    current = {row["provider"] for row in out}
    for previous in baseline.get("providers") or []:
        if not isinstance(previous, dict):
            continue
        provider = str(previous.get("provider") or "").strip().casefold()
        if not provider or provider in current:
            continue
        carried = dict(previous)
        for field in TRANSPORT_OVERLAY_ROW_FIELDS:
            carried.pop(field, None)

        # Refresh dynamic retained evidence for carried rows instead of blindly
        # preserving a stale snapshot from an older renderer.
        declared = [
            str(value or "").strip().casefold()
            for value in carried.get("declaredLanes") or []
            if str(value or "").strip()
        ]
        proof_labels = []
        for lane in declared:
            label = _history_label(history, provider, lane)
            if label != "—":
                proof_labels.append(f"{lane}: {label}")
        carried["historicalProof"] = proof_labels
        carried["candidateProof"] = [
            f"run {x['runId']}" if x.get("runId") else x.get("key", "candidate")
            for x in candidate_proofs(candidate_evidence, provider)
        ]
        route = route_proof(provider_overrides, provider)
        carried["routeProof"] = (
            [f"{route['liveValidatedRouteCount']} live routes / {', '.join(route['validatedTypes'])}"]
            if route else []
        )

        carried = _reconcile_carried_green(carried, provider, waf_browser_evidence)
        carried_status = str(carried.get("status") or "")
        if carried_status == "PROVIDER WAF/ANTIBOT" or carried_status in ENVIRONMENT_ONLY_STATES:
            migrated = browser_harness_status(waf_browser_evidence, provider)
            diag = harness_transport_diagnostic(waf_browser_evidence, provider)
            carried["status"] = migrated
            carried["color"] = STATUS_META[migrated][0]
            carried["harnessTransportClass"] = diag["classification"]
            carried["harnessTransportEvidence"] = diag["evidence"]
            carried["action"] = _harness_action(migrated, diag["classification"])
        final_status = str(carried.get("status") or "")
        authority = _authority_fields(authority_status, provider)
        carried.update(authority)
        if _lifecycle_disabled(authority):
            carried["underlyingStatus"] = final_status
            final_status = "DISABLED"
            carried["status"] = final_status
            carried["color"] = STATUS_META[final_status][0]
        status_repair_eligible = is_repair_eligible_status(final_status)
        carried["brainCheckRequired"] = is_symptomatic_status(final_status)
        carried["statusRepairEligible"] = status_repair_eligible
        carried["repairEligible"] = status_repair_eligible and authority["authorityRepairEligible"]
        carried["action"] = _authority_action(
            final_status,
            str(carried.get("harnessTransportClass") or "not-applicable"),
            authority,
        )
        carried["testedThisRun"] = False
        out.append(carried)
    return out


def render(
    report: dict[str, Any],
    *,
    run_id: str,
    sha: str,
    history: dict[str, Any] | None = None,
    baseline: dict[str, Any] | None = None,
    candidate_evidence: dict[str, Any] | None = None,
    provider_overrides: dict[str, Any] | None = None,
    waf_browser_evidence: dict[str, Any] | None = None,
    authority_status: dict[str, Any] | None = None,
) -> str:
    rows = build_status_rows(
        report,
        history,
        baseline,
        candidate_evidence,
        provider_overrides,
        waf_browser_evidence,
        authority_status,
    )
    states = Counter(row["status"] for row in rows)
    symptomatic = sorted(row["provider"] for row in rows if row.get("brainCheckRequired") is True)
    repair_queue = sorted(row["provider"] for row in rows if row.get("repairEligible") is True)
    environment_queue = sorted(
        row["provider"] for row in rows
        if str(row.get("status") or "") in ENVIRONMENT_ONLY_STATES
        and row.get("authorityRepairEligible") is not False
    )
    harness_mismatch_queue = sorted(
        row["provider"] for row in rows
        if str(row.get("status") or "") == "HARNESS MISMATCH"
        and row.get("authorityRepairEligible") is not False
    )
    environment_blocked_queue = sorted(
        row["provider"] for row in rows
        if str(row.get("status") or "") == "HARNESS/ENV BLOCKED"
        and row.get("authorityRepairEligible") is not False
    )
    lifecycle_disabled_queue = sorted(
        row["provider"] for row in rows
        if _lifecycle_disabled(row)
    )
    authority_rediscovery_queue = sorted(
        row["provider"] for row in rows
        if row.get("brainCheckRequired") is True
        and row.get("authorityRepairEligible") is False
        and not _lifecycle_disabled(row)
    )
    authority_blocked_queue = sorted({
        *lifecycle_disabled_queue,
        *authority_rediscovery_queue,
    })
    short_sha = sha[:12] if sha else "unknown"
    scope = str(report.get("resolved_scope") or report.get("requested_scope") or "all")

    summary_order = [
        "FULL OK",
        "PARTIAL OK",
        "CANDIDATE OK",
        "ROUTE PROVEN",
        "NO PROOF",
        "CHAIN REACHED",
        "HARNESS MISMATCH",
        "HARNESS/ENV BLOCKED",
        "PROVIDER NETWORK BLOCKED",
        "PROVIDER JS BROKEN",
        "PROVIDER JS FULLY BROKEN",
        "REGRESSION PROVIDER JS",
        "REGRESSION PROVIDER",
    ]
    summary = " · ".join(
        f"{STATUS_META[state][0]} {states.get(state, 0)} {state}"
        for state in summary_order
        if states.get(state, 0)
    )

    lines = [
        "# Provider Census Status",
        "",
        "> Auto-generated by scripts/render_provider_census_status.py. Do not edit the table manually.",
        "",
        f"Latest provider census state: **{summary}** across **{len(rows)} providers**.",
        f"Evidence: run {run_id or 'local'} · SHA {short_sha} · scope **{scope}**.",
        f"Symptomatic providers: **{len(symptomatic)}** · automated repair queue: **{len(repair_queue)}** · lifecycle disabled: **{len(lifecycle_disabled_queue)}** · authority rediscovery: **{len(authority_rediscovery_queue)}** · harness mismatch: **{len(harness_mismatch_queue)}** · environment blocked: **{len(environment_blocked_queue)}**.",
        "",
        "## Status semantics",
        "",
    ]
    for state in summary_order:
        emoji, meaning = STATUS_META[state]
        lines.append(f"- {emoji} **{state}** — {meaning}.")
    lines.extend([
        "",
        "**Important:** provider_network_zero_result is not a healthy-provider verdict. Search/lookup-only stays NO PROOF only when no retained positive/candidate/route proof exists; "
        "a content-specific detail/episode/player chain becomes CHAIN REACHED; ROUTE PROVEN preserves qualified live provider routes without pretending terminal media worked; "
        "CANDIDATE OK preserves verified playback from an unpublished repair/reconstruction candidate that current published bytes have not reproduced; PARTIAL OK still requires at least one verified playable lane. "
        "A carried row is last-known evidence, not a claim that this scoped run re-probed it. Repair eligibility is the intersection of runtime status and provider address/backend authority.",
        "",
        "| Provider | Status | Run | Declared lanes | Verified lanes | Retained proof | Candidate proof | Route proof | Authority | Corpus progress | Evidence depth | Harness transport | Latest lane verdicts | Dominant issue | Next action |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ])

    state_order = {
        "REGRESSION PROVIDER JS": 0,
        "REGRESSION PROVIDER": 1,
        "PROVIDER JS FULLY BROKEN": 2,
        "PROVIDER JS BROKEN": 3,
        "HARNESS MISMATCH": 4,
        "HARNESS/ENV BLOCKED": 5,
        "CHAIN REACHED": 6,
        "ROUTE PROVEN": 7,
        "CANDIDATE OK": 8,
        "NO PROOF": 9,
        "PARTIAL OK": 10,
        "FULL OK": 11,
    }
    entries = []
    for row in rows:
        status = row["status"]
        line = (
            f"| **{row['provider']}** | {row['color']} **{status}** | "
            f"{'tested' if row.get('testedThisRun') else 'carried'} | "
            f"{', '.join(row['declaredLanes']) or '—'} | "
            f"{', '.join(row['currentVerifiedLanes']) or '—'} | "
            f"{'; '.join(row['historicalProof']) or '—'} | "
            f"{'; '.join(row.get('candidateProof') or []) or '—'} | "
            f"{'; '.join(row.get('routeProof') or []) or '—'} | "
            f"{row.get('authorityAction') or 'UNCLASSIFIED'} / {row.get('authorityClass') or 'unclassified'}"
            f"{' / blocked' if row.get('authorityRepairEligible') is False else ''} | "
            f"{'; '.join(row['searchProgress']) or '—'} | "
            f"{'; '.join(row.get('evidenceDepth') or []) or '—'} | "
            f"{row.get('harnessTransportClass') if row.get('harnessTransportClass') != 'not-applicable' else '—'} | "
            f"{'; '.join(row['latestLaneVerdicts']) or '—'} | "
            f"{row['dominantIssue']} | {row['action']} |"
        )
        entries.append((state_order.get(status, 9), row["provider"], line))

    lines.extend(line for _, _, line in sorted(entries))
    lines.extend([
        "",
        "The source JSON is the exact provider-v3-quick-yield.json from the same census. "
        "Retained proof/search memory is automation/provider-census-proof-history.json; Repair authority is automation/provider-authority-status.json.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, default=Path("PROVIDER_CENSUS_STATUS.md"))
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--history", type=Path, default=Path("automation/provider-census-proof-history.json"))
    parser.add_argument("--baseline-status", type=Path, default=Path("automation/provider-census-status.json"))
    parser.add_argument("--candidate-evidence", type=Path, default=Path("automation/provider-history-evidence-v1.json"))
    parser.add_argument("--repair-candidate-evidence", type=Path, default=Path("automation/provider-repair-candidate-evidence.json"))
    parser.add_argument("--provider-overrides", type=Path, default=Path("provider-overrides.json"))
    parser.add_argument("--waf-browser-evidence", type=Path, default=Path("automation/provider-waf-browser-session-latest.json"))
    parser.add_argument("--authority-status", type=Path, default=Path("automation/provider-authority-status.json"))
    parser.add_argument("--run-id", default="")
    parser.add_argument("--sha", default="")
    args = parser.parse_args()

    report = load(args.report)
    history = load(args.history) if args.history.is_file() else {}
    baseline = load(args.baseline_status) if args.baseline_status.is_file() else {}
    candidate_evidence = load(args.candidate_evidence) if args.candidate_evidence.is_file() else {}
    repair_candidate_evidence = (
        load(args.repair_candidate_evidence)
        if args.repair_candidate_evidence.is_file()
        else {}
    )
    candidate_evidence = merge_candidate_evidence(candidate_evidence, repair_candidate_evidence)
    provider_overrides = load(args.provider_overrides) if args.provider_overrides.is_file() else {}
    waf_browser_evidence = load(args.waf_browser_evidence) if args.waf_browser_evidence.is_file() else {}
    authority_status = load(args.authority_status) if args.authority_status.is_file() else {}
    rows = build_status_rows(
        report,
        history,
        baseline,
        candidate_evidence,
        provider_overrides,
        waf_browser_evidence,
        authority_status,
    )
    args.output.write_text(
        render(
            report,
            run_id=str(args.run_id),
            sha=str(args.sha),
            history=history,
            baseline=baseline,
            candidate_evidence=candidate_evidence,
            provider_overrides=provider_overrides,
            waf_browser_evidence=waf_browser_evidence,
            authority_status=authority_status,
        ),
        encoding="utf-8",
    )
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schemaVersion": 3,
            "runId": str(args.run_id),
            "triggerSha": str(args.sha),
            "providers": rows,
            "counts": dict(sorted(Counter(row["status"] for row in rows).items())),
            "symptomaticProviders": sorted(
                row["provider"] for row in rows if row.get("brainCheckRequired") is True
            ),
            "brainQueue": sorted(
                row["provider"] for row in rows if row.get("brainCheckRequired") is True
            ),
            "repairQueue": sorted(
                row["provider"] for row in rows if row.get("repairEligible") is True
            ),
            # Compatibility aggregate: all symptoms excluded by authority/lifecycle.
            "authorityBlockedQueue": sorted(
                row["provider"] for row in rows
                if row.get("brainCheckRequired") is True
                and row.get("authorityRepairEligible") is False
            ),
            "lifecycleDisabledQueue": sorted(
                row["provider"] for row in rows
                if _lifecycle_disabled(row)
            ),
            "authorityRediscoveryQueue": sorted(
                row["provider"] for row in rows
                if row.get("brainCheckRequired") is True
                and row.get("authorityRepairEligible") is False
                and not _lifecycle_disabled(row)
            ),
            # Backward-compatible combined transport queue. New consumers should
            # use the two exact queues below instead of interpreting this name as
            # "environment blocked".
            "environmentQueue": sorted(
                row["provider"] for row in rows
                if str(row.get("status") or "") in ENVIRONMENT_ONLY_STATES
                and row.get("authorityRepairEligible") is not False
            ),
            "harnessMismatchQueue": sorted(
                row["provider"] for row in rows
                if str(row.get("status") or "") == "HARNESS MISMATCH"
                and row.get("authorityRepairEligible") is not False
            ),
            "environmentBlockedQueue": sorted(
                row["provider"] for row in rows
                if str(row.get("status") or "") == "HARNESS/ENV BLOCKED"
                and row.get("authorityRepairEligible") is not False
            ),
            "harnessQueue": sorted(
                row["provider"] for row in rows
                if str(row.get("status") or "") in ENVIRONMENT_ONLY_STATES
                and row.get("authorityRepairEligible") is not False
            ),
        }
        args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PROVIDER_CENSUS_STATUS_WRITTEN output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
