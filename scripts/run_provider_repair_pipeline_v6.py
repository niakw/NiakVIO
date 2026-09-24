#!/usr/bin/env python3
"""Canonical proof-first recognition/correction pipeline for unresolved providers."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from current_provider_scope import active_provider_ids, visible_provider_ids

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
DEFAULT_SKIP = ROOT / "automation" / "provider-repair-skip.json"
TARGET_REPORT = ROOT / "automation" / "provider-route-recovery-v6-targeted.json"
MERGED_REPORT = ROOT / "automation" / "provider-route-recovery-v6.json"
YIELD_REPORT = ROOT / "automation" / "provider-repair-yield-v6.json"
SUMMARY = ROOT / "automation" / "provider-repair-v6-summary.json"
BRAIN_REPAIR = ROOT / "automation" / "provider-brain-repair-latest.json"
QUICK_YIELD = ROOT / "provider-v3-quick-yield.json"
PORTFOLIO_BASELINE = ROOT / "automation" / "provider-repair-portfolio-baseline.json"
PORTFOLIO_CANDIDATE = ROOT / "automation" / "provider-repair-portfolio-candidate.json"
PORTFOLIO_RETRY = ROOT / "automation" / "provider-repair-portfolio-retry.json"
PORTFOLIO_LOSSES = ROOT / "automation" / "provider-repair-portfolio-losses.json"
DISPOSITION = ROOT / "automation" / "provider-repair-disposition.json"
HUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"
RUNTIME_PLAN_LKG = Path(os.environ.get("RUNNER_TEMP") or (ROOT / "automation")) / "provider-runtime-plan-lkg-v1.json"
CENSUS_STATUS = ROOT / "automation" / "provider-census-status.json"
CENSUS_HISTORY = ROOT / "automation" / "provider-census-proof-history.json"
CENSUS_MD = ROOT / "PROVIDER_CENSUS_STATUS.md"
CENSUS_POST_REPAIR = ROOT / "automation" / "provider-census-post-repair.json"
REPAIR_CANDIDATE_EVIDENCE = ROOT / "automation" / "provider-repair-candidate-evidence.json"
REPAIR_MATERIALIZATION_SCOPE = ROOT / "automation" / "provider-repair-materialization-scope.json"
AUTHORITY_STATUS = ROOT / "automation" / "provider-authority-status.json"
WAF_STATUS = ROOT / "automation" / "provider-waf-browser-session-latest.json"
CURRENT_OVERRIDES_SNAPSHOT = RUNTIME_PLAN_LKG.parent / "provider-overrides-pre-repair.json"
CENSUS_ENVIRONMENT_ONLY = {"HARNESS MISMATCH", "CLIENT TRANSPORT GAP", "HARNESS/ENV BLOCKED", "PROVIDER WAF/ANTIBOT"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def unresolved_target_scope(
    active_catalogue: list[str],
    skipped: set[str],
    requested: set[str],
    disposition: dict[str, Any] | None = None,
    current_verified: set[str] | None = None,
    census: dict[str, Any] | None = None,
    authority_blocked: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return only providers currently marked symptomatic by the census.

    The durable census ledger is the automatic Repair authority. Explicit
    requests are also intersected with that queue, so a stable FULL/PARTIAL
    provider is never re-probed merely because an old disposition says repair.
    """
    if isinstance(census, dict):
        queue_values = census.get("repairQueue")
        if not isinstance(queue_values, list):
            rows = {
                cid(row.get("provider")): row
                for row in census.get("providers") or []
                if isinstance(row, dict) and cid(row.get("provider"))
            }
            queue_values = [
                value for value in census.get("brainQueue") or []
                if str((rows.get(cid(value)) or {}).get("status") or "") not in CENSUS_ENVIRONMENT_ONLY
            ]
        queue = {cid(value) for value in queue_values or [] if cid(value)}
        selected = (set(requested) & queue) if requested else queue
        hard_blocked = {
            cid(value) for value in (authority_blocked or set()) if cid(value)
        }
        # Current-byte census is stronger authority than provider-repair-skip.
        # A provider reopened by repairQueue must be re-probed even when an old
        # exact-byte optimization still names it. Independent authority blockers
        # remain a hard prerequisite and are never bypassed here.
        targets = [
            provider
            for provider in active_catalogue
            if provider in selected and provider not in hard_blocked
        ]
        excluded = [
            provider
            for provider in active_catalogue
            if provider not in selected or provider in hard_blocked
        ]
        return targets, excluded

    # Compatibility fallback for callers/tests without a census. Production main
    # always supplies census=... and therefore never uses disposition as authority.
    disposition = disposition or {"providers": []}
    state_by_provider = {
        cid(row.get("provider")): str(row.get("routeDataState") or "").strip().casefold()
        for row in disposition.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }
    if requested:
        selected = set(requested)
    else:
        selected = {
            provider
            for provider in active_catalogue
            if state_by_provider.get(provider) != "on"
        }
        if current_verified is not None:
            selected.update(
                provider
                for provider in active_catalogue
                if state_by_provider.get(provider) == "on"
                and provider not in current_verified
            )
    targets = [provider for provider in active_catalogue if provider in selected and provider not in skipped]
    excluded = [
        provider for provider in active_catalogue
        if not requested and provider not in selected
    ]
    return targets, excluded


def run(
    *args: str,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> None:
    print("FIELD_PROVIDER_REPAIR_CMD " + " ".join(args), flush=True)
    subprocess.run(
        list(args),
        cwd=ROOT,
        env=env or os.environ.copy(),
        check=True,
        timeout=timeout,
    )


def route_recovery_outer_timeout(
    provider_count: int,
    workers: int,
    request_timeout: int,
    attempts: int,
) -> int:
    """Wall-clock bound for a concurrent route-recovery cohort."""
    workers = max(1, int(workers))
    batches = max(1, (max(1, int(provider_count)) + workers - 1) // workers)
    per_attempt = max(15, min(int(request_timeout), 120))
    budget = batches * per_attempt * max(1, int(attempts)) + 120
    return max(300, min(900, budget))


def portfolio_probe_timeout(provider_count: int) -> int:
    """Bound targeted quick-yield probes independently of catalogue size."""
    batches = max(1, (max(1, int(provider_count)) + 11) // 12)
    return max(180, min(600, batches * 90 + 120))


def capture_portfolio_yield(destination: Path, providers: list[str] | None = None) -> dict[str, Any]:
    command = [sys.executable, "scripts/audit_provider_quick_yield.py"]
    for provider in providers or []:
        command.extend(["--provider", provider])
    run(*command, timeout=portfolio_probe_timeout(len(providers or [])))
    if not QUICK_YIELD.exists():
        raise RuntimeError("quick-yield audit did not produce provider-v3-quick-yield.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(QUICK_YIELD, destination)
    report = load(destination)
    print(
        "FIELD_PROVIDER_REPAIR_PORTFOLIO "
        f"file={destination.name} raw={int(report.get('raw_provider_count') or 0)} "
        f"playable={int(report.get('playable_provider_count') or 0)} "
        f"verified={int(report.get('verified_provider_count') or 0)} "
        f"wrong={int(report.get('wrong_content_provider_count') or 0)}",
        flush=True,
    )
    return report


def reapply_transport_overlay(*, phase: str) -> None:
    """Keep durable WAF/Tailscale transport authority across internal renders."""
    if not CENSUS_STATUS.exists() or not WAF_STATUS.exists():
        return
    run_id = str(os.environ.get("GITHUB_RUN_ID") or "local")
    sha = str(os.environ.get("GITHUB_SHA") or "")
    tmp = Path(os.environ.get("RUNNER_TEMP") or (ROOT / "automation")) / f"provider-census-transport-{phase}.json"
    cmd = [
        sys.executable,
        "scripts/merge_waf_census_transport.py",
        "--status", str(CENSUS_STATUS.relative_to(ROOT)),
        "--waf", str(WAF_STATUS.relative_to(ROOT)),
        "--output", str(tmp),
        "--run-id", f"{run_id}-{phase}-transport",
        "--sha", sha or phase,
    ]
    if AUTHORITY_STATUS.exists():
        cmd.extend(["--authority-status", str(AUTHORITY_STATUS.relative_to(ROOT))])
    run(*cmd)
    shutil.copyfile(tmp, CENSUS_STATUS)
    run(
        sys.executable,
        "scripts/render_provider_census_status_from_state.py",
        "--status", str(CENSUS_STATUS.relative_to(ROOT)),
        "--output", str(CENSUS_MD.relative_to(ROOT)),
    )
    state = load(CENSUS_STATUS)
    print(
        "FIELD_PROVIDER_REPAIR_TRANSPORT_OVERLAY "
        f"phase={phase} repair={len(state.get('repairQueue') or [])} "
        f"environment={len(state.get('environmentQueue') or [])}",
        flush=True,
    )


def refresh_census(report_path: Path, *, phase: str) -> dict[str, Any]:
    """Merge a targeted current-byte report into the durable global census."""
    run_id = str(os.environ.get("GITHUB_RUN_ID") or "local")
    sha = str(os.environ.get("GITHUB_SHA") or "")
    if CENSUS_HISTORY.exists():
        run(
            sys.executable,
            "scripts/update_provider_census_proof_history.py",
            str(report_path.relative_to(ROOT)),
            "--history", str(CENSUS_HISTORY.relative_to(ROOT)),
            "--run-id", f"{run_id}-{phase}",
            "--sha", sha or phase,
        )
    run(
        sys.executable,
        "scripts/render_provider_census_status.py",
        str(report_path.relative_to(ROOT)),
        "--output", str(CENSUS_MD.relative_to(ROOT)),
        "--json-output", str(CENSUS_STATUS.relative_to(ROOT)),
        "--history", str(CENSUS_HISTORY.relative_to(ROOT)),
        "--baseline-status", str(CENSUS_STATUS.relative_to(ROOT)),
        *(
            ["--waf-browser-evidence", str(WAF_STATUS.relative_to(ROOT))]
            if WAF_STATUS.exists() else []
        ),
        *(
            ["--authority-status", str(AUTHORITY_STATUS.relative_to(ROOT))]
            if AUTHORITY_STATUS.exists() else []
        ),
        "--run-id", f"{run_id}-{phase}",
        "--sha", sha or phase,
    )
    reapply_transport_overlay(phase=phase)
    if (ROOT / "scripts/build_provider_repair_batch_plan.py").exists():
        run(
            sys.executable,
            "scripts/build_provider_repair_batch_plan.py",
            "--status", str(CENSUS_STATUS.relative_to(ROOT)),
            "--overrides", "provider-overrides.json",
            "--output", "automation/provider-repair-batch-plan-latest.json",
        )
    state = load(CENSUS_STATUS)
    print(
        "FIELD_PROVIDER_REPAIR_CENSUS "
        f"phase={phase} symptomatic={len(state.get('symptomaticProviders') or state.get('brainQueue') or [])} "
        f"repair_queue={len(state.get('repairQueue') or [])} "
        f"environment={len(state.get('environmentQueue') or [])}",
        flush=True,
    )
    return state


def persist_repair_candidate_evidence(report: dict[str, Any], *, run_id: str, sha: str) -> dict[str, Any]:
    """Keep verified sandbox Repair outcomes without calling them current bytes."""
    verified_lanes: dict[str, set[str]] = {}
    for row in report.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if (
            str(row.get("status") or "") != "playable_verified"
            or int(row.get("verified") or 0) <= 0
            or int(row.get("contradictions") or 0) != 0
        ):
            continue
        provider = cid(row.get("provider_id"))
        lane = str(row.get("semantic_type") or "").strip().casefold()
        if provider and lane:
            verified_lanes.setdefault(provider, set()).add(lane)

    existing = load(REPAIR_CANDIDATE_EVIDENCE) if REPAIR_CANDIDATE_EVIDENCE.exists() else {
        "schemaVersion": 1,
        "ciEvidence": {},
    }
    existing["schemaVersion"] = 1
    entries = existing.setdefault("ciEvidence", {})
    if not isinstance(entries, dict):
        entries = {}
        existing["ciEvidence"] = entries

    if verified_lanes:
        key = f"repair:{run_id}"
        entries[key] = {
            "scope": "repair-candidate",
            "runId": run_id,
            "sha": sha,
            "verifiedProviders": sorted(verified_lanes),
            "verifiedLanes": {
                provider: sorted(lanes)
                for provider, lanes in sorted(verified_lanes.items())
            },
            "note": (
                "identity-safe playable Repair candidate; provider/Core bytes were "
                "ephemeral and must be replayed against persisted main before current promotion"
            ),
        }
        repair_keys = [
            value for value, row in entries.items()
            if isinstance(row, dict) and str(row.get("scope") or "") == "repair-candidate"
        ]
        for stale in repair_keys[:-32]:
            entries.pop(stale, None)

    REPAIR_CANDIDATE_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    REPAIR_CANDIDATE_EVIDENCE.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return existing


def render_persisted_byte_census(
    current_report: Path,
    *,
    phase: str,
    provider_overrides: Path,
) -> dict[str, Any]:
    """Render current status from persisted-byte evidence plus candidate hints."""
    run_id = str(os.environ.get("GITHUB_RUN_ID") or "local")
    sha = str(os.environ.get("GITHUB_SHA") or "")
    run(
        sys.executable,
        "scripts/render_provider_census_status.py",
        str(current_report.relative_to(ROOT)),
        "--output", str(CENSUS_MD.relative_to(ROOT)),
        "--json-output", str(CENSUS_STATUS.relative_to(ROOT)),
        "--history", str(CENSUS_HISTORY.relative_to(ROOT)),
        "--baseline-status", str(CENSUS_STATUS.relative_to(ROOT)),
        "--repair-candidate-evidence", str(REPAIR_CANDIDATE_EVIDENCE.relative_to(ROOT)),
        "--provider-overrides", str(provider_overrides),
        *(
            ["--waf-browser-evidence", str(WAF_STATUS.relative_to(ROOT))]
            if WAF_STATUS.exists() else []
        ),
        *(
            ["--authority-status", str(AUTHORITY_STATUS.relative_to(ROOT))]
            if AUTHORITY_STATUS.exists() else []
        ),
        "--run-id", f"{run_id}-{phase}",
        "--sha", sha or phase,
    )
    reapply_transport_overlay(phase=phase)
    if (ROOT / "scripts/build_provider_repair_batch_plan.py").exists():
        run(
            sys.executable,
            "scripts/build_provider_repair_batch_plan.py",
            "--status", str(CENSUS_STATUS.relative_to(ROOT)),
            "--overrides", "provider-overrides.json",
            "--output", "automation/provider-repair-batch-plan-latest.json",
        )
    state = load(CENSUS_STATUS)
    print(
        "FIELD_PROVIDER_REPAIR_CENSUS "
        f"phase={phase} symptomatic={len(state.get('symptomaticProviders') or state.get('brainQueue') or [])} "
        f"repair_queue={len(state.get('repairQueue') or [])} "
        f"environment={len(state.get('environmentQueue') or [])}",
        flush=True,
    )
    return state



def effective_repair_materialization_scope(
    scope: dict[str, Any],
    target_providers: list[str],
    *,
    targeted_only: bool,
) -> dict[str, Any]:
    """Narrow sandbox materialization to the Repair cohort when publication is off.

    Route-recovery migrations can legitimately touch global/provider-map inputs in
    the candidate worktree. Automatic Repair is non-publishing, so rebuilding the
    entire catalogue only tests unrelated bytes and scales linearly with catalogue
    size. Explicit Force retains the full selector authority.
    """
    source_mode = str(scope.get("mode") or "").strip().casefold()
    if source_mode not in {"all", "providers", "none"}:
        raise RuntimeError(f"invalid provider materialization mode: {source_mode!r}")
    providers = sorted({cid(value) for value in scope.get("providers") or [] if cid(value)})
    reasons = list(scope.get("reasons") or [])
    narrowed = False
    if targeted_only and source_mode in {"all", "providers"}:
        targets = {cid(value) for value in target_providers if cid(value)}
        providers = sorted(targets if source_mode == "all" else (set(providers) & targets))
        source_mode = "providers" if providers else "none"
        reasons.append("automatic-repair:nonpublishing-target-cohort-only")
        narrowed = True
    return {
        "mode": source_mode,
        "providers": providers,
        "reasons": reasons,
        "narrowed": narrowed,
        "sourceMode": str(scope.get("mode") or "").strip().casefold(),
    }


def rematerialize_repair_scope(
    target_providers: list[str],
    *,
    targeted_only: bool,
) -> dict[str, Any]:
    """Rebuild only candidate bytes relevant to this Repair execution."""
    run(
        sys.executable,
        "scripts/select_provider_materialization_scope.py",
        "--base", "HEAD",
        "--head", "HEAD",
        "--output", str(REPAIR_MATERIALIZATION_SCOPE.relative_to(ROOT)),
    )
    selected = effective_repair_materialization_scope(
        load(REPAIR_MATERIALIZATION_SCOPE),
        target_providers,
        targeted_only=targeted_only,
    )
    mode = str(selected.get("mode") or "")
    providers = list(selected.get("providers") or [])
    if mode == "all":
        run(sys.executable, "scripts/materialize_provider_v3_all.py")
    elif mode == "providers":
        if not providers:
            raise RuntimeError("providers materialization mode without providers")
        for provider in providers:
            run(sys.executable, "scripts/materialize_provider_v3_one.py", provider)
        reconcile = [sys.executable, "scripts/reconcile_targeted_provider_publication.py"]
        for provider in providers:
            reconcile.extend(["--provider", provider])
        run(*reconcile)
    elif mode != "none":
        raise RuntimeError(f"invalid provider materialization mode: {mode!r}")
    print(
        "FIELD_PROVIDER_REPAIR_MATERIALIZATION "
        f"mode={mode} source_mode={selected.get('sourceMode')} "
        f"narrowed={str(bool(selected.get('narrowed'))).lower()} "
        f"providers={len(providers)} ids={','.join(providers) or '-'}",
        flush=True,
    )
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("repair", "learn", "force"), default="repair")
    parser.add_argument("--skip-file", type=Path, default=DEFAULT_SKIP.relative_to(ROOT))
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--workers", type=int, default=0, help="0=auto-scale from unresolved provider count")
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--allow-upstream-positive-loss", action="store_true")
    args = parser.parse_args()

    manifest = load(MANIFEST)
    skip_path = args.skip_file if args.skip_file.is_absolute() else ROOT / args.skip_file
    skip_cfg = load(skip_path)
    skipped = {cid(value) for value in (skip_cfg.get("providers") or {}).keys() if cid(value)}
    catalogue_rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and cid(row.get("id"))]
    catalogue = [cid(row.get("id")) for row in catalogue_rows]
    if len(catalogue) != len(set(catalogue)):
        raise SystemExit("provider catalogue contains duplicate ids")
    visible = visible_provider_ids()
    if set(catalogue) != visible:
        raise SystemExit(
            "manifest/folder provider identity mismatch: "
            f"manifest_only={sorted(set(catalogue)-visible)} folder_only={sorted(visible-set(catalogue))}"
        )
    active_ids = active_provider_ids()
    active_catalogue = [cid(row.get("id")) for row in catalogue_rows if cid(row.get("id")) in active_ids]
    matrix = load(HUB_MATRIX)
    matrix_ids = {cid(row.get("manifestId") or row.get("provider")) for row in matrix.get("rows") or [] if isinstance(row, dict) and cid(row.get("manifestId") or row.get("provider"))}
    if matrix_ids != active_ids:
        print(
            "FIELD_PROVIDER_REPAIR_MATRIX_STALE "
            f"matrix_only={','.join(sorted(matrix_ids-active_ids)) or '-'} "
            f"active_only={','.join(sorted(active_ids-matrix_ids)) or '-'}",
            flush=True,
        )
    requested = {cid(value) for value in args.provider if cid(value)}
    unknown = sorted(requested - set(catalogue))
    if unknown:
        raise SystemExit("unknown providers: " + ",".join(unknown))
    disabled_requested = sorted(requested - set(active_catalogue))
    if disabled_requested:
        raise SystemExit("requested providers are explicitly OFF/disabled: " + ",".join(disabled_requested))

    disposition = load(DISPOSITION) if DISPOSITION.exists() else {"providers": []}
    attempts = max(1, min(int(args.attempts), 4))
    if not CENSUS_STATUS.exists():
        raise SystemExit("provider census status missing; run census before Repair")
    census = load(CENSUS_STATUS)

    # Address/identity authority is a prerequisite for site-dependent Repair.
    # Search-only or stale-domain providers are rediscovered by Domain first;
    # deterministic API/backend providers remain eligible without a homepage.
    run(sys.executable, "scripts/classify_provider_authority.py")
    authority = load(AUTHORITY_STATUS)
    authority_rows = {
        cid(row.get("provider")): row
        for row in authority.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }
    authority_blocked = {
        provider for provider, row in authority_rows.items()
        if row.get("repairEligible") is not True
    }
    skipped.update(authority_blocked)
    if requested & authority_blocked:
        blocked = sorted(requested & authority_blocked)
        print(
            "FIELD_PROVIDER_REPAIR_AUTHORITY_BLOCKED providers=" + ",".join(blocked),
            flush=True,
        )

    # Census is the only automatic symptom authority; the provider-authority
    # arbiter is an independent prerequisite gate before network Repair.
    # current repairQueue, merge those fresh observations into the ledger, then
    # repair only providers that remain symptomatic.
    initial_targets, auto_excluded_green = unresolved_target_scope(
        active_catalogue,
        skipped,
        requested,
        disposition,
        census=census,
        authority_blocked=authority_blocked,
    )
    if not initial_targets:
        summary = {
            "schemaVersion": 12,
            "mode": args.mode,
            "publicationAllowed": False,
            "mainWritesAllowed": False,
            "selectionAuthority": "provider-census-status.json:repairQueue + provider-authority-status.json",
            "authorityBlockedProviders": sorted(authority_blocked),
            "targetedProviderCount": 0,
            "targetedProviders": [],
            "censusStatusUpdated": False,
            "preservationGatePassed": True,
        }
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("FIELD_PROVIDER_REPAIR_EMPTY census_repair_queue=0", flush=True)
        return 0

    baseline_portfolio = capture_portfolio_yield(PORTFOLIO_BASELINE, initial_targets)
    census = refresh_census(PORTFOLIO_BASELINE, phase="pre-repair")
    shutil.copyfile(ROOT / "provider-overrides.json", CURRENT_OVERRIDES_SNAPSHOT)
    targets, auto_excluded_green = unresolved_target_scope(
        active_catalogue,
        skipped,
        requested,
        disposition,
        census=census,
        authority_blocked=authority_blocked,
    )
    regression_reactivated: list[str] = []
    if not targets:
        summary = {
            "schemaVersion": 12,
            "mode": args.mode,
            "publicationAllowed": False,
            "mainWritesAllowed": False,
            "selectionAuthority": "provider-census-status.json:repairQueue + provider-authority-status.json",
            "authorityBlockedProviders": sorted(authority_blocked),
            "targetedProviderCount": 0,
            "targetedProviders": [],
            "preRepairRetestedProviders": initial_targets,
            "censusStatusUpdated": True,
            "postRefreshRepairQueue": census.get("repairQueue") or [],
            "preservationGatePassed": True,
        }
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("FIELD_PROVIDER_REPAIR_EMPTY symptoms_recovered_during_precheck=true", flush=True)
        return 0

    requested_workers = int(args.workers)
    if requested_workers > 0:
        repair_workers = max(1, min(requested_workers, 32))
    elif len(targets) >= 240:
        repair_workers = 32
    elif len(targets) >= 120:
        repair_workers = 24
    elif len(targets) >= 48:
        repair_workers = 16
    else:
        repair_workers = 12

    print(
        "FIELD_PROVIDER_REPAIR_SCOPE "
        f"mode={args.mode} catalogue={len(catalogue)} active={len(active_catalogue)} targeted={len(targets)} "
        f"skip_file={len(skipped)} authority_blocked={len(authority_blocked)} disposition_green_excluded={len(auto_excluded_green)} "
        f"regression_reactivated={len(regression_reactivated)} "
        f"attempts={attempts} workers={repair_workers} providers={','.join(targets)}",
        flush=True,
    )
    if regression_reactivated:
        print(
            "FIELD_PROVIDER_REPAIR_REGRESSIONS providers=" + ",".join(regression_reactivated),
            flush=True,
        )

    run(
        sys.executable,
        "scripts/provider_runtime_plan_lkg_v1.py",
        "capture",
        "--baseline", str(PORTFOLIO_BASELINE.relative_to(ROOT)),
    )

    # PROVIDER_REPAIR_CURRENT_BOUNDARY_V22
    # V21.10's provider-specific `.homes` authority is historical evidence only;
    # current Repair must not replay it. V21.12 is the generic live boundary.
    # This order is canonical. V16 (chained by base runtime V11) requires Source
    # Plan V15. V17 then builds on V16, while V21.8 cumulatively chains V18-V21.7
    # before the live recovery census. Do not reorder these migrations.
    migrations = [
        "scripts/prepatch_identity_cleanup_shared_owner_v1.py",
        "scripts/apply_core_identity_ownership_cleanup.py",
        "scripts/upgrade_provider_worker_route_proof_v1.py",
        "scripts/upgrade_provider_base_runtime_v5.py",
        "scripts/upgrade_provider_base_route_requests_v1.py",
        "scripts/upgrade_provider_route_authority_v5.py",
        "scripts/upgrade_route_recovery_request_specs_v1.py",
        "scripts/upgrade_provider_v3_source_plan_v5.py",
        "scripts/upgrade_provider_repair_v6.py",
        "scripts/upgrade_provider_repair_v7.py",
        "scripts/upgrade_provider_repair_v8.py",
        "scripts/upgrade_provider_text_body_request_v9.py",
        "scripts/upgrade_provider_text_body_request_v9_1.py",
        "scripts/upgrade_provider_source_plan_v10.py",
        "scripts/upgrade_provider_external_identity_route_v11_1.py",
        "scripts/upgrade_provider_source_plan_v12.py",
        "scripts/upgrade_provider_route_plan_v13_2.py",
        "scripts/upgrade_provider_search_request_plan_v14.py",
        "scripts/upgrade_provider_search_request_plan_v14_1.py",
        "scripts/upgrade_provider_source_plan_v15.py",
        "scripts/upgrade_provider_route_retry_v1.py",
        "scripts/upgrade_provider_base_runtime_v11.py",
        "scripts/upgrade_provider_search_detail_bridge_v17.py",
        "scripts/upgrade_provider_composite_request_template_v21_8.py",
        "scripts/upgrade_provider_json_catalogue_preservation_v21_9.py",
        "scripts/retire_provider_neko_sama_v21_11.py",
        "scripts/upgrade_provider_runtime_reconstruction_v21_12.py",
        "scripts/upgrade_stream_sanitizer_v7_selection.py",
    ]
    for migration in migrations:
        run(sys.executable, migration)

    run("node", "--check", "scripts/provider_worker.cjs")
    for test in (
        "tests/provider_route_proof_authority_test.py",
        "tests/provider_repair_v6_recipe_regression_test.py",
        "tests/provider_route_recovery_apply_scope_test.py",
        "tests/provider_route_proof_manifest_current_scope_test.py",
        "tests/provider_repair_merge_typed_recipe_test.py",
        "tests/provider_repair_v7_typed_resolver_test.py",
        "tests/provider_repair_v8_partial_typed_resolver_test.py",
        "tests/provider_text_body_request_v9_test.py",
        "tests/provider_source_plan_v10_regression_test.py",
        "tests/provider_telegram_discovery_only_contract_test.py",
        "tests/provider_external_identity_route_v11_test.py",
        "tests/provider_source_plan_v12_regression_test.py",
        "tests/provider_route_plan_v13_regression_test.py",
        "tests/provider_search_request_plan_v14_contract_test.py",
        "tests/provider_search_request_plan_v14_1_contract_test.py",
        "tests/provider_source_plan_v15_contract_test.py",
        "tests/provider_execution_authority_v16_contract_test.py",
        "tests/provider_composite_request_template_v21_8_test.py",
        "tests/provider_json_catalogue_preservation_v21_9_test.py",
        "tests/provider_neko_sama_retirement_v21_11_test.py",
        "tests/stream_output_correlated_player_fallback_v7_test.py",
        "tests/global_identity_policy_ownership_test.py",
        "tests/provider_latest_request_cancellation_test.py",
        "tests/provider_native_abort_ignorant_cancellation_test.py",
        "tests/provider_quick_yield_fixture_selection_test.py",
        "tests/provider_runtime_plan_lkg_v1_test.py",
        "tests/provider_external_drift_preservation_test.py",
    ):
        run(sys.executable, test)

    cmd = [
        sys.executable, "scripts/recover_provider_routes_from_upstreams.py",
        "--workers", str(repair_workers),
        "--timeout", str(max(15, min(args.timeout, 120))),
        "--attempts", str(attempts),
        "--out", str(TARGET_REPORT.relative_to(ROOT)),
    ]
    for provider in targets:
        cmd.extend(["--provider", provider])
    route_timeout = route_recovery_outer_timeout(
        len(targets),
        repair_workers,
        args.timeout,
        attempts,
    )
    print(
        "FIELD_PROVIDER_REPAIR_ROUTE_BUDGET "
        f"providers={len(targets)} workers={repair_workers} timeout_seconds={route_timeout}",
        flush=True,
    )
    run(*cmd, timeout=route_timeout)

    run(sys.executable, "scripts/merge_provider_repair_report_v6.py", "--baseline", "automation/provider-route-recovery-v5.json", "--targeted", str(TARGET_REPORT.relative_to(ROOT)), "--output", str(MERGED_REPORT.relative_to(ROOT)), "--manifest", "manifest.json")
    run(sys.executable, "scripts/apply_provider_route_recovery_report.py", str(MERGED_REPORT.relative_to(ROOT)))
    run(
        sys.executable,
        "scripts/provider_runtime_plan_lkg_v1.py",
        "apply",
    )
    run(sys.executable, "scripts/enforce_route_proof_manifest_policy_v1.py", "--report", str(MERGED_REPORT.relative_to(ROOT)), "--manifest", "manifest.json", "--overrides", "provider-overrides.json")

    run(sys.executable, "scripts/materialize_provider_base_v3_store.py")
    repair_materialization_scope = rematerialize_repair_scope(
        targets,
        targeted_only=args.mode == "repair",
    )
    run(sys.executable, "scripts/generate_language_manifests.py", "--manifest", "manifest.json", "--report", "health-report.json")
    run(sys.executable, "scripts/validate_published_provider_config.py")

    candidate_guard_env = os.environ.copy()
    if args.mode == "repair":
        candidate_guard_env["NUVIO_PROVIDER_FILTER"] = ",".join(targets)
    for test in (
        "tests/provider_js_lego_ownership_test.py",
        "tests/global_stream_output_guard_test.py",
        "tests/episodic_identity_runtime_test.py",
        "tests/episodic_year_identity_regression_test.py",
        "tests/global_media_type_pre_network_gate_test.py",
        "tests/global_media_type_resolution_test.py",
        "tests/native_dual_id_identity_test.py",
        "tests/global_stream_presentation_test.py",
        "tests/global_stream_presentation_pipeline_test.py",
    ):
        run(
            sys.executable,
            test,
            env=(
                candidate_guard_env
                if test == "tests/global_stream_output_guard_test.py"
                else None
            ),
        )

    # Intelligent repair is one portfolio operation, not provider-by-provider
    # maintenance. The Brain stages all unresolved targets, tests reusable
    # hypotheses in bounded batches, learns from strict wins, rematerializes, and
    # lets later waves transfer trusted skills to compatible remaining providers.
    BRAIN_REPAIR.unlink(missing_ok=True)
    if args.mode in {"repair", "force"}:
        brain_rounds_per_batch = 1 if args.mode == "repair" else 3
        brain_waves = 1 if args.mode == "repair" else 3
        brain_time_budget_seconds = 600 if args.mode == "repair" else 900
        brain_cmd = [
            sys.executable,
            "scripts/run_provider_brain_repair.py",
            "--waves", str(brain_waves),
            "--batch-size", "48",
            "--max-rounds-per-batch", str(brain_rounds_per_batch),
            "--time-budget-seconds", str(brain_time_budget_seconds),
            "--min-start-batch-seconds", "150",
            "--output", str(BRAIN_REPAIR.relative_to(ROOT)),
        ]
        print(
            "FIELD_PROVIDER_REPAIR_BRAIN_ROUNDS "
            f"mode={args.mode} rounds_per_batch={brain_rounds_per_batch} "
            f"waves={brain_waves} time_budget_seconds={brain_time_budget_seconds}",
            flush=True,
        )
        for provider in targets:
            brain_cmd.extend(["--provider", provider])
        run(
            *brain_cmd,
            timeout=1080,
        )
        if not BRAIN_REPAIR.exists():
            raise RuntimeError("Brain Repair did not produce its portfolio report")

    # Revalidate the whole symptom set that entered this cycle. Providers that
    # recovered during the pre-check are not repaired, but remain in the final
    # census so preservation/comparison never mistakes recovery for disappearance.
    candidate_portfolio = capture_portfolio_yield(PORTFOLIO_CANDIDATE, initial_targets)

    # Activation finalization is deliberately after the real candidate census.
    # Broken/incomplete providers become enabled=false while their learned DATA is
    # retained and explicitly classified repair/off for later Learning/Repair.
    run(
        sys.executable,
        "scripts/finalize_provider_repair_disposition_v1.py",
        "--recovery", str(TARGET_REPORT.relative_to(ROOT)),
        "--quick-yield", str(QUICK_YIELD.relative_to(ROOT)),
    )
    run(sys.executable, "scripts/generate_language_manifests.py", "--manifest", "manifest.json", "--report", "health-report.json")
    run(sys.executable, "scripts/validate_published_provider_config.py")
    run(sys.executable, "tests/provider_v3_strategy_plan_contract_test.py")

    PORTFOLIO_RETRY.unlink(missing_ok=True)
    PORTFOLIO_LOSSES.unlink(missing_ok=True)
    preliminary_cmd = [
        sys.executable,
        "scripts/compare_quick_yield_preservation.py",
        "--baseline", str(PORTFOLIO_BASELINE.relative_to(ROOT)),
        "--candidate", str(PORTFOLIO_CANDIDATE.relative_to(ROOT)),
        "--losses-output", str(PORTFOLIO_LOSSES.relative_to(ROOT)),
    ]
    subprocess.run(
        preliminary_cmd,
        cwd=ROOT,
        env=os.environ.copy(),
        check=False,
        timeout=300,
    )
    losses = load(PORTFOLIO_LOSSES).get("providers") if PORTFOLIO_LOSSES.exists() else []
    losses = [cid(value) for value in losses or [] if cid(value)]
    if losses and attempts > 1:
        retry_attempts = min(max(attempts - 1, 1), 3)
        run(
            sys.executable,
            "scripts/audit_provider_quick_yield_targeted.py",
            "--providers-json", str(PORTFOLIO_LOSSES.relative_to(ROOT)),
            "--output", str(PORTFOLIO_RETRY.relative_to(ROOT)),
            "--attempts", str(retry_attempts),
        )

    final_portfolio_cmd = [
    sys.executable,
    "scripts/compare_quick_yield_preservation.py",
    "--baseline", str(PORTFOLIO_BASELINE.relative_to(ROOT)),
    "--candidate", str(PORTFOLIO_CANDIDATE.relative_to(ROOT)),
    "--baseline-runtime-lkg", str(RUNTIME_PLAN_LKG),
    "--manifest", str(MANIFEST.relative_to(ROOT)),
    "--disposition", str(DISPOSITION.relative_to(ROOT)),
    "--root", ".",
    "--losses-output", str(PORTFOLIO_LOSSES.relative_to(ROOT)),
]
    if PORTFOLIO_RETRY.exists():
        final_portfolio_cmd.extend(["--candidate-retry", str(PORTFOLIO_RETRY.relative_to(ROOT))])
    portfolio_proc = subprocess.run(
        final_portfolio_cmd,
        cwd=ROOT,
        env=os.environ.copy(),
        check=False,
        timeout=300,
    )

    yield_cmd = [sys.executable, "scripts/audit_provider_repair_yield_v6.py", "--recovery", str(TARGET_REPORT.relative_to(ROOT)), "--skip-file", str(skip_path.relative_to(ROOT) if skip_path.is_relative_to(ROOT) else skip_path), "--output", str(YIELD_REPORT.relative_to(ROOT))]
    if not args.allow_upstream_positive_loss:
        yield_cmd.append("--require-upstream-positive-preserved")
    yield_proc = subprocess.run(
        yield_cmd,
        cwd=ROOT,
        env=os.environ.copy(),
        check=False,
        timeout=600,
    )

    # The final yield audit is another current-byte observation from this same run.
    # Preserve any stronger identity-safe positive evidence before the authoritative
    # post-repair census is rendered; otherwise a later verified fixture can be
    # discarded by an earlier zero-result portfolio sample.
    if YIELD_REPORT.exists():
        run(
            sys.executable,
            "scripts/merge_provider_same_run_positive_evidence.py",
            "--base", str(PORTFOLIO_CANDIDATE.relative_to(ROOT)),
            "--supplement", str(YIELD_REPORT.relative_to(ROOT)),
            "--output", str(PORTFOLIO_CANDIDATE.relative_to(ROOT)),
        )
        candidate_portfolio = load(PORTFOLIO_CANDIDATE)
    shutil.copyfile(PORTFOLIO_CANDIDATE, CENSUS_POST_REPAIR)
    run_id = str(os.environ.get("GITHUB_RUN_ID") or "local")
    trigger_sha = str(os.environ.get("GITHUB_SHA") or "")
    persist_repair_candidate_evidence(
        candidate_portfolio,
        run_id=f"{run_id}-post-repair",
        sha=trigger_sha or "post-repair",
    )
    # Repair candidate bytes are ephemeral in this workflow. Render durable
    # current state from the pre-repair/current-byte audit; retain verified
    # candidate playback separately as CANDIDATE OK until main reproduces it.
    post_repair_census = render_persisted_byte_census(
        PORTFOLIO_BASELINE,
        phase="post-repair-candidate",
        provider_overrides=CURRENT_OVERRIDES_SNAPSHOT,
    )

    targeted_report = load(TARGET_REPORT)
    merged_report = load(MERGED_REPORT)
    yield_report = load(YIELD_REPORT) if YIELD_REPORT.exists() else {}
    retry_report = load(PORTFOLIO_RETRY) if PORTFOLIO_RETRY.exists() else {}
    disposition_report = load(DISPOSITION) if DISPOSITION.exists() else {}
    brain_report = load(BRAIN_REPAIR) if BRAIN_REPAIR.exists() else {}
    brain_deferred = {
        cid(value) for value in brain_report.get("deferredLearningProviders") or []
        if cid(value)
    }
    brain_remaining = {
        cid(value) for value in brain_report.get("remainingProviders") or []
        if cid(value)
    }
    brain_accepted = int(brain_report.get("acceptedRepairCount") or 0)
    # Repair can legitimately converge without a mutation: once every targeted
    # signature exhausted the bounded Core strategies it becomes independent
    # Learning debt. A transient failure to reproduce historical upstream proof
    # must remain visible, but it cannot mean that an unmodified Repair candidate
    # regressed that proof.
    converged_to_learning_debt = bool(
        args.mode == "repair"
        and targets
        and brain_accepted == 0
        and not brain_remaining
        and set(targets).issubset(brain_deferred)
    )
    summary = {
        "schemaVersion": 12,
        "mode": args.mode,
        "publicationAllowed": False,
        "mainWritesAllowed": False,
        "catalogueProviderCount": len(catalogue),
        "activeProviderCount": len(active_catalogue),
        "selectionAuthority": "provider-census-status.json:repairQueue",
        "preRepairRetestedProviders": initial_targets,
        "censusStatusUpdated": True,
        "postRepairCensusCounts": post_repair_census.get("counts") or {},
        "postRepairSymptomaticProviders": post_repair_census.get("symptomaticProviders") or post_repair_census.get("brainQueue") or [],
        "postRepairRepairQueue": post_repair_census.get("repairQueue") or [],
        "postRepairEnvironmentQueue": post_repair_census.get("environmentQueue") or [],
        "skippedAlreadyGreenProviders": sorted(skipped),
        "autoExcludedCurrentGreenProviders": sorted(auto_excluded_green),
        "freshRegressionReactivatedProviders": sorted(regression_reactivated),
        "dispositionScopedUnresolvedOnly": not bool(requested),
        "targetedProviderCount": len(targets),
        "targetedProviders": targets,
        "maxAttemptsPerTask": attempts,
        "routePlanRevision": "v21.12",
        "repairMaterializationMode": repair_materialization_scope.get("mode"),
        "repairMaterializedProviders": repair_materialization_scope.get("providers") or [],
        "repairMaterializationReasons": repair_materialization_scope.get("reasons") or [],
        "brainRepair": brain_report or None,
        "brainRepairAcceptedCount": brain_accepted,
        "brainRepairDeferredLearningProviders": sorted(brain_deferred),
        "brainRepairRemainingProviders": sorted(brain_remaining),
        "brainRepairConvergedToLearningDebt": converged_to_learning_debt,
        "targetedProvidersWithProvenRoutes": int(targeted_report.get("providersWithProvenRoutes") or 0),
        "targetedProvenRoutes": int(targeted_report.get("provenRouteCount") or 0),
        "mergedProvidersWithProvenRoutes": int(merged_report.get("providersWithProvenRoutes") or 0),
        "mergedProvenRoutes": int(merged_report.get("provenRouteCount") or 0),
        "postRepairPlayableProviders": yield_report.get("playableProviders") or [],
        "postRepairVerifiedProviders": yield_report.get("verifiedProviders") or [],
        "lostUpstreamPositivePairs": yield_report.get("lostUpstreamPositivePairs") or [],
        "upstreamPositivePreservationGatePassed": yield_proc.returncode == 0,
        "portfolioBaselineRawProviders": baseline_portfolio.get("raw_providers") or [],
        "portfolioBaselinePlayableProviders": baseline_portfolio.get("playable_providers") or [],
        "portfolioBaselineVerifiedProviders": baseline_portfolio.get("verified_providers") or [],
        "portfolioCandidateRawProviders": candidate_portfolio.get("raw_providers") or [],
        "portfolioCandidatePlayableProviders": candidate_portfolio.get("playable_providers") or [],
        "portfolioCandidateVerifiedProviders": candidate_portfolio.get("verified_providers") or [],
        "portfolioRetriedProviders": retry_report.get("providers") or [],
        "portfolioPreservationGatePassed": portfolio_proc.returncode == 0,
        "repairDispositionStateCounts": disposition_report.get("stateCounts") or {},
        "disabledProviderCount": int(disposition_report.get("disabledProviderCount") or 0),
        "activeBrokenProviderAllowed": False,
        "preservationGatePassed": yield_proc.returncode == 0 and portfolio_proc.returncode == 0,
        "executionGatePassed": (
            (yield_proc.returncode == 0 and portfolio_proc.returncode == 0)
            or (converged_to_learning_debt and portfolio_proc.returncode == 0)
        ),
        "executionOutcome": (
            "preserved"
            if (yield_proc.returncode == 0 and portfolio_proc.returncode == 0)
            else ("converged_to_learning_debt" if converged_to_learning_debt and portfolio_proc.returncode == 0 else "failed")
        ),
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_REPAIR_V6_FINAL "
        f"mode={args.mode} revision=v21.11 targeted={len(targets)} targeted_proven={summary['targetedProvidersWithProvenRoutes']} "
        f"playable={len(summary['postRepairPlayableProviders'])} verified={len(summary['postRepairVerifiedProviders'])} "
        f"disabled={summary['disabledProviderCount']} lost={len(summary['lostUpstreamPositivePairs'])} "
        f"upstream_gate={str(summary['upstreamPositivePreservationGatePassed']).lower()} "
        f"portfolio_gate={str(summary['portfolioPreservationGatePassed']).lower()} "
        f"preservation_gate={str(summary['preservationGatePassed']).lower()} "
        f"execution_gate={str(summary['executionGatePassed']).lower()} "
        f"outcome={summary['executionOutcome']} active_broken=false"
    )
    return 0 if summary["executionGatePassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
