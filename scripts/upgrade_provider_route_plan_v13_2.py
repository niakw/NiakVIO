#!/usr/bin/env python3
"""V13.2: add the standard-library regex dependency used by V13 recovery."""
from __future__ import annotations

import upgrade_provider_route_plan_v13 as v13
import upgrade_provider_route_plan_v13_1 as v13_1


def ensure_re_import() -> bool:
    text = v13.RECOVERY.read_text(encoding="utf-8")
    if "\nimport re\n" in text:
        return False
    anchor = "import os\n"
    if text.count(anchor) != 1:
        raise AssertionError("V13.2 recovery import anchor drift")
    text = text.replace(anchor, anchor + "import re\n", 1)
    v13.RECOVERY.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    imported = ensure_re_import()
    v13_1._original_once = v13.once
    changed = bool(imported)
    # Run the V13.1 deterministic migration after dependency ownership is fixed.
    v13.once = v13_1._v13_once
    changed = bool(v13.patch_recovery() | v13.patch_materializer() | v13.patch_base() | changed)
    v13.validate_recovery()
    v13.validate_materializer()
    v13.validate_base()
    print(
        f"PROVIDER_ROUTE_PLAN_V13_2_OK changed={str(changed).lower()} "
        "regex_dependency=stdlib-re shared_placeholder_maps=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
