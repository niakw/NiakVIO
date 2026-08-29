#!/usr/bin/env python3
"""Age out stale content-hashed provider bundles without breaking old clients.

Provider JS filenames are immutable/content-addressed and older Nuvio clients may
keep an older manifest for several publication cycles. Therefore an unreferenced
bundle is never deleted immediately.

Retention model:
- every bundle referenced by a current/pending manifest, LKG or published
  provenance is protected indefinitely and its stale counter is reset;
- every other hashed bundle accumulates one stale publication cycle;
- deletion is allowed only after the configured number of consecutive stale
  publication cycles (10 by default);
- plain source files are never removed.

The cycle ledger lives inside providers/.generation-retention.json so the same
atomic git add -A providers transaction persists both bundles and retention state.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = ROOT / "providers"
RETENTION_LEDGER = ".generation-retention.json"
DEFAULT_RETENTION_CYCLES = 10
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


def load_ledger(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid provider retention ledger; refusing to prune: {exc}")
    rows = raw.get("stale_cycles") if isinstance(raw, dict) else {}
    if not isinstance(rows, dict):
        return {}
    out: dict[str, int] = {}
    for key, value in rows.items():
        if isinstance(key, str) and isinstance(value, int) and value >= 0:
            out[key] = value
    return out


def write_ledger(path: Path, ledger: dict[str, int], retention_cycles: int) -> None:
    payload = {
        "schema_version": 1,
        "policy": "content-addressed-provider-generation-grace",
        "retention_cycles": retention_cycles,
        "stale_cycles": dict(sorted(ledger.items())),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retention-cycles", type=int, default=DEFAULT_RETENTION_CYCLES)
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.retention_cycles < 1:
        raise SystemExit("--retention-cycles must be >= 1")

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
                if isinstance(record, dict):
                    retain_recorded_provider_path(referenced, record.get("published_filename"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid PROVENANCE.json; refusing to prune: {exc}")

    if not referenced:
        raise SystemExit("No provider JavaScript paths found in authoritative published state; refusing to prune.")

    missing = sorted(path for path in referenced if not (root / path).is_file())
    if missing:
        preview = "\n- ".join(missing[:20])
        raise SystemExit(f"Referenced provider files are missing; refusing to prune:\n- {preview}")

    ledger_path = providers_dir / RETENTION_LEDGER
    previous = load_ledger(ledger_path)
    ledger: dict[str, int] = {}
    removed: list[str] = []
    retained_by_grace: list[str] = []

    if providers_dir.is_dir():
        for path in sorted(providers_dir.glob("*.js")):
            relative = path.relative_to(root).as_posix()
            if not HASHED_PROVIDER_RE.search(path.name):
                continue
            if relative in referenced:
                ledger[relative] = 0
                continue
            stale_cycles = previous.get(relative, 0) + 1
            if stale_cycles >= args.retention_cycles:
                removed.append(relative)
                if not args.dry_run:
                    path.unlink()
                continue
            ledger[relative] = stale_cycles
            retained_by_grace.append(relative)

    existing = {
        path.relative_to(root).as_posix()
        for path in providers_dir.glob("*.js")
        if path.is_file() and HASHED_PROVIDER_RE.search(path.name)
    }
    ledger = {key: value for key, value in ledger.items() if key in existing}

    if not args.dry_run:
        write_ledger(ledger_path, ledger, args.retention_cycles)

    mode = "would remove" if args.dry_run else "removed"
    print(
        "provider prune complete: "
        f"manifests={','.join(p.relative_to(root).as_posix() for p in manifests)}, "
        f"referenced={len(referenced)}, grace={len(retained_by_grace)}, "
        f"retention_cycles={args.retention_cycles}, {mode}={len(removed)}"
    )
    for relative in removed:
        print(f"- {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
