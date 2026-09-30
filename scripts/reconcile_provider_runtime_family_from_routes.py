#!/usr/bin/env python3
"""Reclassify selected Provider v3 runtime families from current route DATA.

Used after targeted route recognition. A stale non-unknown runtime family must
not survive when the provider's current route shape now proves a different
generic runtime family. This script changes only the selected providers in
automation/provider-v3-static-knowledge.json; it never edits provider runtime
code or Core.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sanitize_provider_v3_core_metadata_routes import derive_runtime_family

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()

    path = args.knowledge if args.knowledge.is_absolute() else ROOT / args.knowledge
    payload = json.loads(path.read_text(encoding="utf-8"))
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ValueError("static knowledge providers object missing")

    requested = {canon(value) for value in args.provider if canon(value)}
    if not requested:
        raise ValueError("at least one --provider is required")

    changed: list[dict[str, str]] = []
    seen: set[str] = set()
    for provider_id, raw in providers.items():
        pid = canon(provider_id)
        if pid not in requested or not isinstance(raw, dict):
            continue
        seen.add(pid)
        model = raw.get("model") if isinstance(raw.get("model"), dict) else {}
        knowledge = raw.get("knowledge") if isinstance(raw.get("knowledge"), dict) else {}
        current = str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold() or "unknown"
        inferred = derive_runtime_family(model, respect_current=False)
        if inferred == "unknown" or inferred == current:
            continue
        model["sourceRuntimeFamily"] = inferred
        knowledge["runtimeFamily"] = inferred
        raw["model"] = model
        raw["knowledge"] = knowledge
        changed.append({
            "provider": pid,
            "before": current,
            "after": inferred,
        })

    missing = sorted(requested - seen)
    if missing:
        raise ValueError("provider(s) missing from static knowledge: " + ",".join(missing))

    if changed:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(
        "FIELD_PROVIDER_RUNTIME_FAMILY_RECONCILE "
        f"requested={len(requested)} changed={len(changed)} "
        f"rows={json.dumps(changed, ensure_ascii=True, separators=(',', ':'))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
