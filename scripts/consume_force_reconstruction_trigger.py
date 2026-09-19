#!/usr/bin/env python3
"""Consume explicit one-shot ProviderBase reconstruction requests after publication.

A one-shot request is consumed after the canonical publication transaction has
durably installed the exact forced clean ProviderBase SHA in PROVENANCE and
provider-bases/. Runtime activation stays separate: an unverified clean candidate
may keep the production LKG until strict Deep proof succeeds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from provider_base_store import (
    CLEAN_RECONSTRUCTION_AUTHORING_VERSION,
    CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE,
    CLEAN_RECONSTRUCTION_SOURCE,
    build_base_from_seed,
    build_clean_provider_seed,
    canonical_id,
    sha256,
)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def forced_candidates(registry: dict[str, Any], provider_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in registry.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        cid = canonical_id(str(row.get("canonical_id") or row.get("upstream_id") or ""))
        if cid != provider_id:
            continue
        if row.get("clean_reconstruction_mode") is not True:
            continue
        if str(row.get("candidate_code_origin") or "") != "new-niakvio-clean-seed":
            continue
        if row.get("provider_base_reconstruction_required") is not True:
            continue
        if row.get("upstream_code_executed") is not False:
            continue
        if row.get("legacy_provider_js_executed_for_reconstruction") is not False:
            continue
        result.append(row)
    return result


def expected_base_hashes(
    provider_id: str,
    candidates: list[dict[str, Any]],
    overrides_path: Path,
) -> set[str]:
    hashes: set[str] = set()
    for row in candidates:
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        model = row.get("clean_provider_model") if isinstance(row.get("clean_provider_model"), dict) else {}
        seed = build_clean_provider_seed(
            provider_id,
            metadata,
            known_site=str(row.get("observed_upstream_site") or "").strip() or None,
            provider_model=model,
        )
        base_data, _stripped = build_base_from_seed(
            provider_id,
            seed,
            overrides_path=overrides_path,
        )
        hashes.add(sha256(base_data))
    return hashes


def durable_base_matches(
    provider_id: str,
    provenance_row: dict[str, Any] | None,
    expected_hashes: set[str],
    root: Path,
) -> bool:
    if not isinstance(provenance_row, dict) or not expected_hashes:
        return False
    source = str(provenance_row.get("base_source") or "")
    verified = (
        source == CLEAN_RECONSTRUCTION_SOURCE
        and provenance_row.get("clean_reconstruction_verified") is True
        and provenance_row.get("clean_reconstruction_required") is not True
    )
    materialized_candidate = (
        source == CLEAN_RECONSTRUCTION_CANDIDATE_SOURCE
        and provenance_row.get("clean_reconstruction_candidate") is True
        and provenance_row.get("clean_reconstruction_verified") is not True
        and provenance_row.get("clean_reconstruction_required") is True
        and int(provenance_row.get("clean_reconstruction_authoring_version") or 0)
        >= CLEAN_RECONSTRUCTION_AUTHORING_VERSION
        and provenance_row.get("legacy_provider_js_executed_for_reconstruction") is False
        and provenance_row.get("upstream_code_executed") is False
    )
    if not (verified or materialized_candidate):
        return False
    digest = str(provenance_row.get("base_sha256") or "").strip()
    relative = str(provenance_row.get("base_filename") or "").strip()
    if digest not in expected_hashes or not relative.startswith("provider-bases/"):
        return False
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    if not path.is_file() or sha256(path.read_bytes()) != digest:
        return False
    return True



def consume(
    trigger_path: Path,
    registry_path: Path,
    provenance_path: Path,
    overrides_path: Path,
    root: Path,
) -> tuple[list[str], list[str]]:
    if not trigger_path.is_file():
        return [], []

    trigger = load_object(trigger_path)
    if trigger.get("mode") != "explicit-one-shot":
        raise ValueError("force reconstruction trigger mode must be explicit-one-shot")
    if trigger.get("remove_after_materialization") is not True:
        raise ValueError("force reconstruction trigger must opt into removal after materialization")

    requested = []
    for raw in trigger.get("providers") or []:
        cid = canonical_id(str(raw or ""))
        if cid and cid not in requested:
            requested.append(cid)
    if not requested:
        raise ValueError("force reconstruction trigger has no providers")

    registry = load_object(registry_path)
    provenance = load_object(provenance_path)
    provenance_rows = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}

    consumed: list[str] = []
    remaining: list[str] = []
    for provider_id in requested:
        candidates = forced_candidates(registry, provider_id)
        expected = expected_base_hashes(provider_id, candidates, overrides_path)
        if durable_base_matches(
            provider_id,
            provenance_rows.get(provider_id),
            expected,
            root,
        ):
            consumed.append(provider_id)
        else:
            remaining.append(provider_id)

    if remaining:
        trigger["providers"] = remaining
        previous = [
            canonical_id(str(value or ""))
            for value in trigger.get("consumedProviders") or []
            if canonical_id(str(value or ""))
        ]
        trigger["consumedProviders"] = list(dict.fromkeys(previous + consumed))
        trigger_path.write_text(
            json.dumps(trigger, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        trigger_path.unlink()

    return consumed, remaining


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", type=Path, required=True)
    parser.add_argument("--stage-registry", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    consumed, remaining = consume(
        args.trigger.resolve(),
        args.stage_registry.resolve(),
        args.provenance.resolve(),
        args.overrides.resolve(),
        args.root.resolve(),
    )
    print(
        "FIELD_FORCE_RECONSTRUCTION_TRIGGER "
        f"consumed={','.join(consumed) or '-'} remaining={','.join(remaining) or '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
