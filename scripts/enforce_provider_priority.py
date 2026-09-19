#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Keep stable provider ordering in published Nuvio manifests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (ROOT / "manifest.json", ROOT / "vf" / "manifest.json")
PRIORITY = ("anime-sama", "purstream", "goated")


def canonical(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def reorder(path: Path) -> bool:
    if not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("scrapers")
    if not isinstance(rows, list):
        raise ValueError(f"invalid manifest structure: {path}")
    original = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    rank = {provider_id: index for index, provider_id in enumerate(PRIORITY)}
    indexed = list(enumerate(rows))
    indexed.sort(key=lambda item: (rank.get(canonical(item[1].get("id") if isinstance(item[1], dict) else ""), len(rank)), item[0]))
    payload["scrapers"] = [row for _index, row in indexed]
    changed = json.dumps(payload["scrapers"], ensure_ascii=False, sort_keys=True) != original
    if changed:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    changed = [str(path.relative_to(ROOT)) for path in MANIFESTS if reorder(path)]
    print("provider priority updated: " + (", ".join(changed) if changed else "already current"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
