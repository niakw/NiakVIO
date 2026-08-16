#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Remove stale hard-disable flags that are not safety quarantines.

NiakVIO activation is evidence-driven. A historical ``manifest_overrides.enabled
= false`` must not permanently suppress a provider that later has current
playable/identity proof. Only explicit safety quarantines remain hard-disabled.

A safety quarantine is explicit when the provider capability is ``quarantined``,
a quarantine patch is configured, or a dedicated ``safety_quarantine`` flag is
set. Publication-scoped audit quarantine bundles are intentionally not encoded
here; a fresh upstream sibling may recover from those after strict current proof
and the final catalogue/media audit.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
QUARANTINE_PATCH = "quarantine_provider_v1.py"


def is_configured_safety_quarantine(patch: Any) -> bool:
    if not isinstance(patch, dict):
        return False
    if patch.get("safety_quarantine") is True:
        return True
    if str(patch.get("capability") or "").strip().casefold() == "quarantined":
        return True
    scripts = [str(value) for value in patch.get("patch_scripts") or []]
    legacy = str(patch.get("patch_script") or "")
    if legacy:
        scripts.append(legacy)
    return any(
        value.replace("\\", "/").endswith("/" + QUARANTINE_PATCH)
        or value == QUARANTINE_PATCH
        for value in scripts
    )


def normalize(config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    output = copy.deepcopy(config)
    patches = output.get("provider_patches")
    if not isinstance(patches, dict):
        return output, []

    released: list[str] = []
    for raw_id, patch in patches.items():
        if not isinstance(patch, dict) or is_configured_safety_quarantine(patch):
            continue
        manifest_overrides = patch.get("manifest_overrides")
        if not isinstance(manifest_overrides, dict):
            continue
        if manifest_overrides.get("enabled") is False:
            manifest_overrides.pop("enabled", None)
            released.append(str(raw_id).casefold())

    meta = output.setdefault("provider_engine_normalization", {})
    if isinstance(meta, dict):
        previous = {
            str(value).casefold()
            for value in meta.get("non_safety_hard_disables_released") or []
            if str(value).strip()
        }
        recorded = sorted(previous | set(released))
        meta["non_safety_hard_disables_released"] = recorded
        meta["non_safety_hard_disable_count"] = len(recorded)
    return output, sorted(released)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    path = args.config.resolve()
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    normalized, released = normalize(value)

    if args.check:
        if normalized != value:
            raise SystemExit(
                "provider activation overrides are not normalized; recoverable hard disables: "
                + ", ".join(released)
            )
    else:
        path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    meta = normalized.get("provider_engine_normalization") or {}
    recorded = [
        str(value)
        for value in (meta.get("non_safety_hard_disables_released") or [])
        if str(value)
    ] if isinstance(meta, dict) else []
    print(
        "provider activation override normalization passed: "
        f"released_now={len(released)} recorded_total={len(recorded)}"
        + (" ids=" + ",".join(released) if released else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
