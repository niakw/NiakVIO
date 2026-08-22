#!/usr/bin/env python3
"""Export the exact Nuvio client commits accepted by the canonical runtime guard.

The audited client registry in ``automation/nuvio-client-upstreams.json`` is the
single source of truth for client refs. ``sources.json`` may retain historical
accepted-ref diagnostics, but native proofs must never derive their checkout SHA
from that mutable/reporting state.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "automation" / "nuvio-client-upstreams.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
ENV_NAMES = {
    "nuvio-desktop": "NUVIO_DESKTOP_SHA",
    "nuvio-mobile": "NUVIO_MOBILE_SHA",
    "nuvio-tv": "NUVIO_TV_SHA",
}


def resolve_refs(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    clients = payload.get("clients", {}) if isinstance(payload, dict) else {}
    result: dict[str, str] = {}
    for client, env_name in ENV_NAMES.items():
        row = clients.get(client)
        if not isinstance(row, dict):
            raise RuntimeError(f"missing audited Nuvio client registry row: {client}")
        ref = str(row.get("verified_ref") or "").strip().lower()
        if not SHA.fullmatch(ref):
            raise RuntimeError(f"invalid verified ref for {client}: {ref!r}")
        result[env_name] = ref
    if len(set(result.values())) != len(result):
        # Different repositories may technically have identical SHA-1s, but that
        # is sufficiently unexpected here to catch copy/paste state corruption.
        raise RuntimeError("Nuvio client verified refs unexpectedly collide")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    refs = resolve_refs(args.registry.resolve())
    if args.json:
        print(json.dumps(refs, sort_keys=True))
    else:
        for key, value in refs.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
