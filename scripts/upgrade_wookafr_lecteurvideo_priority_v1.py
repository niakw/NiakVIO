#!/usr/bin/env python3
"""Wire the WookaFR lecteurvideo seed-priority Lego into canonical DATA."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
SCRIPT = "scripts/provider_patches/wookafr_lecteurvideo_priority_v1.py"


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    patches = value.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get("wookafr"), dict):
        raise AssertionError("provider-overrides.json missing wookafr provider patch row")
    return value


def patch() -> bool:
    value = load()
    row = value["provider_patches"]["wookafr"]
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)
    scripts = [str(v) for v in row.get("provider_lego_scripts") or [] if str(v).strip()]
    if SCRIPT not in scripts:
        scripts.append(SCRIPT)
    row["provider_lego_scripts"] = scripts
    opts = row.get("provider_lego_options")
    if not isinstance(opts, dict):
        opts = {}
    opts[SCRIPT] = {"priority_host": "lecteurvideo.com"}
    row["provider_lego_options"] = opts
    notes = [str(v) for v in row.get("notes") or []]
    note = "Wooka player crawl preserves all discovered embeds but prioritizes lecteurvideo.com before the ProviderBase bounded seed budget; current lecteurvideo pages are structurally parsed and still pass shared terminal/identity guards."
    if note not in notes:
        notes.append(note)
    row["notes"] = notes
    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    row = load()["provider_patches"]["wookafr"]
    if SCRIPT not in [str(v) for v in row.get("provider_lego_scripts") or []]:
        raise AssertionError("wookafr priority Lego missing")
    opts = row.get("provider_lego_options") or {}
    if (opts.get(SCRIPT) or {}).get("priority_host") != "lecteurvideo.com":
        raise AssertionError("wookafr priority host mismatch")
    types = {str(v).lower() for v in row.get("published_types") or []}
    if types != {"movie", "tv"}:
        raise AssertionError(f"wookafr capability drift: {sorted(types)}")


def main() -> int:
    changed = patch()
    validate()
    print(f"WOOKAFR_LECTEURVIDEO_PRIORITY_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
