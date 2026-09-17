#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "automation" / "provider-v3-static-knowledge.json"

ALLOWED_MODEL_KEYS = {"officialSite", "knownSite", "officialHub", "origins", "observedUrls"}
ALLOWED_RECIPE_KEYS = {"referer", "referrer"}


def load(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: object required")
    return value


def canon(value: object) -> str:
    return str(value or "").strip().casefold()


def touched_ids(changes: dict[str, Any]) -> set[str]:
    return {canon(value) for value in changes.get("changed") or [] if canon(value)}


def strip_allowed_model(model: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(model)
    for key in ALLOWED_MODEL_KEYS:
        out.pop(key, None)
    recipe = out.get("apiRecipe")
    if isinstance(recipe, dict):
        for key in ALLOWED_RECIPE_KEYS:
            recipe.pop(key, None)
        if not recipe:
            out.pop("apiRecipe", None)
    return out


def validate(before: dict[str, Any], after: dict[str, Any], touched: set[str]) -> None:
    before_top = {k: v for k, v in before.items() if k != "providers"}
    after_top = {k: v for k, v in after.items() if k != "providers"}
    if before_top != after_top:
        raise AssertionError("Domain Refresh mutated static-knowledge top-level metadata")

    before_rows = before.get("providers") or {}
    after_rows = after.get("providers") or {}
    if not isinstance(before_rows, dict) or not isinstance(after_rows, dict):
        raise AssertionError("static providers object required")
    if set(before_rows) != set(after_rows):
        raise AssertionError("Domain Refresh may not add/remove static providers")

    for raw_pid in sorted(before_rows):
        pid = canon(raw_pid)
        b = before_rows[raw_pid]
        a = after_rows[raw_pid]
        if not isinstance(b, dict) or not isinstance(a, dict):
            if b != a:
                raise AssertionError(f"{pid}: static row mutated")
            continue
        if pid not in touched:
            if b != a:
                raise AssertionError(f"{pid}: untouched static knowledge mutated")
            continue

        b_without_model = {k: v for k, v in b.items() if k != "model"}
        a_without_model = {k: v for k, v in a.items() if k != "model"}
        if b_without_model != a_without_model:
            raise AssertionError(f"{pid}: Domain Refresh mutated non-model static evidence")
        bm = b.get("model")
        am = a.get("model")
        if not isinstance(bm, dict) or not isinstance(am, dict):
            raise AssertionError(f"{pid}: static model missing")
        if strip_allowed_model(bm) != strip_allowed_model(am):
            raise AssertionError(f"{pid}: Domain Refresh mutated non-address static model data")
        if bm.get("routeData") != am.get("routeData"):
            raise AssertionError(f"{pid}: routeData proof changed during Domain Refresh")
        if bm.get("strategy") != am.get("strategy"):
            raise AssertionError(f"{pid}: strategy changed during Domain Refresh")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-static", required=True)
    parser.add_argument("--after-static", default=str(STATIC))
    parser.add_argument("--changes", default="health-output/domain-site-changes.json")
    args = parser.parse_args()
    before = load(args.before_static)
    after = load(args.after_static)
    changes = load(args.changes)
    touched = touched_ids(changes)
    validate(before, after, touched)
    print(
        "FIELD_DOMAIN_STATIC_NON_DESTRUCTIVE "
        + json.dumps({
            "changed": sorted(touched),
            "repair_evidence_preserved": True,
            "unrelated_static_churn": False,
        }, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
