#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re

from route_proof_activation_preservation_v1 import validate as validate_activation_preservation

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROOT_MANIFEST = "manifest.json"
HUB46_MANIFEST = "manifest-hub46.json"
NATIVE_HUB46_MANIFEST = "native-hub46/manifest.json"
VF_MANIFEST = "vf/manifest.json"
NO_ANIME_MANIFEST = "no-anime/manifest.json"
VF_NO_ANIME_MANIFEST = "vf-no-anime/manifest.json"


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


def validate_manifest_paths(relative: str, *, nested: bool, allow_disabled: bool = True) -> list[str]:
    """Validate manifest provider references against lifecycle-owned directories.

    ``providers/`` is executable/active publication. ``provider-disabled/`` is a
    distinct, non-executable retention scope for providers that remain visible in
    catalogue projections while explicitly ``enabled: false``.  Never infer
    disabled state from the path itself: the row flag owns the transition and the
    path must agree with it.  Active-only manifests (Hub46) set
    ``allow_disabled=False`` so a disabled row cannot leak into execution scope.
    """
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
        disabled = entry.get("enabled") is False
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

        if disabled and not allow_disabled:
            errors.append(f"{relative}:{provider_id}: disabled provider is forbidden in active-only manifest")
            continue

        lifecycle_dir = "provider-disabled" if disabled else "providers"
        expected_prefix = f"../{lifecycle_dir}/" if nested else f"{lifecycle_dir}/"
        if not filename.startswith(expected_prefix):
            state = "disabled" if disabled else "active"
            errors.append(
                f"{relative}:{provider_id}: {state} filename must start {expected_prefix}: {filename}"
            )

        resolved = (manifest_dir / filename).resolve()
        lifecycle_root = (ROOT / lifecycle_dir).resolve()
        try:
            resolved.relative_to(lifecycle_root)
        except ValueError:
            errors.append(
                f"{relative}:{provider_id}: filename escapes {lifecycle_dir}/ lifecycle scope: {filename}"
            )
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
        ROOT_MANIFEST: load(ROOT_MANIFEST).get("version"),
        HUB46_MANIFEST: load(HUB46_MANIFEST).get("version"),
        NATIVE_HUB46_MANIFEST: load(NATIVE_HUB46_MANIFEST).get("version"),
        VF_MANIFEST: load(VF_MANIFEST).get("version"),
        NO_ANIME_MANIFEST: load(NO_ANIME_MANIFEST).get("version"),
        VF_NO_ANIME_MANIFEST: load(VF_NO_ANIME_MANIFEST).get("version"),
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

    errors.extend(validate_manifest_paths(ROOT_MANIFEST, nested=False))
    errors.extend(validate_manifest_paths(HUB46_MANIFEST, nested=False, allow_disabled=False))
    errors.extend(validate_manifest_paths(VF_MANIFEST, nested=True))
    errors.extend(validate_manifest_paths(NO_ANIME_MANIFEST, nested=True))
    errors.extend(validate_manifest_paths(VF_NO_ANIME_MANIFEST, nested=True))
    # native-hub46 intentionally contains absolute raw-GitHub provider URLs pinned
    # to the accepted provider SHA. Its transport shape is validated by the
    # dedicated native_hub46_transport_manifest_test instead of the relative-path gate.
    if os.environ.get("NUVIO_SKIP_ACTIVATION_PRESERVATION") != "1":
        errors.extend(validate_activation_preservation())
    else:
        print("FIELD_RELEASE_INTEGRITY activation_preservation=skipped owner=domain_refresh")
    errors.extend(validate_hash_inventory(expected))

    if errors:
        raise SystemExit("release integrity errors:\n" + "\n".join(errors))
    print("release integrity validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
