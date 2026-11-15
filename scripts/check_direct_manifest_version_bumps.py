#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
MANIFESTS = ("manifest.json", "vf/manifest.json")


def parse_semver(value: object) -> tuple[int, int, int] | None:
    match = SEMVER.fullmatch(str(value or "").strip())
    return tuple(map(int, match.groups())) if match else None


def canonical_id(value: object) -> str:
    return str(value or "").strip().casefold()


def normalize_name(value: object) -> str:
    text = str(value or "").strip()
    return re.sub(r"^NiakVIO(?:\s+v\d+\.\d+\.\d+)?(?=\s*(?:—|$))", "NiakVIO", text, count=1)


def comparable_manifest(value: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(value))
    clone.pop("version", None)
    if "name" in clone:
        clone["name"] = normalize_name(clone.get("name"))
    return clone


def comparable_provider(value: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(value))
    clone.pop("version", None)
    return clone


def load_current(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{relative}: object required")
    return value


def load_at(base: str, relative: str) -> dict[str, Any] | None:
    proc = subprocess.run(
        ["git", "show", f"{base}:{relative}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise RuntimeError(f"{base}:{relative}: object required")
    return value


def repo_provider_path(manifest_rel: str, filename: object) -> str | None:
    raw = str(filename or "").strip()
    if not raw or raw.startswith(("http://", "https://")):
        return None
    base = (Path(manifest_rel).parent / raw).resolve()
    try:
        rel = base.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None
    return rel


def blob_at(base: str, relative: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{base}:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def rows_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        cid = canonical_id(row.get("id"))
        if not cid:
            continue
        if cid in rows:
            raise RuntimeError(f"duplicate provider id: {cid}")
        rows[cid] = row
    return rows


def validate_pair(
    label: str,
    old: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    old_release = parse_semver(old.get("version"))
    current_release = parse_semver(current.get("version"))

    if comparable_manifest(old) != comparable_manifest(current):
        if old_release is None or current_release is None or current_release <= old_release:
            errors.append(
                f"{label}: client-visible manifest changed without release bump "
                f"old={old.get('version')} current={current.get('version')}"
            )

    old_rows = rows_by_id(old)
    current_rows = rows_by_id(current)
    for cid, row in current_rows.items():
        version = parse_semver(row.get("version"))
        if version is None:
            errors.append(f"{label}:{cid}: invalid provider version {row.get('version')!r}")
            continue
        previous = old_rows.get(cid)
        if previous is None:
            continue
        if comparable_provider(previous) == comparable_provider(row):
            continue
        previous_version = parse_semver(previous.get("version"))
        if previous_version is None or version <= previous_version:
            errors.append(
                f"{label}:{cid}: provider row changed without provider bump "
                f"old={previous.get('version')} current={row.get('version')}"
            )
    return errors


def validate_in_place_bytes(
    base: str,
    manifest_rel: str,
    old: dict[str, Any],
    current: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    old_rows = rows_by_id(old)
    current_rows = rows_by_id(current)
    for cid in sorted(set(old_rows) & set(current_rows)):
        old_rel = repo_provider_path(manifest_rel, old_rows[cid].get("filename"))
        current_rel = repo_provider_path(manifest_rel, current_rows[cid].get("filename"))
        if not old_rel or old_rel != current_rel:
            continue
        old_bytes = blob_at(base, old_rel)
        current_path = ROOT / current_rel
        if old_bytes is None or not current_path.is_file():
            continue
        current_bytes = current_path.read_bytes()
        if hashlib.sha256(old_bytes).digest() != hashlib.sha256(current_bytes).digest():
            errors.append(
                f"{manifest_rel}:{cid}: content-addressed provider mutated in place at {current_rel}; "
                "publish a new filename and bump the provider version"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD^")
    args = parser.parse_args()

    errors: list[str] = []
    checked = 0
    for manifest_rel in MANIFESTS:
        current_path = ROOT / manifest_rel
        if not current_path.is_file():
            continue
        old = load_at(args.base, manifest_rel)
        if old is None:
            continue
        current = load_current(manifest_rel)
        checked += 1
        errors.extend(validate_pair(manifest_rel, old, current))
        errors.extend(validate_in_place_bytes(args.base, manifest_rel, old, current))

    if errors:
        for error in errors:
            print(f"VERSION_BUMP_GUARD_FAIL {error}")
        return 1

    print(f"VERSION_BUMP_GUARD_OK manifests={checked} base={args.base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
