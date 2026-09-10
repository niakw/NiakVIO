#!/usr/bin/env python3
"""Remove non-concrete address constructors from provider-hubs.json.

This is a conservative preflight for the scheduled Domain Refresh. It never
invents a provider address: when `direct` is invalid it may only reuse the first
already-curated concrete direct candidate, otherwise it becomes null. Historical
concrete candidates are preserved.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
from pathlib import Path
from typing import Any

PLACEHOLDER_TOKENS = ("${", "{{", "}}", "<%", "%>", "{", "}")


def concrete_http(value: object) -> bool:
    raw = str(value or "").strip()
    if not raw or any(token in raw for token in PLACEHOLDER_TOKENS):
        return False
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.casefold()
    return not any(token in hostname for token in ("$", "{", "}"))


def host(value: object) -> str:
    raw = str(value or "").strip()
    if "://" not in raw:
        raw = "https://" + raw
    return (urllib.parse.urlparse(raw).hostname or "").casefold().strip(".")


def dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.rstrip("/").casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def sanitize(document: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    providers = document.get("providers")
    if not isinstance(providers, dict):
        raise AssertionError("provider-hubs.json providers must be an object")

    changed: list[str] = []
    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        before = json.dumps(row, ensure_ascii=False, sort_keys=True)

        candidates = dedupe([
            str(value).strip()
            for value in row.get("direct_candidates") or []
            if concrete_http(value)
        ])
        row["direct_candidates"] = candidates

        direct = row.get("direct")
        if not concrete_http(direct):
            row["direct"] = candidates[0] if candidates else None
        elif str(direct).rstrip("/").casefold() not in {
            value.rstrip("/").casefold() for value in candidates
        }:
            row["direct_candidates"] = dedupe([str(direct).strip(), *candidates])

        allowed: list[str] = []
        for value in row.get("allowed_terminal_hosts") or []:
            raw = str(value or "").strip().casefold().strip(".")
            if not raw or any(token in raw for token in PLACEHOLDER_TOKENS):
                continue
            if raw not in allowed:
                allowed.append(raw)
        for value in row.get("direct_candidates") or []:
            hostname = host(value)
            if hostname and hostname not in allowed:
                allowed.append(hostname)
        row["allowed_terminal_hosts"] = allowed

        after = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if before != after:
            changed.append(str(provider_id))

    return document, sorted(changed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="provider-hubs.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    path = Path(args.registry)
    document = json.loads(path.read_text(encoding="utf-8"))
    document, changed = sanitize(document)
    if args.check and changed:
        raise SystemExit(f"provider hub registry requires sanitization: {','.join(changed)}")
    if changed and not args.check:
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_HUB_REGISTRY_SANITIZE "
        f"changed={len(changed)} providers={','.join(changed) if changed else '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
