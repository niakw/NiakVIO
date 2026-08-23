#!/usr/bin/env python3
"""Delete stale content-hashed provider bundles not referenced by published state.

When manifest.next.json exists, pruning retains the union of the pending manifest
and every currently published manifest. This is required by the two-phase
publication transaction: phase one may publish new provider bundles before the
new manifest is committed, so bundles referenced by the still-live manifest
must remain available until phase two succeeds.

Once manifest.next.json has been consumed, the published manifests become
solely authoritative and old bundles can be pruned normally. Content-addressed
last-known-good artifacts remain protected because they can still be selected by
the publication transaction. ``canonical_source_filename`` in provenance is
historical metadata only: it is not a client/runtime dependency and is therefore
not allowed to keep an otherwise stale JavaScript alias executable/scannable in
``providers/``. Desktop compatibility already falls back to the current published
bundle when that historical source is absent. Plain source files (for example
providers/foo.js) are never removed; only generated bundles ending in
``--<16 hex>.js`` are eligible.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = ROOT / "providers"
HASHED_PROVIDER_RE = re.compile(r"--[0-9a-f]{16}\.js$", re.IGNORECASE)
PROVIDER_PATH_RE = re.compile(r"(?:^|/)(providers/[^?#\"'\\]+\.js)(?:[?#].*)?$", re.IGNORECASE)


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def normalize_provider_path(value: str) -> str | None:
    text = value.strip().replace("\\", "/")
    if not text:
        return None
    parsed = urlparse(text)
    candidate = parsed.path if parsed.scheme or parsed.netloc else text
    match = PROVIDER_PATH_RE.search(candidate)
    if not match:
        return None
    relative = Path(match.group(1)).as_posix().lstrip("/")
    if not relative.startswith("providers/") or ".." in Path(relative).parts:
        return None
    return relative


def choose_manifests(root: Path) -> list[Path]:
    """Return every manifest whose references must survive this transaction.

    A pending manifest is additive here rather than exclusive. Until it is
    promoted, clients can still fetch the currently published manifest and all
    bundles referenced by that manifest therefore remain live dependencies.
    """
    manifests: list[Path] = []
    pending = root / "manifest.next.json"
    if pending.is_file():
        manifests.append(pending)

    main = root / "manifest.json"
    if main.is_file():
        manifests.append(main)
    for path in sorted(root.glob("*/manifest.json")):
        if path != main and path.is_file():
            manifests.append(path)
    return manifests


def referenced_provider_paths(manifests: list[Path]) -> set[str]:
    referenced: set[str] = set()
    for manifest in manifests:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for value in iter_strings(data):
            normalized = normalize_provider_path(value)
            if normalized:
                referenced.add(normalized)
    return referenced


def retain_recorded_provider_path(referenced: set[str], value: object) -> None:
    if not isinstance(value, str):
        return
    normalized = normalize_provider_path(value)
    if normalized:
        referenced.add(normalized)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()

    root = args.root.resolve()
    providers_dir = root / "providers"
    manifests = choose_manifests(root)
    if not manifests:
        raise SystemExit("No manifest.next.json or published manifest.json found; refusing to prune.")

    referenced = referenced_provider_paths(manifests)

    lkg_path = root / "provider-lkg.json"
    if lkg_path.is_file():
        try:
            lkg = json.loads(lkg_path.read_text(encoding="utf-8"))
            for record in (lkg.get("providers", {}) if isinstance(lkg, dict) else {}).values():
                if isinstance(record, dict):
                    retain_recorded_provider_path(referenced, record.get("filename"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid provider-lkg.json; refusing to prune: {exc}")

    provenance_path = root / "PROVENANCE.json"
    if provenance_path.is_file():
        try:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            records = provenance.get("providers", {}) if isinstance(provenance, dict) else {}
            for record in records.values():
                if not isinstance(record, dict):
                    continue
                # published_filename can still be part of the active transaction.
                # canonical_source_filename is deliberately *not* retained: it is
                # historical provenance, not a client-visible executable artifact.
                retain_recorded_provider_path(referenced, record.get("published_filename"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid PROVENANCE.json; refusing to prune: {exc}")

    if not referenced:
        raise SystemExit("No provider JavaScript paths found in authoritative published state; refusing to prune.")

    missing = sorted(path for path in referenced if not (root / path).is_file())
    if missing:
        preview = "\n- ".join(missing[:20])
        raise SystemExit(f"Referenced provider files are missing; refusing to prune:\n- {preview}")

    removed: list[str] = []
    if providers_dir.is_dir():
        for path in sorted(providers_dir.glob("*.js")):
            relative = path.relative_to(root).as_posix()
            if not HASHED_PROVIDER_RE.search(path.name):
                continue
            if relative in referenced:
                continue
            removed.append(relative)
            if not args.dry_run:
                path.unlink()

    mode = "would remove" if args.dry_run else "removed"
    print(
        f"provider prune complete: manifests={','.join(p.relative_to(root).as_posix() for p in manifests)}, "
        f"referenced={len(referenced)}, {mode}={len(removed)}"
    )
    for relative in removed:
        print(f"- {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
