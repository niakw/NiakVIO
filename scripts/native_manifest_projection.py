#!/usr/bin/env python3
"""Canonical NiakVIO manifest projection authority for native clients and CI.

Published user-facing manifests:
- manifest.json
- vf/manifest.json
- no-anime/manifest.json
- vf-no-anime/manifest.json

Native runtime acceptance executes Global and VF directly. The no-anime
variants remain published functional subsets and are validated without
duplicating expensive device execution.
"""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from current_provider_scope import projection_active_provider_ids  # noqa: E402

EXECUTION_MANIFESTS = ("manifest.json", "vf/manifest.json")
VARIANT_MANIFESTS = ("no-anime/manifest.json", "vf-no-anime/manifest.json")
PUBLISHED_MANIFESTS = EXECUTION_MANIFESTS + VARIANT_MANIFESTS
RETIRED_TRACKED_MANIFESTS = ("manifest-hub46.json", "native-hub46/manifest.json")


def cid(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def manifest_path(relative: str) -> Path:
    if relative not in PUBLISHED_MANIFESTS:
        raise ValueError(f"unsupported canonical manifest: {relative}")
    return ROOT / relative


def load_manifest(relative: str) -> dict[str, Any]:
    return json.loads(manifest_path(relative).read_text(encoding="utf-8"))


def rows(relative: str, *, active_only: bool = False) -> list[dict[str, Any]]:
    out = [row for row in load_manifest(relative).get("scrapers") or [] if isinstance(row, dict)]
    return [row for row in out if row.get("enabled") is True] if active_only else out


def active_ids(relative: str) -> set[str]:
    return {cid(row.get("id")) for row in rows(relative, active_only=True) if cid(row.get("id"))}


def execution_active_union_ids() -> set[str]:
    return set().union(*(active_ids(relative) for relative in EXECUTION_MANIFESTS))


def active_provider_manifest(provider: str) -> str:
    wanted = cid(provider)
    if not wanted:
        raise ValueError("provider id is required")
    for relative in EXECUTION_MANIFESTS:
        if wanted in active_ids(relative):
            return relative
    raise ValueError(f"provider is not active in Global or VF: {provider}")


def validate(*, require_retired_absent: bool = False) -> dict[str, Any]:
    versions: dict[str, str] = {}
    ids_by_manifest: dict[str, set[str]] = {}
    for relative in PUBLISHED_MANIFESTS:
        path = manifest_path(relative)
        data = load_manifest(relative)
        versions[relative] = str(data.get("version") or "")
        seen: set[str] = set()
        for row in rows(relative):
            provider = cid(row.get("id"))
            if not provider or provider in seen:
                raise RuntimeError(f"{relative}: invalid/duplicate provider id {provider!r}")
            seen.add(provider)
            filename = str(row.get("filename") or "").strip()
            if not filename or filename.startswith(("http://", "https://")):
                raise RuntimeError(f"{relative}:{provider}: filename must be repository-relative")
            source = (path.parent / filename).resolve()
            try:
                repo_relative = source.relative_to(ROOT.resolve())
            except ValueError as exc:
                raise RuntimeError(f"{relative}:{provider}: provider path escapes repository") from exc
            if not repo_relative.parts or repo_relative.parts[0] not in {"providers", "provider-disabled"}:
                raise RuntimeError(f"{relative}:{provider}: provider path outside lifecycle stores: {repo_relative}")
            if "provider-old" in repo_relative.parts:
                raise RuntimeError(f"{relative}:{provider}: archived provider leaked into publication")
            if not source.is_file():
                raise RuntimeError(f"{relative}:{provider}: provider file missing: {repo_relative}")
        ids_by_manifest[relative] = seen

    values = set(versions.values())
    if len(values) != 1:
        raise RuntimeError(f"published manifest version drift: {versions}")
    if not ids_by_manifest["no-anime/manifest.json"] <= ids_by_manifest["manifest.json"]:
        raise RuntimeError("no-anime must remain a Global subset")
    if not ids_by_manifest["vf-no-anime/manifest.json"] <= ids_by_manifest["vf/manifest.json"]:
        raise RuntimeError("vf-no-anime must remain a VF subset")

    active_union = execution_active_union_ids()
    expected = projection_active_provider_ids()
    if active_union != expected:
        raise RuntimeError(
            "canonical native execution union drift "
            f"missing={sorted(expected-active_union)} extra={sorted(active_union-expected)}"
        )
    retired_present = [relative for relative in RETIRED_TRACKED_MANIFESTS if (ROOT / relative).exists()]
    if require_retired_absent and retired_present:
        raise RuntimeError("retired tracked transport still exists: " + ",".join(retired_present))
    return {
        "version": next(iter(values)),
        "globalActive": len(active_ids("manifest.json")),
        "vfActive": len(active_ids("vf/manifest.json")),
        "activeUnion": len(active_union),
        "sharedActive": len(active_ids("manifest.json") & active_ids("vf/manifest.json")),
        "retiredPresent": retired_present,
    }


def ephemeral_active_union() -> dict[str, Any]:
    """Build an untracked diagnostic union; never use this as publication."""
    validate()
    global_doc = load_manifest("manifest.json")
    vf_doc = load_manifest("vf/manifest.json")
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for relative, doc in (("manifest.json", global_doc), ("vf/manifest.json", vf_doc)):
        base = manifest_path(relative).parent
        for row in doc.get("scrapers") or []:
            if not isinstance(row, dict) or row.get("enabled") is not True:
                continue
            provider = cid(row.get("id"))
            if not provider or provider in seen:
                continue
            seen.add(provider)
            copy = deepcopy(row)
            source = (base / str(row.get("filename") or "")).resolve()
            copy["filename"] = source.relative_to(ROOT.resolve()).as_posix()
            merged.append(copy)
    out = {key: deepcopy(value) for key, value in global_doc.items() if key != "scrapers"}
    out["scrapers"] = merged
    out["diagnosticScope"] = {
        "ephemeral": True,
        "authority": "manifest.json + vf/manifest.json active union",
        "providerCount": len(merged),
    }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate")
    check.add_argument("--require-retired-absent", action="store_true")
    select = sub.add_parser("select-provider")
    select.add_argument("provider")
    union = sub.add_parser("write-active-union")
    union.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "validate":
        print(json.dumps(validate(require_retired_absent=args.require_retired_absent), sort_keys=True))
        return 0
    if args.command == "select-provider":
        print(active_provider_manifest(args.provider))
        return 0
    if args.command == "write-active-union":
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ephemeral_active_union(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(path)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
