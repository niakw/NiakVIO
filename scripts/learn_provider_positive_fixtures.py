#!/usr/bin/env python3
"""Merge fresh playable lane witnesses into the Brain's positive-fixture memory.

Only a current exact-bundle ``playable_verified`` witness may become positive
fixture memory. Failed runs never erase a previous witness; they mark it stale so
Learning can try it first and then search for a replacement.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CERTIFICATION = ROOT / "automation/provider-playable-certification.json"
DEFAULT_REGISTRY = ROOT / "automation/provider-positive-fixtures.json"


def load(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def merge(certification: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    providers = registry.get("providers") if isinstance(registry.get("providers"), dict) else {}
    providers = dict(providers)
    generated_at = certification.get("generatedAt")
    manifest_version = certification.get("manifestVersion")

    seen: set[str] = set()
    for raw in certification.get("providers") or []:
        if not isinstance(raw, dict):
            continue
        provider = canon(raw.get("providerId"))
        if not provider:
            continue
        seen.add(provider)
        current = providers.get(provider) if isinstance(providers.get(provider), dict) else {}
        current = dict(current)
        current["providerId"] = provider
        current["lastObservedBundleSha256"] = raw.get("bundleSha256")
        current["lastObservedFilename"] = raw.get("filename")
        current["lastObservedManifestVersion"] = manifest_version
        current["lastObservedAt"] = generated_at
        current["certified"] = bool(raw.get("certified"))
        current["requiredTypes"] = list(raw.get("requiredTypes") or [])
        current["certifiedTypes"] = list(raw.get("certifiedTypes") or [])
        current["missingTypes"] = list(raw.get("missingTypes") or [])
        lanes = current.get("lanes") if isinstance(current.get("lanes"), dict) else {}
        lanes = dict(lanes)
        fresh_lanes = raw.get("lanes") if isinstance(raw.get("lanes"), dict) else {}
        for lane in raw.get("requiredTypes") or []:
            lane = canon(lane)
            if not lane:
                continue
            fresh = fresh_lanes.get(lane) if isinstance(fresh_lanes.get(lane), dict) else {}
            old = lanes.get(lane) if isinstance(lanes.get(lane), dict) else {}
            old = dict(old)
            if fresh.get("state") == "certified" and fresh.get("fixtureSlug"):
                slug = str(fresh["fixtureSlug"])
                known = [str(value) for value in old.get("knownPositiveFixtures") or [] if str(value)]
                if slug in known:
                    known.remove(slug)
                known.insert(0, slug)
                old.update({
                    "state": "certified",
                    "fixtureSlug": slug,
                    "fixture": fresh.get("fixture"),
                    "knownPositiveFixtures": known[:12],
                    "bundleSha256": raw.get("bundleSha256"),
                    "filename": raw.get("filename"),
                    "manifestVersion": manifest_version,
                    "lastVerifiedAt": generated_at,
                    "source": "exact-bundle-playable-lane-certification-v1",
                })
            else:
                old["state"] = "stale-or-unverified"
                old["lastFailedAt"] = generated_at
                old["lastFailedBundleSha256"] = raw.get("bundleSha256")
            lanes[lane] = old
        current["lanes"] = lanes
        providers[provider] = current

    for provider, raw in list(providers.items()):
        if provider in seen or not isinstance(raw, dict):
            continue
        stale = dict(raw)
        stale["certified"] = False
        stale["registryState"] = "not-observed-in-latest-certification"
        providers[provider] = stale

    return {
        "schemaVersion": 1,
        "authority": "provider-positive-fixture-memory-v1",
        "updatedAt": generated_at,
        "sourceManifestVersion": manifest_version,
        "providers": dict(sorted(providers.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certification", type=Path, default=DEFAULT_CERTIFICATION)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    certification = load(args.certification.resolve(), {})
    if certification.get("authority") != "exact-bundle-playable-lane-certification-v1":
        raise SystemExit("playable certification authority required")
    registry = load(args.registry.resolve(), {"providers": {}})
    output = args.output.resolve() if args.output else args.registry.resolve()
    merged = merge(certification, registry)
    write(output, merged)
    certified = sum(1 for row in merged["providers"].values() if isinstance(row, dict) and row.get("certified"))
    print(f"FIELD_PROVIDER_POSITIVE_FIXTURE_MEMORY providers={len(merged['providers'])} certified={certified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
