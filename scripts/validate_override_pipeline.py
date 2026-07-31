#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate that configured provider overrides reached the staged artefacts.

Validator revision: idempotent-terminal-v3.

This is an end-to-end guard: it inspects staging/candidates.json and the exact
JavaScript files later executed and promoted. A unit test of string replacement
alone cannot catch a workflow that accidentally validates or publishes the
unpatched upstream file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"


def canonical(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")



def terminal_replacement(value: str, replacements: dict[str, object]) -> str:
    """Resolve chained replacements without requiring intermediate hosts to remain."""
    current = str(value)
    seen: set[str] = set()
    while current in replacements and current not in seen:
        seen.add(current)
        current = str(replacements[current])
    return current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    args = parser.parse_args()
    stage = args.stage.resolve()
    registry_path = stage / "candidates.json"
    if not registry_path.exists():
        raise SystemExit(f"missing staged candidate registry: {registry_path}")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    candidates = registry.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit("staging/candidates.json has no candidates array")

    global_replacements = config.get("domain_replacements") or {}
    provider_patches = config.get("provider_patches") or {}
    patch_profiles = config.get("patch_profiles") or {}
    failures: list[str] = []
    checked = 0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        provider_id = canonical(candidate.get("canonical_id") or candidate.get("upstream_id"))
        replacements = dict(global_replacements)
        specific = provider_patches.get(provider_id, {})
        required_values = []
        specific_replacements: dict[str, object] = {}
        if isinstance(specific, dict):
            specific_replacements.update(specific.get("replacements") or {})
            specific_replacements.update(specific.get("route_replacements") or {})
            specific_replacements.update(specific.get("runtime_domain_replacements") or {})
            replacements.update(specific_replacements)
            required_values = list(specific.get("required_values") or [])
            required_values.extend(specific.get("required_route_values") or [])
        records = candidate.get("local_patches") or []
        applied_profiles = {
            str(record.get("profile")) for record in records
            if isinstance(record, dict) and record.get("type") == "patch_profile"
        }
        for profile_name in applied_profiles:
            profile = patch_profiles.get(profile_name, {})
            if isinstance(profile, dict):
                required_values.extend(profile.get("required_values") or [])
        if not replacements and not required_values:
            continue

        local_path = (stage / str(candidate.get("local_path") or "")).resolve()
        try:
            local_path.relative_to((stage / "providers").resolve())
        except ValueError:
            failures.append(f"{candidate.get('key')}: unsafe staged path {local_path}")
            continue
        if not local_path.exists():
            failures.append(f"{candidate.get('key')}: missing staged file {local_path}")
            continue

        data = local_path.read_bytes()
        text = data.decode("utf-8", errors="strict")
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != candidate.get("sha256"):
            failures.append(f"{candidate.get('key')}: staged SHA differs from candidates.json")

        replacement_records = [
            record for record in records
            if isinstance(record, dict)
            and record.get("type") == "replace"
            and int(record.get("count", 0) or 0) > 0
        ]
        for old, new in replacements.items():
            old, new = str(old), str(new)
            matching_records = [
                record for record in replacement_records
                if str(record.get("from")) == old
                and str(record.get("to")) == new
            ]
            if old in text:
                failures.append(f"{candidate.get('key')}: forbidden pre-override value remains: {old}")
            terminal = terminal_replacement(new, replacements)
            if matching_records and terminal not in text:
                failures.append(
                    f"{candidate.get('key')}: patch recorded but terminal replacement absent: {terminal}"
                )

        # Provider-specific override contracts are idempotent:
        #   1. an old value is replaced and the terminal target must exist;
        #   2. the terminal target already exists, which is also success;
        #   3. neither source nor target is represented, indicating a stale
        #      override or a provider structure change that needs review.
        # Global replacements are intentionally excluded from this presence
        # contract because they are offered to every provider bundle.
        terminal_groups: dict[str, set[str]] = {}
        for old, new in specific_replacements.items():
            terminal = terminal_replacement(str(new), replacements)
            terminal_groups.setdefault(terminal, set()).add(str(old))
        for terminal, historical_values in terminal_groups.items():
            related_record = any(
                str(record.get("from")) in historical_values
                for record in replacement_records
            )
            if terminal in text:
                continue
            if related_record:
                failures.append(
                    f"{candidate.get('key')}: override applied but terminal target missing: {terminal}"
                )
                continue
            failures.append(
                f"{candidate.get('key')}: override stale; neither historical value nor terminal target is represented: {terminal}"
            )

        for required in required_values:
            required = str(required)
            terminal_required = terminal_replacement(required, replacements)
            if required in text or terminal_required in text:
                continue
            failures.append(
                f"{candidate.get('key')}: required value missing from staged file: {required}"
            )
        # Metadata-only records (and legacy string markers such as
        # ``published_baseline``) do not prove that the JavaScript was mutated.
        # Only records emitted by apply_provider_overrides after a real content
        # change may require the patched SHA to differ from the upstream SHA.
        effective_records = [
            record for record in records
            if isinstance(record, dict)
            and (
                record.get("type") in {"patch_profile", "patch_script", "fixed_endpoint"}
                or int(record.get("count", 0) or 0) > 0
            )
        ]
        if effective_records and candidate.get("upstream_sha256") == candidate.get("sha256"):
            failures.append(f"{candidate.get('key')}: effective patches recorded but upstream and patched SHA are equal")
        checked += 1


    if failures:
        print("Override pipeline validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"override pipeline validation passed ({checked} staged candidates inspected; validator=idempotent-terminal-v3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
