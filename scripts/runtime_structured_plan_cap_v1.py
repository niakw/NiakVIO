#!/usr/bin/env python3
"""Cap all structured executable Provider plans to <=3 semantic alternatives.

HTTP proof can contain many observations. Runtime alternatives cannot. Identical
protocol plans proven by multiple semantic fixtures are merged and their
semanticTypes are unioned. Remaining alternatives are selected by semantic
coverage, with a hard maximum of movie/tv/anime = 3 top-level plans.

Internal steps inside one structured plan are preserved; they are a recipe, not
independent runtime alternatives.
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
MAX_STRUCTURED_PLANS = 3
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
    # Proof bookkeeping does not define a different runtime protocol.
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


def plan_score(plan: dict[str, Any], index: int) -> int:
    coverage = len(lanes_for(plan))
    score = coverage * 10000
    role = str(plan.get("sourceRole") or "").casefold()
    if "provider-value" in role:
        score += 700
    elif "catalog-search" in role or "search" in role:
        score += 650
    elif "external" in role:
        score += 600
    try:
        proof = int(plan.get("proofModelVersion") or 0)
    except (TypeError, ValueError):
        proof = 0
    score += min(proof, 100) * 10
    # Stable preference for the earlier proof when all else is equal.
    score += max(0, 100 - min(index, 100))
    return score


def cap_structured_plans(plans: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    original = [copy.deepcopy(row) for row in plans if isinstance(row, dict)]
    merged = merge_equivalent(original)
    if len(merged) <= MAX_STRUCTURED_PLANS:
        covered = set().union(*(lanes_for(row) for row in merged)) if merged else set()
        return merged, {
            "before": len(original),
            "afterMerge": len(merged),
            "after": len(merged),
            "coveredLanes": sorted(covered),
            "capped": len(merged) < len(original),
        }

    universe = set().union(*(lanes_for(row) for row in merged)) if merged else set()
    selected: list[dict[str, Any]] = []
    remaining = set(universe)
    indexed = list(enumerate(merged))

    while remaining and len(selected) < MAX_STRUCTURED_PLANS:
        candidates: list[tuple[int, int, int, dict[str, Any]]] = []
        for index, plan in indexed:
            if plan in selected:
                continue
            fresh = lanes_for(plan) & remaining
            if not fresh:
                continue
            candidates.append((len(fresh), plan_score(plan, index), -index, plan))
        if not candidates:
            break
        _coverage, _score, _stable, best = max(candidates, key=lambda item: item[:3])
        selected.append(best)
        remaining -= lanes_for(best)

    if not selected:
        selected = [row for _index, row in sorted(indexed, key=lambda pair: plan_score(pair[1], pair[0]), reverse=True)[:MAX_STRUCTURED_PLANS]]
    else:
        for index, plan in sorted(indexed, key=lambda pair: plan_score(pair[1], pair[0]), reverse=True):
            if len(selected) >= MAX_STRUCTURED_PLANS:
                break
            if plan not in selected:
                selected.append(plan)

    selected = selected[:MAX_STRUCTURED_PLANS]
    covered = set().union(*(lanes_for(row) for row in selected)) if selected else set()
    return selected, {
        "before": len(original),
        "afterMerge": len(merged),
        "after": len(selected),
        "coveredLanes": sorted(covered),
        "capped": len(selected) < len(original),
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
    capped_fields = 0
    merged_fields = 0
    max_before = 0
    max_after = 0
    violations: list[str] = []

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
            if audit["after"] > MAX_STRUCTURED_PLANS:
                violations.append(f"{provider_id}:{model_key}:{audit['after']}")
                continue
            if audit["capped"]:
                capped_fields += 1
            if audit["afterMerge"] < audit["before"]:
                merged_fields += 1
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

        proof["structuredRuntimePlanCap"] = MAX_STRUCTURED_PLANS
        proof["structuredRuntimePlanAudit"] = field_audit
        model["routeProof"] = proof
        patch["route_proof"] = copy.deepcopy(proof)
        static_row["model"] = model
        providers[provider_id] = static_row
        patches[provider_id] = patch

    if violations:
        raise RuntimeError("structured runtime plan cap violated: " + ",".join(violations[:20]))

    overrides["provider_patches"] = patches
    knowledge["providers"] = providers
    write(overrides_path, overrides)
    write(knowledge_path, knowledge)
    return {
        "providerCount": len(providers),
        "changedProviders": len(changed_providers),
        "cappedFields": capped_fields,
        "mergedFields": merged_fields,
        "maxBefore": max_before,
        "maxAfter": max_after,
        "cap": MAX_STRUCTURED_PLANS,
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
        "RUNTIME_STRUCTURED_PLAN_CAP_V1_OK "
        f"providers={summary['providerCount']} changed={summary['changedProviders']} "
        f"capped_fields={summary['cappedFields']} merged_fields={summary['mergedFields']} "
        f"max_before={summary['maxBefore']} max_after={summary['maxAfter']} cap={summary['cap']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
