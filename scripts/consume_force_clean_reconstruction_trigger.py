#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRIGGER = ROOT / ".github" / "triggers" / "force-clean-provider-reconstruction.json"
DEFAULT_STAGE = ROOT / "checked-artifact" / "staging" / "candidates.json"
DEFAULT_PROVENANCE = ROOT / "PROVENANCE.json"

CLEAN_CANDIDATE = "niakvio-clean-reconstruction-v2-candidate"
CLEAN_VERIFIED = "niakvio-clean-reconstruction-v2"


def canonical(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def requested_providers(trigger: dict[str, Any]) -> list[str]:
    if trigger.get("mode") != "explicit-one-shot":
        raise ValueError("force reconstruction trigger must use explicit-one-shot mode")
    raw = trigger.get("providers")
    if not isinstance(raw, list) or not raw:
        raise ValueError("force reconstruction trigger requires providers")
    out: list[str] = []
    for value in raw:
        provider_id = canonical(value)
        if provider_id and provider_id not in out:
            out.append(provider_id)
    if not out:
        raise ValueError("force reconstruction trigger contains no valid provider ids")
    return out


def completion_status(
    trigger: dict[str, Any],
    stage: dict[str, Any],
    provenance: dict[str, Any],
) -> tuple[bool, list[str]]:
    requested = requested_providers(trigger)
    candidates = {
        canonical(row.get("canonical_id") or row.get("upstream_id")): row
        for row in stage.get("candidates") or []
        if isinstance(row, dict)
    }
    provenance_rows = provenance.get("providers")
    if not isinstance(provenance_rows, dict):
        provenance_rows = {}

    missing: list[str] = []
    for provider_id in requested:
        candidate = candidates.get(provider_id)
        if not isinstance(candidate, dict):
            missing.append(f"{provider_id}:missing-stage-candidate")
            continue
        if candidate.get("clean_reconstruction_mode") is not True:
            missing.append(f"{provider_id}:force-mode-not-recorded")
        if str(candidate.get("candidate_code_origin") or "") != "new-niakvio-clean-seed":
            missing.append(f"{provider_id}:not-rebuilt-this-run")
        if candidate.get("provider_base_reconstruction_required") is not True:
            missing.append(f"{provider_id}:reconstruction-not-required-in-stage")
        if candidate.get("upstream_code_executed") is not False:
            missing.append(f"{provider_id}:upstream-code-execution-flag-invalid")
        if candidate.get("legacy_provider_js_executed_for_reconstruction") is not False:
            missing.append(f"{provider_id}:legacy-code-execution-flag-invalid")

        row = provenance_rows.get(provider_id)
        if not isinstance(row, dict):
            missing.append(f"{provider_id}:missing-provenance")
            continue
        if int(row.get("clean_reconstruction_authoring_version") or 0) < 2:
            missing.append(f"{provider_id}:old-authoring-version")
        source = str(row.get("base_source") or "")
        candidate_state = (
            source == CLEAN_CANDIDATE
            and row.get("clean_reconstruction_candidate") is True
            and row.get("clean_reconstruction_verified") is not True
        )
        verified_state = (
            source == CLEAN_VERIFIED
            and row.get("clean_reconstruction_verified") is True
        )
        if not (candidate_state or verified_state):
            missing.append(f"{provider_id}:reconstruction-not-materialized")
        origin = str(row.get("clean_reconstruction_candidate_origin") or "")
        if origin and origin != "new-niakvio-clean-seed":
            missing.append(f"{provider_id}:provenance-origin-mismatch")

    return not missing, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", type=Path, default=DEFAULT_TRIGGER)
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--consume", action="store_true")
    args = parser.parse_args()

    trigger_path = args.trigger.resolve()
    if not trigger_path.is_file():
        print("FIELD_FORCE_RECONSTRUCTION_TRIGGER state=absent")
        return 0
    if not args.stage.is_file() or not args.provenance.is_file():
        print("FIELD_FORCE_RECONSTRUCTION_TRIGGER state=pending reason=missing-stage-or-provenance")
        return 0

    trigger = load(trigger_path)
    stage = load(args.stage.resolve())
    provenance = load(args.provenance.resolve())
    complete, reasons = completion_status(trigger, stage, provenance)
    if not complete:
        print(
            "FIELD_FORCE_RECONSTRUCTION_TRIGGER state=pending reasons="
            + ",".join(reasons)
        )
        return 0

    providers = ",".join(requested_providers(trigger))
    if args.consume:
        trigger_path.unlink()
        print(
            "FIELD_FORCE_RECONSTRUCTION_TRIGGER state=consumed providers="
            + providers
        )
    else:
        print(
            "FIELD_FORCE_RECONSTRUCTION_TRIGGER state=ready providers="
            + providers
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
