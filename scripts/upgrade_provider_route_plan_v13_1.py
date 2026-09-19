#!/usr/bin/env python3
"""V13.1: deterministic owner for the two shared recipe placeholder maps.

`_recipeUrl` and `_recipeExpandScalar` intentionally contain the same replacement
fragment. V13 patches both. The normal migration helper is strict for every other
anchor; only these two labels are allowed to consume one of two identical anchors
sequentially.
"""
from __future__ import annotations

import upgrade_provider_route_plan_v13 as v13

_original_once = v13.once


def _v13_once(text: str, old: str, new: str, label: str) -> str:
    if label in {"recipe-url-imdb-placeholder", "recipe-scalar-imdb-placeholder"}:
        count = text.count(old)
        if count < 1:
            raise AssertionError(f"{label}: expected remaining shared placeholder anchor, got {count}")
        return text.replace(old, new, 1)
    return _original_once(text, old, new, label)


def main() -> int:
    v13.once = _v13_once
    changed = v13.patch_recovery() | v13.patch_materializer() | v13.patch_base()
    v13.validate_recovery()
    v13.validate_materializer()
    v13.validate_base()
    print(
        f"PROVIDER_ROUTE_PLAN_V13_1_OK changed={str(changed).lower()} "
        "strict_anchors_preserved=1 shared_placeholder_maps=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
