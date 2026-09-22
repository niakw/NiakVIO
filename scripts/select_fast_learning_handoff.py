#!/usr/bin/env python3
"""Select the current Fast Repair -> LEARN handoff scope.

A handoff is valid only when the trigger explicitly identifies Fast Brain
strategy exhaustion and providers are simultaneously:
- pending/LEARN-owned in the sanitized handoff registry; and
- present in the current census repairQueue.

Historical handoff debt therefore cannot expand a current targeted Learning run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRIGGER = ROOT / ".github" / "triggers" / "brain-learning-reconstruction"
DEFAULT_HANDOFF = ROOT / "automation" / "provider-repair-learn-handoff-v1.json"
DEFAULT_CENSUS = ROOT / "automation" / "provider-census-status.json"


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def trigger_fields(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    fields: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        key = key.strip().casefold().replace("-", "_")
        value = value.strip()
        if key and value:
            fields[key] = value
    return fields


def trigger_is_fast_handoff(path: Path) -> bool:
    fields = trigger_fields(path)
    if not fields:
        return False
    reason = fields.get("reason", "")
    scope = fields.get("expected_scope", "")
    mode = fields.get("execution_mode", "")
    # Backward-compatible original Fast Repair marker.
    if (
        reason == "fast-brain-strategy-exhaustion"
        and scope == "current-fast-repair-handoff-only"
    ):
        return True
    # Versioned targeted handoff markers may evolve their descriptive reason or
    # exact cohort cardinality. The stable contract is an explicit
    # targeted-fast-handoff execution mode plus a provider-repair-handoff scope.
    return (
        mode.startswith("targeted-fast-handoff")
        and "provider-repair-handoff" in scope
    )


def select(trigger: Path, handoff: dict[str, Any], census: dict[str, Any]) -> list[str]:
    if not trigger_is_fast_handoff(trigger):
        return []
    repair = {cid(x) for x in census.get("repairQueue") or [] if cid(x)}
    rows = handoff.get("providers") if isinstance(handoff.get("providers"), dict) else {}
    out: list[str] = []
    for raw_provider, row in rows.items():
        provider = cid(raw_provider)
        if not provider or provider not in repair or not isinstance(row, dict):
            continue
        if str(row.get("owner") or "") != "LEARN":
            continue
        if str(row.get("status") or "") != "pending":
            continue
        out.append(provider)
    return sorted(set(out))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", type=Path, default=DEFAULT_TRIGGER)
    parser.add_argument("--handoff", type=Path, default=DEFAULT_HANDOFF)
    parser.add_argument("--census", type=Path, default=DEFAULT_CENSUS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    providers = select(args.trigger, load(args.handoff), load(args.census))
    payload = {
        "schemaVersion": 1,
        "fastHandoff": bool(providers),
        "providerCount": len(providers),
        "providers": providers,
        "providerFilter": ",".join(providers),
        "policy": "intersection of current repairQueue and pending sanitized LEARN handoff only",
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_FAST_LEARNING_HANDOFF "
        f"enabled={'true' if providers else 'false'} providers={len(providers)} "
        f"ids={','.join(providers) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
