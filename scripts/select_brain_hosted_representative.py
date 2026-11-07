#!/usr/bin/env python3
"""Choose one representative Brain sandbox target from current census and retained failures.

Only orchestration: never modifies providers, statuses, domains or authority.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
ARCHIVE = re.compile(r"[0-9]{8,14}\.json\Z")

# CANDIDATE OK must go to same_provider_candidate_program_replay, a
# *non-mutation* Brain policy. Do not feed those targets to a synthesis-only
# workflow that cannot replay the recorded candidate's exact bytes.
STATUS_PRIOR = {
    "REGRESSION PROVIDER": 72,
    "REGRESSION PROVIDER JS": 72,
    "CHAIN REACHED": 62,
    "ROUTE PROVEN": 45,
}


def negative_history(directory: Path) -> dict[str, int]:
    debt: dict[str, int] = {}
    if not directory.is_dir():
        return debt
    for path in sorted(directory.iterdir())[-350:]:
        if not path.is_file() or not ARCHIVE.fullmatch(path.name):
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(raw, dict) or raw.get("publicationAuthority") is not False:
            continue
        provider = str(raw.get("provider") or "").strip().casefold()
        if not ID.fullmatch(provider) or raw.get("acceptedProviderCount") not in (0, None):
            continue
        trace = raw.get("scopeTrace") or []
        reasons = {
            str(row.get("reason") or "").strip().casefold()
            for row in trace if isinstance(row, dict)
        }
        if "no_op" in reasons or "causally_empty_deletion" in reasons:
            debt[provider] = debt.get(provider, 0) + 30
        elif trace:
            debt[provider] = debt.get(provider, 0) + 12
    return {key: min(150, value) for key, value in debt.items()}


def choose(state: dict, debt: dict[str, int], manual: str = "") -> tuple[str, int]:
    providers = {
        str(row.get("provider") or "").strip().casefold(): row
        for row in (state.get("providers") or [])
        if isinstance(row, dict) and ID.fullmatch(str(row.get("provider") or "").strip().casefold())
    }
    manual = manual.strip().casefold()
    if manual:
        if not ID.fullmatch(manual) or manual not in providers:
            raise ValueError("Manual Brain target is not a known current provider")
        row = providers[manual]
        if row.get("status") == "DISABLED":
            raise ValueError("Brain proof cannot target lifecycle-disabled provider")
        if (manual not in set(state.get("repairQueue") or [])
            or row.get("repairEligible") is not True
            or row.get("authorityRepairEligible") is False):
            raise ValueError("Manual Brain target is not currently eligible for repair")
        if row.get("status") not in STATUS_PRIOR or row.get("candidateProof"):
            raise ValueError("Candidate replay/NO PROOF requires a separate evidence workflow, not source synthesis")
        return manual, 0
    queue = {
        str(value).strip().casefold()
        for value in state.get("repairQueue") or []
        if isinstance(value, str) and ID.fullmatch(value.strip().casefold())
    }
    scored = []
    for provider in sorted(queue):
        row = providers.get(provider)
        if not row or row.get("repairEligible") is not True:
            continue
        if row.get("authorityRepairEligible") is False:
            continue
        status = str(row.get("status") or "")
        # In the Brain adapter, *any* candidateProof takes precedence over a
        # route or terminal gap and maps to candidate_replay_gap. Its strategy
        # is intentionally NO_MUTATION. Never silently override that policy.
        if status not in STATUS_PRIOR or row.get("candidateProof"):
            continue
        issue = str(row.get("dominantIssue") or "").casefold()
        score = STATUS_PRIOR[status]
        score += 17 if row.get("historicalProof") else 0
        score += 12 if "zero_result" in issue else 0
        score += 4 if "http_error" in issue else 0
        score -= 80 if "waf" in issue else 0
        score -= 20 if "timeout" in issue else 0
        score -= 10 if "exception" in issue else 0
        score -= debt.get(provider, 0)
        scored.append((score, provider))
    if not scored:
        raise ValueError("No current authorized repair-queue representative")
    score, provider = max(scored, key=lambda row: (row[0], -len(row[1]), row[1]))
    return provider, score


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--manual", default="")
    parser.add_argument("--github-env", type=Path, required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads(args.census.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or not isinstance(state.get("providers"), list):
        raise SystemExit("Brain representative requires current census state")
    debt = negative_history(args.evidence_dir)
    provider, score = choose(state, debt, args.manual)
    # Failed/replay-only targets are explicitly withheld from this mutation
    # lane rather than being counted as 0 Qwen candidates.
    replay = [row.get("provider") for row in state.get("providers") or []
              if isinstance(row, dict)
              and row.get("provider") in (state.get("repairQueue") or [])
              and (row.get("status") == "CANDIDATE OK" or row.get("candidateProof"))]
    print("FIELD_BRAIN_REPLAY_ONLY_QUEUE count="+str(len(replay))
          +" route=same_provider_candidate_program_replay",flush=True)
    if not ID.fullmatch(provider):
        raise SystemExit("Invalid selected Brain provider")
    for path in (args.github_env, args.github_output):
        with path.open("a", encoding="utf-8") as output:
            output.write("TARGET_PROVIDER=" + provider + "\n" if path == args.github_env
                         else "provider=" + provider + "\n")
    print("FIELD_BRAIN_REPRESENTATIVE provider="+provider+
          " score="+str(score)+" repeated_negative_weight="+str(debt.get(provider, 0))+
          " selection="+("manual" if args.manual.strip() else "census_and_experiment"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
