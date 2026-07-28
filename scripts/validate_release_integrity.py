#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))



def sha256(path: pathlib.Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def validate_hash_inventory(expected_version: str) -> list[str]:
    errors: list[str] = []
    for relative in ("SHA256SUMS.json", "FILE-HASHES.json"):
        payload = load(relative)
        if str(payload.get("release") or "") != expected_version:
            errors.append(f"{relative}: release field does not match {expected_version}")
        if payload.get("algorithm") != "sha256":
            errors.append(f"{relative}: unsupported algorithm {payload.get('algorithm')!r}")
        files = payload.get("files") or {}
        if not isinstance(files, dict):
            errors.append(f"{relative}: files must be an object")
            continue
        for filename, expected_hash in files.items():
            target = (ROOT / str(filename)).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{relative}: unsafe hash path {filename}")
                continue
            if not target.is_file():
                errors.append(f"{relative}: missing hashed file {filename}")
                continue
            actual = sha256(target)
            if actual != str(expected_hash):
                errors.append(f"{relative}: hash mismatch for {filename}")

    patch_path = ROOT / "PATCH-SHA256SUMS.txt"
    seen: set[str] = set()
    for number, line in enumerate(patch_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  \./(.+)", line)
        if not match:
            errors.append(f"PATCH-SHA256SUMS.txt:{number}: invalid line")
            continue
        expected_hash, filename = match.groups()
        if filename in seen:
            errors.append(f"PATCH-SHA256SUMS.txt:{number}: duplicate {filename}")
            continue
        seen.add(filename)
        target = (ROOT / filename).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"PATCH-SHA256SUMS.txt:{number}: unsafe path {filename}")
            continue
        if not target.is_file():
            errors.append(f"PATCH-SHA256SUMS.txt:{number}: missing {filename}")
        elif sha256(target) != expected_hash:
            errors.append(f"PATCH-SHA256SUMS.txt:{number}: hash mismatch for {filename}")
    return errors

def validate_manifest_paths(relative: str, *, nested: bool) -> list[str]:
    errors: list[str] = []
    manifest = load(relative)
    manifest_dir = (ROOT / relative).parent.resolve()
    seen: set[str] = set()
    for index, entry in enumerate(manifest.get("scrapers") or []):
        if not isinstance(entry, dict):
            errors.append(f"{relative}: scraper #{index} is not an object")
            continue
        provider_id = str(entry.get("id") or "").strip()
        filename = str(entry.get("filename") or "").strip()
        if not provider_id:
            errors.append(f"{relative}: scraper #{index} has no id")
        elif provider_id.casefold() in seen:
            errors.append(f"{relative}: duplicate provider id {provider_id}")
        seen.add(provider_id.casefold())
        if not filename:
            errors.append(f"{relative}:{provider_id}: missing filename")
            continue
        if filename.startswith(("http://", "https://", "/")):
            errors.append(f"{relative}:{provider_id}: external/absolute provider filename is forbidden: {filename}")
            continue
        if nested:
            if not filename.startswith("../providers/"):
                errors.append(f"{relative}:{provider_id}: nested filename must start ../providers/: {filename}")
        elif filename.startswith("../") or not filename.startswith("providers/"):
            errors.append(f"{relative}:{provider_id}: root filename must start providers/: {filename}")
        resolved = (manifest_dir / filename).resolve()
        try:
            resolved.relative_to((ROOT / "providers").resolve())
        except ValueError:
            errors.append(f"{relative}:{provider_id}: filename escapes providers/: {filename}")
            continue
        if not resolved.is_file():
            errors.append(f"{relative}:{provider_id}: referenced provider file does not exist: {filename}")
    return errors


def main() -> int:
    package = load("package.json")
    expected = str(package.get("version") or "")
    sources = load("sources.json")
    versions = {
        "package.json": expected,
        "manifest.json": load("manifest.json").get("version"),
        "vf/manifest.json": load("vf/manifest.json").get("version"),
        "sources.json.manifest_version": sources.get("manifest_version"),
        "sources.json.repository.manifest_version": (sources.get("repository") or {}).get("manifest_version"),
    }
    bad = {key: value for key, value in versions.items() if value != expected}
    if bad:
        raise SystemExit(f"version mismatch: expected {expected}, got {bad}")

    allowed = {
        "actions/checkout",
        "actions/setup-python",
        "actions/setup-node",
        "actions/upload-artifact",
        "actions/download-artifact",
    }
    pattern = re.compile(r"uses:\s*(actions/[^@\s]+)@([^\s#]+)")
    errors: list[str] = []
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        for line_number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
            match = pattern.search(line)
            if match and match.group(1) in allowed and not re.fullmatch(r"[0-9a-f]{40}", match.group(2)):
                errors.append(f"{workflow.relative_to(ROOT)}:{line_number}: {match.group(0)}")

    errors.extend(validate_manifest_paths("manifest.json", nested=False))
    errors.extend(validate_manifest_paths("vf/manifest.json", nested=True))
    errors.extend(validate_hash_inventory(expected))

    if errors:
        raise SystemExit("release integrity errors:\n" + "\n".join(errors))
    print("release integrity validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
