#!/usr/bin/env python3
"""Materialize validated Brain sandbox repairs as a reproducible config proposal.

This script never publishes providers. It translates only repairs already accepted
by the bounded sandbox retest into a proposed provider-overrides.json that can be
reviewed and validated in a draft pull request.

When the live repository provider-overrides.json is used, the proposal is anchored
to the immutable Git HEAD checked out for the run. Sandbox preparation is allowed
to mutate its working-tree copy for diagnostics, but those incidental top-level
changes must never leak into a repair proposal.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE_PROFILE = "adaptive_runtime_recovery"
ADAPTIVE_SCRIPT = "scripts/provider_patches/adaptive_runtime_recovery_v5.py"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_proposal_baseline(path: Path) -> tuple[dict[str, Any], str]:
    """Return the trusted config baseline and how it was obtained.

    The Brain workflow mutates ROOT/provider-overrides.json while building its
    isolated stage (normalization, learned runtime metadata, etc.). The repair PR
    must be derived from the exact committed input instead, otherwise an unrelated
    sandbox metadata change trips the publication guard or, worse, gets proposed.

    Temporary/custom override files used by tests and tooling remain literal input.
    """
    resolved = path.resolve()
    committed = (ROOT / "provider-overrides.json").resolve()
    if resolved != committed:
        return load_json(resolved), "input-file"

    completed = subprocess.run(
        ["git", "show", "HEAD:provider-overrides.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        details = "\n".join(
            part.strip()
            for part in (completed.stdout, completed.stderr)
            if part and part.strip()
        )
        raise RuntimeError(
            "cannot materialize immutable provider-overrides baseline from run HEAD: "
            + details[-1200:]
        )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise ValueError("HEAD:provider-overrides.json must be a JSON object")
    return value, "git-head"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def provider_id(candidate: dict[str, Any]) -> str:
    return str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold().strip()


def accepted_profile(round_row: dict[str, Any], accepted: dict[str, Any]) -> str:
    direct = str(accepted.get("profile") or "").strip()
    if direct:
        return direct
    parent_key = str(accepted.get("parent_key") or "")
    accepted_sha = str(accepted.get("sha256") or "")
    generated = [
        row for row in round_row.get("attempts") or []
        if isinstance(row, dict)
        and str(row.get("parent_key") or "") == parent_key
        and str(row.get("status") or "") == "generated"
        and row.get("profile")
    ]
    exact = [row for row in generated if accepted_sha and str(row.get("repair_sha256") or "") == accepted_sha]
    choice = exact[0] if exact else (generated[0] if len(generated) == 1 else None)
    return str(choice.get("profile") or "").strip() if isinstance(choice, dict) else ""


def adaptive_options(candidate: dict[str, Any]) -> dict[str, Any] | None:
    for record in reversed(candidate.get("local_patches") or []):
        if not isinstance(record, dict):
            continue
        if record.get("type") != "patch_profile" or record.get("profile") != ADAPTIVE_PROFILE:
            continue
        options = record.get("options")
        if isinstance(options, dict) and options:
            return copy.deepcopy(options)
    return None


def apply_proposal(overrides: dict[str, Any], pid: str, profile: str, candidate: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    patches = overrides.setdefault("provider_patches", {})
    if not isinstance(patches, dict):
        raise ValueError("provider_patches must be an object")
    patch = patches.setdefault(pid, {})
    if not isinstance(patch, dict):
        raise ValueError(f"provider_patches.{pid} must be an object")

    if profile == ADAPTIVE_PROFILE:
        options = adaptive_options(candidate)
        if not options:
            return False, {"providerId": pid, "profile": profile, "reason": "missing_validated_adaptive_options"}
        scripts = [str(value) for value in patch.get("patch_scripts") or [] if str(value).strip()]
        changed = False
        if ADAPTIVE_SCRIPT not in scripts:
            scripts.append(ADAPTIVE_SCRIPT)
            patch["patch_scripts"] = scripts
            changed = True
        option_map = patch.setdefault("patch_script_options", {})
        if not isinstance(option_map, dict):
            raise ValueError(f"provider_patches.{pid}.patch_script_options must be an object")
        if option_map.get(ADAPTIVE_SCRIPT) != options:
            option_map[ADAPTIVE_SCRIPT] = options
            changed = True
        return changed, {
            "providerId": pid,
            "profile": profile,
            "proposalType": "validated_patch_script",
            "patchScript": ADAPTIVE_SCRIPT,
        }

    profiles = [str(value) for value in patch.get("profiles") or [] if str(value).strip()]
    if profile in profiles:
        return False, {"providerId": pid, "profile": profile, "reason": "already_persisted"}
    profiles.append(profile)
    patch["profiles"] = profiles
    return True, {
        "providerId": pid,
        "profile": profile,
        "proposalType": "validated_runtime_profile",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--repair-report", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    stage = load_json(args.stage)
    report = load_json(args.repair_report)
    original, baseline_source = load_proposal_baseline(args.overrides)
    proposed = copy.deepcopy(original)

    candidates = {
        str(row.get("key") or ""): row
        for row in stage.get("candidates") or []
        if isinstance(row, dict) and row.get("key")
    }
    proposals: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for round_row in report.get("rounds") or []:
        if not isinstance(round_row, dict):
            continue
        for accepted in round_row.get("accepted") or []:
            if not isinstance(accepted, dict):
                continue
            parent_key = str(accepted.get("parent_key") or "")
            candidate = candidates.get(parent_key)
            if not candidate:
                skipped.append({"parentKey": parent_key, "reason": "missing_final_candidate"})
                continue
            pid = provider_id(candidate)
            profile = accepted_profile(round_row, accepted)
            if not pid or not profile:
                skipped.append({"parentKey": parent_key, "providerId": pid or None, "reason": "missing_provider_or_profile"})
                continue
            changed, row = apply_proposal(proposed, pid, profile, candidate)
            row.update({
                "parentKey": parent_key,
                "round": round_row.get("round"),
                "statusBefore": accepted.get("status_before"),
                "statusAfter": accepted.get("status_after"),
                "streamsPlayableBefore": accepted.get("streams_playable_before"),
                "streamsPlayableAfter": accepted.get("streams_playable_after"),
                "reason": row.get("reason") or accepted.get("reason"),
            })
            (proposals if changed else skipped).append(row)

    write_json(args.output, proposed)
    summary = {
        "schemaVersion": 1,
        "baselineSource": baseline_source,
        "proposalCount": len(proposals),
        "providers": sorted({row["providerId"] for row in proposals if row.get("providerId")}),
        "proposals": proposals,
        "skipped": skipped,
        "policy": {
            "publicationAllowed": False,
            "productionWritesAllowed": False,
            "pullRequestOnly": True,
            "requiresFreshCi": True,
            "requiresHumanMerge": True,
        },
    }
    write_json(args.summary, summary)
    print(
        "FIELD_BRAIN_REPAIR_PROPOSAL "
        f"proposals={len(proposals)} providers={len(summary['providers'])} skipped={len(skipped)} "
        f"baseline={baseline_source}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
