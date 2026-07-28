#!/usr/bin/env python3
"""Align every release-version field with the promoted manifest version."""
from __future__ import annotations

import argparse
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="Explicit authoritative version")
    parser.add_argument(
        "--manifest",
        default="manifest.json",
        help="Manifest containing the authoritative version",
    )
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    manifest = load(manifest_path)
    version = args.version or str(manifest.get("version", ""))
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"invalid authoritative release version: {version!r}")

    package_path = ROOT / "package.json"
    package = load(package_path)
    package["version"] = version
    dump(package_path, package)

    sources_path = ROOT / "sources.json"
    sources = load(sources_path)
    sources["manifest_version"] = version
    repository = sources.setdefault("repository", {})
    repository["manifest_version"] = version
    if "version" in repository:
        repository["version"] = version
    dump(sources_path, sources)

    for relative in ("manifest.json", "vf/manifest.json"):
        path = ROOT / relative
        payload = load(path)
        payload["version"] = version
        dump(path, payload)

    print(f"release versions synchronized to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
