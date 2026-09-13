#!/usr/bin/env python3
"""Plan the next adaptive native-Lab fixture from one completed fixture log.

A provider rotates only when its declared route completed successfully with count=0.
Any runtime error, provider-load error, identity contradiction, transport/player error,
or positive result removes that provider from rotation. The next fixture is selected
from the same global lane only, one title at a time.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rotating_corpus import canonical_lane, fixture_by_slug, rotated_candidates  # noqa: E402

FIELD_RE = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")


def fields(line: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for match in FIELD_RE.finditer(line)}


def decode(value: str) -> str:
    if not value:
        return ""
    text = value.replace("-", "+").replace("_", "/")
    text += "=" * ((4 - len(text) % 4) % 4)
    try:
        return base64.b64decode(text).decode("utf-8")
    except Exception:
        return ""


def provider_from(f: dict[str, str]) -> str:
    return decode(f.get("provider64", "")) or f.get("provider", "")


def clean_miss_providers(paths: list[Path], fixture: str) -> list[str]:
    states: dict[str, dict[str, bool]] = {}
    for path in paths:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            marker = raw.find("FIELD_NATIVE_")
            if marker < 0:
                continue
            line = raw[marker:].strip()
            f = fields(line)
            if f.get("fixture") and f.get("fixture") != fixture:
                continue
            provider = provider_from(f).strip()
            if not provider:
                continue
            state = states.setdefault(provider.casefold(), {"zero": False, "positive": False, "error": False, "skip": False})
            route_mode = str(f.get("route_mode") or "declared").casefold()
            if route_mode == "capability_probe":
                continue
            if line.startswith("FIELD_NATIVE_RESULT "):
                count = int(f.get("count") or 0)
                if count > 0:
                    state["positive"] = True
                else:
                    state["zero"] = True
            elif line.startswith(("FIELD_NATIVE_ERROR ", "FIELD_NATIVE_PROVIDER_LOAD_ERROR ", "FIELD_NATIVE_RUNTIME_ERROR ")):
                state["error"] = True
            elif line.startswith("FIELD_NATIVE_PROVIDER_SKIPPED "):
                state["skip"] = True
            elif line.startswith(("FIELD_NATIVE_CONTRADICTION ", "FIELD_NATIVE_TRANSPORT_FAILURE ", "FIELD_NATIVE_PLAYER_FAILURE ")):
                state["error"] = True
    return sorted(
        provider for provider, state in states.items()
        if state["zero"] and not state["positive"] and not state["error"] and not state["skip"]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--log", action="append", required=True)
    parser.add_argument("--used", action="append", default=[])
    parser.add_argument("--seed", default=None)
    parser.add_argument("--providers-out", required=True)
    parser.add_argument("--fixture-out", required=True)
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    fixture = fixture_by_slug(args.fixture)
    lane = canonical_lane(fixture)
    providers = clean_miss_providers([Path(value) for value in args.log], args.fixture)
    used = {args.fixture, *[str(value).strip() for value in args.used if str(value).strip()]}
    next_fixture = ""
    if providers:
        candidates = rotated_candidates(lane, seed=args.seed, exclude=used)
        if candidates:
            next_fixture = candidates[0]["slug"]

    Path(args.providers_out).write_text("\n".join(providers) + ("\n" if providers else ""), encoding="utf-8")
    Path(args.fixture_out).write_text(next_fixture + ("\n" if next_fixture else ""), encoding="utf-8")
    payload = {
        "fixture": args.fixture,
        "lane": lane,
        "cleanMissProviders": providers,
        "nextFixture": next_fixture or None,
        "used": sorted(used),
        "action": "rotate" if providers and next_fixture else ("exhausted" if providers else "stop"),
        "rule": "rotate_only_clean_zero_no_error",
    }
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"FIELD_NATIVE_CATALOG_ROTATION fixture={args.fixture} lane={lane} "
        f"clean_miss={len(providers)} next={next_fixture or 'none'} action={payload['action']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
