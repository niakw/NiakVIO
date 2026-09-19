#!/usr/bin/env python3
"""Merge duplicate structured Provider plans without imposing a universal count cap.

Three top-level plans is the normal semantic shape, not a hard invariant.  Plans
with the same executable protocol are merged and their semanticTypes are unioned.
Distinct evidence-backed plans are preserved even when more than three remain,
because some providers legitimately need several independent resolvers or
language/player branches.

Internal steps inside one structured plan are always preserved; they are one
resolver recipe, not independent route alternatives.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
NORMAL_STRUCTURED_PLAN_TARGET = 3
MAX_STRUCTURED_PLANS = NORMAL_STRUCTURED_PLAN_TARGET  # compatibility alias
LANES = ("movie", "tv", "anime")
PLAN_FIELDS = (
    ("search_request_plan", "searchRequestPlan"),
    ("provider_value_plan", "providerValuePlan"),
    ("external_identity_plan", "externalIdentityPlan"),
)


def lane(value: object) -> str:
    value = str(value or "").strip().casefold()
    if value == "series":
        value = "tv"
    return value if value in LANES else ""


def lanes_for(plan: dict[str, Any]) -> set[str]:
    return {lane(value) for value in plan.get("semanticTypes") or [] if lane(value)}


def protocol_fingerprint(plan: dict[str, Any]) -> str:
    value = copy.deepcopy(plan)
    value.pop("semanticTypes", None)
    value.pop("proofFixture", None)
    value.pop("fixture", None)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def merge_equivalent(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    by_fp: dict[str, dict[str, Any]] = {}
    for raw in plans:
        if not isinstance(raw, dict):
            continue
        plan = copy.deepcopy(raw)
        fp = protocol_fingerprint(plan)
        current = by_fp.get(fp)
        if current is None:
            current = plan
            current["semanticTypes"] = sorted(lanes_for(plan))
            by_fp[fp] = current
            out.append(current)
        else:
            current["semanticTypes"] = sorted(lanes_for(current) | lanes_for(plan))
    return out


def cap_structured_plans(plans: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compatibility name: merge duplicates, never truncate distinct proven plans."""
    original = [copy.deepcopy(row) for row in plans if isinstance(row, dict)]
    merged = merge_equivalent(original)
    covered = set().union(*(lanes_for(row) for row in merged)) if merged else set()
    return merged, {
        "before": len(original),
        "afterMerge": len(merged),
        "after": len(merged),
        "coveredLanes": sorted(covered),
        "merged": len(merged) < len(original),
        "capped": False,
        "normalTarget": NORMAL_STRUCTURED_PLAN_TARGET,
        "targetExceeded": len(merged) > NORMAL_STRUCTURED_PLAN_TARGET,
        "exceptionReason": "distinct-evidence-backed-plans" if len(merged) > NORMAL_STRUCTURED_PLAN_TARGET else "",
    }


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def enforce_structured_plan_cap(
    *, overrides_path: Path = OVERRIDES, knowledge_path: Path = KNOWLEDGE
) -> dict[str, Any]:
    overrides = load(overrides_path)
    knowledge = load(knowledge_path)
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    changed_providers: set[str] = set()
    merged_fields = 0
    target_exceeded_fields = 0
    max_before = 0
    max_after = 0

    for provider_id, static_row in providers.items():
        if not isinstance(static_row, dict):
            continue
        patch = patches.get(provider_id)
        if not isinstance(patch, dict):
            continue
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        proof = model.get("routeProof") if isinstance(model.get("routeProof"), dict) else {}
        field_audit: dict[str, Any] = {}

        for patch_key, model_key in PLAN_FIELDS:
            source = patch.get(patch_key)
            if not isinstance(source, list):
                source = model.get(model_key)
            plans = [row for row in source or [] if isinstance(row, dict)]
            selected, audit = cap_structured_plans(plans)
            max_before = max(max_before, audit["before"])
            max_after = max(max_after, audit["after"])
            if audit["merged"]:
                merged_fields += 1
            if audit["targetExceeded"]:
                target_exceeded_fields += 1
            existing_model = [row for row in model.get(model_key) or [] if isinstance(row, dict)]
            existing_patch = [row for row in patch.get(patch_key) or [] if isinstance(row, dict)]
            if selected != existing_model or selected != existing_patch:
                changed_providers.add(provider_id)
            if selected:
                model[model_key] = copy.deepcopy(selected)
                patch[patch_key] = copy.deepcopy(selected)
            else:
                model.pop(model_key, None)
                patch.pop(patch_key, None)
            field_audit[model_key] = audit

        proof.pop("structuredRuntimePlanCap", None)
        proof["normalStructuredRuntimePlanTarget"] = NORMAL_STRUCTURED_PLAN_TARGET
        proof["structuredRuntimePlanPolicy"] = "merge-equivalent-preserve-distinct-evidence-backed-plans"
        proof["structuredRuntimePlanAudit"] = field_audit
        model["routeProof"] = proof
        patch["route_proof"] = copy.deepcopy(proof)
        static_row["model"] = model
        providers[provider_id] = static_row
        patches[provider_id] = patch

    overrides["provider_patches"] = patches
    knowledge["providers"] = providers
    write(overrides_path, overrides)
    write(knowledge_path, knowledge)
    return {
        "providerCount": len(providers),
        "changedProviders": len(changed_providers),
        "cappedFields": 0,
        "mergedFields": merged_fields,
        "targetExceededFields": target_exceeded_fields,
        "maxBefore": max_before,
        "maxAfter": max_after,
        "target": NORMAL_STRUCTURED_PLAN_TARGET,
        "cap": NORMAL_STRUCTURED_PLAN_TARGET,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    args = parser.parse_args()
    summary = enforce_structured_plan_cap(
        overrides_path=args.overrides if args.overrides.is_absolute() else ROOT / args.overrides,
        knowledge_path=args.knowledge if args.knowledge.is_absolute() else ROOT / args.knowledge,
    )
    print(
        "RUNTIME_STRUCTURED_PLAN_POLICY_V2_OK "
        f"providers={summary['providerCount']} changed={summary['changedProviders']} "
        f"merged_fields={summary['mergedFields']} target_exceeded_fields={summary['targetExceededFields']} "
        f"max_before={summary['maxBefore']} max_after={summary['maxAfter']} target={summary['target']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
