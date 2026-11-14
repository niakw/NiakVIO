#!/usr/bin/env python3
"""Keep a stable manifest URL while forcing Nuvio to notice activation transitions.

Nuvio preserves the previous local `enabled` value when the scraper identifier is
unchanged. The identifier is `<manifest URL>:<provider id>`. We therefore keep a
stable URL and toggle only the *case* of a provider id when it transitions from
manifest-disabled to manifest-enabled. Repository tooling compares provider ids
case-insensitively, while Nuvio treats the resulting scraper id as a new entry.

Official client-runtime compatibility refs are tracked separately in `sources.json`;
this module only manages provider cache/activation identity and never approves a
Mobile, Desktop or TV runtime-contract change. A known linear
`contract_review_required` remains an adaptation/native-review signal rather than
a provider-pipeline veto; unverifiable or divergent client history stays fail-closed.

The provider pipeline watches this compatibility primitive, so a reviewed change
here intentionally receives an independent Quick validation before Deep/learning.
This checkpoint follows the repository-wide cleanup of historical quarantine-state
assumptions so recovered providers are validated from their current runtime state.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "nuvio-client-id-state.json"
MAIN_PATH = ROOT / "manifest.json"
VF_PATH = ROOT / "vf" / "manifest.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_id(value: object) -> str:
    return str(value or "").strip().casefold()


def alternate_client_id(current: str, canonical: str) -> str:
    return canonical.lower() if current == canonical.upper() else canonical.upper()


def bump_patch(value: object) -> str:
    match = SEMVER.fullmatch(str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def vf_filename(value: object) -> str:
    filename = str(value or "").strip()
    if not filename or filename.startswith(("http://", "https://", "../")):
        return filename
    if filename.startswith(("providers/", "provider-disabled/")):
        return f"../{filename}"
    return filename


def apply_policy(*, bootstrap_active: bool = False) -> dict[str, Any]:
    main = load(MAIN_PATH)
    vf = load(VF_PATH)
    state = load(STATE_PATH) if STATE_PATH.exists() else {
        "schema_version": 2,
        "strategy": "case-toggle-on-disabled-to-enabled",
        "providers": {},
    }
    providers_state = state.setdefault("providers", {})

    main_rows = [row for row in main.get("scrapers", []) if isinstance(row, dict)]
    vf_rows = [row for row in vf.get("scrapers", []) if isinstance(row, dict)]
    changed_ids: list[str] = []
    activation_transitions: list[str] = []
    main_by_canonical: dict[str, dict[str, Any]] = {}
    visible_ids: set[str] = set()

    def apply_identity(row: dict[str, Any], *, scope: str) -> str:
        canonical = canonical_id(row.get("id"))
        if not canonical:
            raise RuntimeError("provider without client identity")
        enabled = row.get("enabled") is True
        previous = providers_state.get(canonical)

        if bootstrap_active:
            desired_id = canonical.upper() if enabled else canonical.lower()
            transition = enabled
        elif isinstance(previous, dict):
            previous_enabled = previous.get("enabled") is True
            desired_id = str(previous.get("client_id") or canonical)
            transition = enabled and not previous_enabled
            if transition:
                desired_id = alternate_client_id(desired_id, canonical)
        else:
            desired_id = canonical.upper() if enabled else canonical.lower()
            transition = False

        if row.get("id") != desired_id:
            row["id"] = desired_id
            changed_ids.append(canonical)
        if (bootstrap_active and enabled) or transition:
            row["version"] = bump_patch(row.get("version"))
            activation_transitions.append(canonical)

        providers_state[canonical] = {
            "client_id": desired_id,
            "enabled": enabled,
            "scope": scope,
        }
        visible_ids.add(canonical)
        return canonical

    for row in main_rows:
        canonical = canonical_id(row.get("id"))
        if not canonical or canonical in main_by_canonical:
            raise RuntimeError(f"invalid or duplicate provider id: {row.get('id')!r}")
        apply_identity(row, scope="global")
        main_by_canonical[canonical] = row

    # VF contains shared Global rows plus first-class France-only rows. Shared
    # rows inherit the Global client identity; a France-only row owns its own
    # activation transition and must never be forced into manifest.json.
    vf_seen: set[str] = set()
    france_only_count = 0
    for row in vf_rows:
        canonical = canonical_id(row.get("id"))
        if not canonical or canonical in vf_seen:
            raise RuntimeError(f"invalid or duplicate VF provider id: {row.get('id')!r}")
        vf_seen.add(canonical)
        source = main_by_canonical.get(canonical)
        if source is None:
            france_only_count += 1
            apply_identity(row, scope="france")
            continue

        visible_ids.add(canonical)
        row["id"] = source["id"]
        row["version"] = source.get("version")
        row["filename"] = vf_filename(source.get("filename"))
        row["enabled"] = source.get("enabled") is True
        row["supportedTypes"] = source.get("supportedTypes", [])
        for optional in (
            "hasSettings",
            "formats",
            "supportedFormats",
            "contentLanguage",
            "supportsExternalPlayer",
            "limited",
            "disabledPlatforms",
            "supportedPlatforms",
        ):
            if optional in source:
                row[optional] = source[optional]
            else:
                row.pop(optional, None)

    for canonical in sorted(set(providers_state) - visible_ids):
        providers_state.pop(canonical, None)

    state["schema_version"] = 2
    state["strategy"] = "case-toggle-on-disabled-to-enabled"
    state["manifest_url"] = "https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/manifest.json"
    state["vf_manifest_url"] = "https://raw.githubusercontent.com/niakw/Niakvio/refs/heads/main/vf/manifest.json"
    state["active_count"] = sum(1 for row in main_rows if row.get("enabled") is True)
    state["vf_active_count"] = sum(1 for row in vf_rows if row.get("enabled") is True)
    state["visible_count"] = len(visible_ids)
    state["france_only_count"] = france_only_count

    dump(MAIN_PATH, main)
    dump(VF_PATH, vf)
    dump(STATE_PATH, state)

    return {
        "changed_ids": sorted(set(changed_ids)),
        "activation_transitions": sorted(set(activation_transitions)),
        "active_count": state["active_count"],
        "vf_active_count": state["vf_active_count"],
        "visible_count": state["visible_count"],
        "france_only_count": state["france_only_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bootstrap-active",
        action="store_true",
        help="Give every currently enabled provider a fresh client id once.",
    )
    args = parser.parse_args()
    result = apply_policy(bootstrap_active=args.bootstrap_active)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
