#!/usr/bin/env python3
"""Build the physical Hub-46 manifest consumed by official native clients.

Official Nuvio clients derive relative plugin URLs by stripping the literal suffix
``/manifest.json`` from the repository URL. A root file named
``manifest-hub46.json`` therefore cannot be a production-faithful repository
transport: relative provider URLs resolve under the wrong base.

This builder keeps the terminal transport filename ``manifest.json`` and rewrites
every provider filename to an absolute raw-GitHub URL pinned to one immutable
provider-source SHA. The transport manifest itself may live at
``native-hub46/manifest.json`` without copying provider bundles into that directory.

The result is exactly the Hub-46 set; the global 96-provider catalogue remains
untouched.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"
DEFAULT_SOURCE = ROOT / "manifest-hub46.json"
DEFAULT_OUTPUT = ROOT / "native-hub46" / "manifest.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON object required: {path}")
    return value


def scope_ids(path: Path) -> set[str]:
    data = load(path)
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = {
        cid(row.get("manifestId") or row.get("provider"))
        for row in rows
        if isinstance(row, dict) and cid(row.get("manifestId") or row.get("provider"))
    }
    expected = int(data.get("hubCount") or data.get("providerCount") or len(ids))
    if expected != 46 or len(ids) != 46:
        raise SystemExit(f"Hub-46 scope mismatch: ids={len(ids)} expected={expected}")
    return ids


def provider_repo_path(filename: object, repository: str) -> str:
    raw = str(filename or "").strip()
    if not raw:
        raise SystemExit("provider filename missing")
    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        if parsed.hostname != "raw.githubusercontent.com":
            raise SystemExit(f"non-repository provider URL cannot be pinned: {raw}")
        parts = [part for part in parsed.path.split("/") if part]
        repo_parts = repository.split("/", 1)
        if len(repo_parts) != 2 or len(parts) < 4:
            raise SystemExit(f"invalid repository/provider URL: {raw}")
        if parts[0].casefold() != repo_parts[0].casefold() or parts[1].casefold() != repo_parts[1].casefold():
            raise SystemExit(f"provider URL belongs to another repository: {raw}")
        try:
            index = parts.index("providers", 3)
        except ValueError as error:
            raise SystemExit(f"provider URL does not point to providers/: {raw}") from error
        return "/".join(parts[index:])
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "providers":
        raise SystemExit(f"unsafe provider path: {raw}")
    return path.as_posix()


def git_has(sha: str, path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:{path}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def build(
    source: dict[str, Any],
    *,
    scoped: set[str],
    repository: str,
    provider_sha: str,
    verify_git: bool,
) -> dict[str, Any]:
    if not SHA_RE.fullmatch(provider_sha):
        raise SystemExit(f"provider SHA must be 40 lowercase hex: {provider_sha}")
    if repository.count("/") != 1 or any(not part.strip() for part in repository.split("/")):
        raise SystemExit(f"invalid repository: {repository}")

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_row in source.get("scrapers") or []:
        if not isinstance(raw_row, dict):
            continue
        provider_id = cid(raw_row.get("id"))
        if provider_id not in scoped:
            continue
        if provider_id in seen:
            raise SystemExit(f"duplicate provider in source manifest: {provider_id}")
        seen.add(provider_id)
        row = dict(raw_row)
        path = provider_repo_path(row.get("filename"), repository)
        if verify_git and not git_has(provider_sha, path):
            raise SystemExit(f"provider bundle absent at frozen SHA: {provider_id} {provider_sha}:{path}")
        row["filename"] = f"https://raw.githubusercontent.com/{repository}/{provider_sha}/{path}"
        selected.append(row)

    missing = sorted(scoped - seen)
    extra = sorted(seen - scoped)
    if missing or extra or len(selected) != 46:
        raise SystemExit(
            f"physical Hub-46 mismatch selected={len(selected)} missing={','.join(missing)} extra={','.join(extra)}"
        )

    out = dict(source)
    out["scrapers"] = selected
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-sha", required=True)
    parser.add_argument("--repository", default="niakw/NiakVIO")
    parser.add_argument("--scope-matrix", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-git-verify", action="store_true")
    args = parser.parse_args()

    scope = args.scope_matrix if args.scope_matrix.is_absolute() else ROOT / args.scope_matrix
    source_path = args.source if args.source.is_absolute() else ROOT / args.source
    output = args.output if args.output.is_absolute() else ROOT / args.output
    payload = build(
        load(source_path),
        scoped=scope_ids(scope),
        repository=args.repository,
        provider_sha=args.provider_sha,
        verify_git=not args.no_git_verify,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_NATIVE_HUB46_TRANSPORT_BUILT "
        f"providers=46 provider_sha={args.provider_sha} output={output.relative_to(ROOT)} "
        "terminal_name=manifest.json absolute_provider_urls=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
