#!/usr/bin/env python3
"""Scope sanitized Brain guidance to the exact canonical Repair cohort."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def scope_payload(payload: dict[str, Any], providers: list[str]) -> tuple[dict[str, Any], list[str]]:
    wanted: list[str] = []
    seen: set[str] = set()
    for raw in providers:
        provider = canon(raw)
        if provider and provider not in seen:
            seen.add(provider)
            wanted.append(provider)

    out = json.loads(json.dumps(payload))
    rows = out.get("rows")
    if not isinstance(rows, list):
        raise ValueError("guidance rows missing")

    if wanted:
        wanted_set = set(wanted)
        rows = [
            row for row in rows
            if isinstance(row, dict) and canon(row.get("providerId")) in wanted_set
        ]

    out["rows"] = rows
    out["providerCount"] = len({
        canon(row.get("providerId"))
        for row in rows
        if isinstance(row, dict) and canon(row.get("providerId"))
    })
    present = sorted({
        canon(row.get("providerId"))
        for row in rows
        if isinstance(row, dict) and canon(row.get("providerId"))
    })
    return out, present


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--provider", action="append", default=[])
    p.add_argument("--providers", default="")
    args = p.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("guidance payload must be an object")
    requested = [*args.provider, *str(args.providers or "").split(",")]
    scoped, present = scope_payload(payload, requested)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scoped, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    wanted = sorted({canon(value) for value in requested if canon(value)})
    print(
        "FIELD_CANONICAL_REPAIR_GUIDANCE_SCOPE "
        f"requested={','.join(wanted) or 'global'} "
        f"present={','.join(present) or 'none'} "
        f"providers={scoped.get('providerCount', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
