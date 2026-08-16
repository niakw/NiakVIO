#!/usr/bin/env python3
"""Export the exact Nuvio client commits accepted by the release guard.

Native proofs must exercise the same official client revisions that NiakVIO's
upstream compatibility fence accepted. Keeping SHAs in one generated state
(`sources.json`) prevents native workflows from silently testing stale clients.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"^[0-9a-f]{40}$")
ENV_NAMES = {
    "nuvio-desktop": "NUVIO_DESKTOP_SHA",
    "nuvio-mobile": "NUVIO_MOBILE_SHA",
    "nuvio-tv": "NUVIO_TV_SHA",
}


def resolve_refs(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    clients = (
        payload.get("nuvio_client_compatibility", {}).get("clients", {})
        if isinstance(payload, dict)
        else {}
    )
    result: dict[str, str] = {}
    for client, env_name in ENV_NAMES.items():
        row = clients.get(client)
        if not isinstance(row, dict):
            raise RuntimeError(f"missing accepted Nuvio client state: {client}")
        ref = str(row.get("accepted_ref") or "").strip().lower()
        if not SHA.fullmatch(ref):
            raise RuntimeError(f"invalid accepted ref for {client}: {ref!r}")
        result[env_name] = ref
    if len(set(result.values())) != len(result):
        # Different repositories may technically have identical SHA-1s, but that
        # is sufficiently unexpected here to catch copy/paste state corruption.
        raise RuntimeError("Nuvio client accepted refs unexpectedly collide")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    refs = resolve_refs(args.sources.resolve())
    if args.json:
        print(json.dumps(refs, sort_keys=True))
    else:
        for key, value in refs.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
