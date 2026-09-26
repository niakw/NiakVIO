#!/usr/bin/env python3
"""Causally revalidate persisted local FORCE guidance on exact current bytes.

Unlike external Brain-LLM FORCE mutations, local farm winners are advisor
profile/experiment hypotheses. Re-run the exact guidance through Deep Repair
from a detached worktree, compare it with an untouched Deep health baseline,
and grant causal credit only for strict current-byte improvement + identity.
No production/provider publication occurs here.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import deep_repair_loop as deep  # noqa: E402
import runtime_repair  # noqa: E402
from repair_identity_gate import automatic_repair_identity_gate  # noqa: E402

FARM_PATH = ROOT / "scripts" / "local" / "run_force_experiment_farm.py"
_spec = importlib.util.spec_from_file_location("local_force_farm", FARM_PATH)
farm = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(farm)

SHA40 = __import__("re").compile(r"^[0-9a-f]{40}$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def baseline_health(worktree: Path, provider: str, root: Path) -> dict[str, Any]:
    payload = farm.guidance_payload(
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True).strip(),
        {},
    )
    payload["rows"] = []
    payload["providerCount"] = 0
    stage, _guidance, output = farm.prepare_stage(worktree, provider, root, payload)
    health = deep.run_health(
        stage=stage,
        registry_path=stage / "candidates.json",
        output_dir=output,
        mode="deep",
        health_check=ROOT / "scripts" / "health_check.mjs",
    )
    rows = [
        row for row in health.get("results") or []
        if isinstance(row, dict) and (
            canon(row.get("provider")) == provider
            or canon(row.get("provider_id")) == provider
            or canon(str(row.get("key") or "").split(":")[-1]) == provider
        )
    ]
    if len(rows) != 1:
        if len(health.get("results") or []) == 1:
            return copy.deepcopy(health["results"][0])
        raise ValueError(f"{provider}: baseline expected one health result, got {len(rows)}")
    return copy.deepcopy(rows[0])


def summary(result: dict[str, Any]) -> dict[str, Any]:
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    return {
        "status": str(result.get("status") or ""),
        "score": int(result.get("score") or 0),
        "streamsPlayable": runtime_repair.playable_stream_count(result),
        "streamsReturned": runtime_repair.stream_count(result),
        "identityContradictions": runtime_repair.identity_contradiction_count(result),
        "providerRequests": int(evidence.get("provider_request_count") or 0),
        "failureClass": str(result.get("failure_class") or ""),
    }


def evaluate_pair(baseline: dict[str, Any], candidate: dict[str, Any], accepted_repairs: int) -> tuple[bool, str]:
    base = summary(baseline)
    cand = summary(candidate)
    if base["streamsPlayable"] > 0 and str(base["status"]).casefold() == "healthy":
        return False, "baseline_already_healthy"
    accepted, reason = runtime_repair.compare_results(baseline, candidate)
    if not accepted:
        return False, reason
    if accepted_repairs <= 0:
        return False, "deep_report_did_not_accept_repair"
    identity_ok, identity_reason = automatic_repair_identity_gate(candidate)
    if not identity_ok:
        return False, identity_reason
    return True, reason


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--current-sha", required=True)
    p.add_argument("--provider", action="append", default=[])
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--deep-rounds", type=int, default=3)
    p.add_argument("--deep-timeout", type=int, default=900)
    p.add_argument("--work-root", type=Path)
    a = p.parse_args()

    sha = str(a.current_sha or "").strip().casefold()
    if not SHA40.fullmatch(sha):
        raise SystemExit("exact current SHA required")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().casefold()
    if actual != sha:
        raise SystemExit(f"local FORCE guidance SHA mismatch current={sha} actual={actual}")

    payload = load(a.input)
    if payload.get("localForcePromotion") is not True or payload.get("priorOnly") is not True:
        raise SystemExit("input is not promoted local FORCE guidance")
    selected = {canon(x) for x in a.provider if canon(x)}
    rows = [
        copy.deepcopy(row)
        for row in payload.get("rows") or []
        if isinstance(row, dict)
        and canon(row.get("providerId"))
        and (not selected or canon(row.get("providerId")) in selected)
    ]
    by_provider: dict[str, dict[str, Any]] = {}
    for row in rows:
        provider = canon(row.get("providerId"))
        if provider in by_provider:
            raise SystemExit(f"{provider}: multiple local FORCE candidates unsupported")
        by_provider[provider] = row
    if selected - set(by_provider):
        raise SystemExit("promoted local FORCE guidance missing requested providers")

    if a.work_root:
        work_root = a.work_root.resolve()
        owned = False
        work_root.mkdir(parents=True, exist_ok=True)
    else:
        parent = ROOT / "local-output"
        parent.mkdir(parents=True, exist_ok=True)
        work_root = Path(tempfile.mkdtemp(prefix="local-force-causal-", dir=parent))
        owned = True

    report_rows: list[dict[str, Any]] = []
    try:
        for provider, row in by_provider.items():
            worktree = work_root / f"{provider}-worktree"
            subprocess.run(["git", "worktree", "add", "--detach", str(worktree), sha], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
            try:
                farm.link_shared_local_tooling(worktree)
                base_root = worktree / ".local-force-causal" / "baseline"
                base = baseline_health(worktree, provider, base_root)

                farm.reset_worktree(worktree, sha)
                exp_root = worktree / ".local-force-causal" / "candidate"
                guidance = farm.guidance_payload(sha, row)
                stage, guidance_path, output = farm.prepare_stage(worktree, provider, exp_root, guidance)
                env = os.environ.copy()
                env["GITHUB_SHA"] = sha
                env["NIAKVIO_BRAIN_LLM_GUIDANCE"] = str(guidance_path)
                env["NUVIO_BRAIN_EXPLORATION_CHAIN"] = "1"
                env["NUVIO_HEALTH_CONCURRENCY"] = "1"
                env.pop("NUVIO_BRAIN_PLANNER_MODE", None)
                rc, runtime = farm.run_logged(
                    [
                        sys.executable,
                        "scripts/run_adaptive_deep_repair.py",
                        "--stage", str(stage),
                        "--registry", str(stage / "candidates.json"),
                        "--output", str(output),
                        "--max-rounds", str(max(1, min(int(a.deep_rounds), 5))),
                    ],
                    cwd=worktree,
                    env=env,
                    log_path=work_root / f"{provider}-deep.log",
                    timeout=max(120, min(int(a.deep_timeout), 1800)),
                )
                repair = farm.load_json(output / "repair-report.json", {})
                cand_health_payload = farm.load_json(output / "health-results.json", {})
                result_rows = [
                    x for x in cand_health_payload.get("results") or []
                    if isinstance(x, dict) and (
                        canon(x.get("provider")) == provider
                        or canon(x.get("provider_id")) == provider
                        or canon(str(x.get("key") or "").split(":")[-1]) == provider
                    )
                ]
                candidate = copy.deepcopy(result_rows[0]) if result_rows else {}
                accepted_repairs = int(repair.get("accepted_repairs") or 0)
                accepted, reason = evaluate_pair(base, candidate, accepted_repairs)
                report_rows.append({
                    "provider": provider,
                    "profile": row.get("profile"),
                    "experimentFingerprint": row.get("experimentFingerprint"),
                    "deepReturnCode": rc,
                    "deepRuntime": runtime,
                    "acceptedRepairs": accepted_repairs,
                    "accepted": accepted,
                    "reason": reason,
                    "baseline": summary(base),
                    "candidate": summary(candidate),
                    "acceptedEvents": farm.accepted_events(repair)[:8],
                })
                print(
                    "FIELD_LOCAL_FORCE_CAUSAL "
                    f"provider={provider} accepted={str(accepted).lower()} reason={reason} "
                    f"baseline_playable={summary(base)['streamsPlayable']} candidate_playable={summary(candidate)['streamsPlayable']}",
                    flush=True,
                )
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        accepted = [row["provider"] for row in report_rows if row.get("accepted") is True]
        out = {
            "schemaVersion": 1,
            "currentSha": sha,
            "candidateCount": len(report_rows),
            "acceptedProviderCount": len(accepted),
            "acceptedProviders": accepted,
            "rows": report_rows,
            "proofAuthority": False,
            "publicationAuthority": False,
            "providerPublicationAuthority": False,
            "causalEvidenceOnly": True,
        }
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            "FIELD_LOCAL_FORCE_CAUSAL_SUMMARY "
            f"candidates={len(report_rows)} accepted={len(accepted)} providers={','.join(accepted) or '-'}"
        )
        return 0
    finally:
        subprocess.run(["git", "worktree", "prune"], cwd=ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if owned:
            shutil.rmtree(work_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
