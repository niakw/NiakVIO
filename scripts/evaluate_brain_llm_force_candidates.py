#!/usr/bin/env python3
"""Evaluate external Brain-LLM Force mutations in isolated provider sandboxes.

Each provider candidate starts from the exact current Git SHA in its own detached
git worktree. The candidate is applied there, only that provider is
rematerialized, and the same Deep health lane is executed for baseline and
candidate bytes. A Force candidate can be exported for later application only
after strict runtime improvement AND the existing automatic identity gate pass.

This script never mutates the caller's working tree.
"""
from __future__ import annotations

import argparse
import copy
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

SHA40 = __import__("re").compile(r"^[0-9a-f]{40}$")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def run(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        env=env,
        check=True,
    )


def provider_result(payload: dict[str, Any], provider: str) -> dict[str, Any]:
    rows = [
        row
        for row in payload.get("results") or []
        if isinstance(row, dict)
        and (
            canon(row.get("provider")) == provider
            or canon(row.get("provider_id")) == provider
            or str(row.get("key") or "").casefold().endswith(":" + provider)
        )
    ]
    if len(rows) != 1:
        if len(payload.get("results") or []) == 1 and isinstance((payload.get("results") or [None])[0], dict):
            return copy.deepcopy(payload["results"][0])
        raise ValueError(
            f"{provider}: expected exactly one provider health result, got {len(rows)}"
        )
    return copy.deepcopy(rows[0])


def invocation_summary(result: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for test in result.get("tests") or []:
        if not isinstance(test, dict):
            continue
        fixture = test.get("fixture") if isinstance(test.get("fixture"), dict) else {}
        for row in test.get("invocation_diagnostics") or []:
            if not isinstance(row, dict):
                continue
            output.append(
                {
                    "fixture": str(fixture.get("label") or fixture.get("tmdbId") or "")[:160],
                    "name": str(row.get("name") or "")[:80],
                    "inferredMode": str(row.get("inferred_mode") or "")[:40],
                    "result": str(row.get("result") or "")[:40],
                    "streamCount": int(row.get("stream_count") or 0),
                    "providerObservations": int(row.get("provider_observations") or 0),
                    "errorCode": str((row.get("error") or {}).get("code") or "")[:100]
                    if isinstance(row.get("error"), dict)
                    else "",
                }
            )
    return output[:48]


def result_summary(result: dict[str, Any]) -> dict[str, Any]:
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    return {
        "status": str(result.get("status") or ""),
        "score": int(result.get("score") or 0),
        "streamsPlayable": runtime_repair.playable_stream_count(result),
        "streamsReturned": runtime_repair.stream_count(result),
        "identityContradictions": runtime_repair.identity_contradiction_count(result),
        "providerRequests": int(evidence.get("provider_request_count") or 0),
        "failureClass": str(result.get("failure_class") or ""),
        "invocationDiagnostics": invocation_summary(result),
    }


def evaluate_pair(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> tuple[bool, str]:
    accepted, reason = runtime_repair.compare_results(baseline, candidate)
    if not accepted:
        return False, reason
    identity_ok, identity_reason = automatic_repair_identity_gate(candidate)
    if not identity_ok:
        return False, identity_reason
    return True, reason


def write_targets(path: Path, provider: str) -> None:
    path.write_text(
        json.dumps({"targets": [{"id": provider}]}, indent=2) + "\n",
        encoding="utf-8",
    )


def stage_provider(repo_root: Path, provider: str, stage: Path, targets: Path) -> None:
    run(
        sys.executable,
        "scripts/stage_published.py",
        "--stage",
        str(stage),
        "--include-file",
        str(targets),
        cwd=repo_root,
    )


def health_provider(stage: Path, output: Path) -> dict[str, Any]:
    return deep.run_health(
        stage=stage,
        registry_path=stage / "candidates.json",
        output_dir=output,
        mode="deep",
        health_check=ROOT / "scripts" / "health_check.mjs",
    )


def single_row_payload(payload: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    result = {
        key: copy.deepcopy(value)
        for key, value in payload.items()
        if key != "rows"
    }
    result["rows"] = [copy.deepcopy(row)]
    result["providerCount"] = 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--accepted-output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    args = parser.parse_args()

    current_sha = str(args.current_sha or "").strip().casefold()
    if not SHA40.fullmatch(current_sha):
        raise SystemExit("exact 40-hex current SHA required")
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip().casefold()
    if actual != current_sha:
        raise SystemExit(f"Force sandbox SHA mismatch current={current_sha} actual={actual}")

    payload = load(args.input)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("Force mutation rows missing")
    selected = {canon(value) for value in args.provider if canon(value)}

    eligible: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        provider = canon(raw.get("providerId"))
        if not provider or (selected and provider not in selected):
            continue
        if provider in seen:
            raise SystemExit(
                f"{provider}: multiple concrete Force candidates require isolated hypothesis scheduling"
            )
        seen.add(provider)
        eligible.append(copy.deepcopy(raw))

    report_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []

    parent = args.work_root.resolve() if args.work_root else Path(
        tempfile.mkdtemp(prefix="niakvio-force-candidates-")
    )
    owned_parent = args.work_root is None
    parent.mkdir(parents=True, exist_ok=True)

    try:
        for index, row in enumerate(eligible, start=1):
            provider = canon(row.get("providerId"))
            fingerprint = str(row.get("mutationFingerprint") or "").strip().casefold()
            root = parent / f"{index:03d}-{provider}"
            baseline_stage = root / "baseline-stage"
            candidate_stage = root / "candidate-stage"
            baseline_out = root / "baseline-health"
            candidate_out = root / "candidate-health"
            worktree = root / "worktree"
            targets = root / "targets.json"
            row_payload = root / "force-row.json"
            apply_report = root / "apply-report.json"
            root.mkdir(parents=True, exist_ok=True)
            write_targets(targets, provider)

            stage_provider(ROOT, provider, baseline_stage, targets)
            baseline_health = health_provider(baseline_stage, baseline_out)
            baseline = provider_result(baseline_health, provider)

            run("git", "worktree", "add", "--detach", str(worktree), current_sha)
            try:
                isolated = single_row_payload(payload, row)
                row_payload.write_text(
                    json.dumps(isolated, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                apply_args = [
                    sys.executable,
                    "scripts/apply_brain_llm_force_mutations.py",
                    "--input",
                    str(row_payload),
                    "--current-sha",
                    current_sha,
                    "--provider",
                    provider,
                    "--census",
                    "automation/provider-census-status.json",
                    "--report",
                    str(apply_report),
                ]
                run(*apply_args, cwd=worktree)
                applied = load(apply_report)
                if int(applied.get("appliedProviderCount") or 0) != 1:
                    report_rows.append(
                        {
                            "provider": provider,
                            "mutationFingerprint": fingerprint,
                            "accepted": False,
                            "reason": "force_candidate_not_applied",
                            "baseline": result_summary(baseline),
                            "application": applied,
                        }
                    )
                    continue

                run(
                    sys.executable,
                    "scripts/materialize_provider_v3_one.py",
                    provider,
                    "--preserve-structured-data",
                    cwd=worktree,
                )
                stage_provider(worktree, provider, candidate_stage, targets)
                candidate_health = health_provider(candidate_stage, candidate_out)
                candidate = provider_result(candidate_health, provider)
                accepted, reason = evaluate_pair(baseline, candidate)

                result = {
                    "provider": provider,
                    "mutationFingerprint": fingerprint,
                    "accepted": bool(accepted),
                    "reason": reason,
                    "baseline": result_summary(baseline),
                    "candidate": result_summary(candidate),
                    "application": {
                        "changedFiles": applied.get("changedFiles") or [],
                        "sourceBrainLlmSha": applied.get("sourceBrainLlmSha"),
                        "sourceNiakvioSha": applied.get("sourceNiakvioSha"),
                    },
                }
                report_rows.append(result)
                if accepted:
                    accepted_rows.append(copy.deepcopy(row))
            finally:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=ROOT,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

        accepted_payload = {
            key: copy.deepcopy(value)
            for key, value in payload.items()
            if key != "rows"
        }
        accepted_payload["rows"] = accepted_rows
        accepted_payload["providerCount"] = len(
            {canon(row.get("providerId")) for row in accepted_rows}
        )

        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.accepted_output.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "currentSha": current_sha,
                    "candidateCount": len(eligible),
                    "acceptedProviderCount": len(accepted_rows),
                    "acceptedProviders": [
                        canon(row.get("providerId")) for row in accepted_rows
                    ],
                    "rows": report_rows,
                    "publicationAuthority": False,
                    "proofAuthority": False,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        args.accepted_output.write_text(
            json.dumps(accepted_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            "FIELD_BRAIN_LLM_FORCE_SANDBOX "
            f"candidates={len(eligible)} accepted={len(accepted_rows)} "
            f"providers={','.join(canon(row.get('providerId')) for row in accepted_rows) or '-'}"
        )
        return 0
    finally:
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if owned_parent:
            shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
