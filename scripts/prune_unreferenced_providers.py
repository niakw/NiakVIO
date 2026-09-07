#!/usr/bin/env python3
"""Prune immutable provider bundles with a rolling generation window.

Provider JS filenames are content-addressed client artifacts. Retention is based
on distinct published generations, not on "stale run" counters.

Policy:
- keep the 10 most recent generations per provider by default;
- when an 11th generation appears, remove only the oldest unprotected one;
- each later generation removes at most the next oldest unprotected generation
  needed to return to the configured rolling window;
- current/pending manifests, LKG and published provenance are always protected;
- if an older SHA becomes referenced again after being inactive, it becomes the
  newest occurrence in the rolling order;
- plain non-hashed provider sources are never removed.

The persistent order lives in providers/.generation-retention.json and is
committed atomically with the provider tree.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = ROOT / "providers"
RETENTION_LEDGER = ".generation-retention.json"
SECURITY_REVOCATIONS = "provider-security-revocations.json"
DEFAULT_RETENTION_GENERATIONS = 10
HASHED_PROVIDER_RE = re.compile(
    r"^(?P<provider>.+?)--.+--(?P<digest>[0-9a-f]{16})\.js$",
    re.IGNORECASE,
)
PROVIDER_PATH_RE = re.compile(
    r"(?:^|/)(providers/[^?#\"'\\]+\.js)(?:[?#].*)?$",
    re.IGNORECASE,
)


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


def normalize_generated_path(value: str) -> str | None:
    text = str(value or "").strip().replace("\\", "/").lstrip("/")
    if not text or ".." in Path(text).parts:
        return None
    if text.startswith("providers/") or text.startswith("provider-bases/"):
        if text.endswith(".js"):
            return Path(text).as_posix()
    return None


def load_security_revocations(root: Path) -> set[str]:
    path = root / SECURITY_REVOCATIONS
    if not path.is_file():
        return set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {SECURITY_REVOCATIONS}; refusing to prune: {exc}")
    if not isinstance(raw, dict) or not isinstance(raw.get("entries"), list):
        raise SystemExit(f"Invalid {SECURITY_REVOCATIONS}; refusing to prune.")
    revoked: set[str] = set()
    for row in raw["entries"]:
        if not isinstance(row, dict):
            continue
        normalized = normalize_generated_path(row.get("path"))
        if normalized:
            revoked.add(normalized)
    return revoked


def provider_key(relative: str) -> str | None:
    match = HASHED_PROVIDER_RE.match(Path(relative).name)
    return match.group("provider").casefold() if match else None


def git_first_seen(root: Path, relative: str) -> int | None:
    """Best-effort bootstrap ordering for generations predating the ledger."""
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ct", "--", relative],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    values = [
        int(line.strip())
        for line in result.stdout.splitlines()
        if line.strip().isdigit()
    ]
    return min(values) if values else None


def load_ledger(path: Path) -> dict:
    if not path.is_file():
        return {
            "schema_version": 2,
            "next_sequence": 1,
            "order": {},
            "referenced": {},
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid provider retention ledger; refusing to prune: {exc}")
    if not isinstance(raw, dict):
        raise SystemExit("Invalid provider retention ledger; refusing to prune.")

    if raw.get("schema_version") == 2:
        order = raw.get("order") if isinstance(raw.get("order"), dict) else {}
        referenced = raw.get("referenced") if isinstance(raw.get("referenced"), dict) else {}
        return {
            "schema_version": 2,
            "next_sequence": max(1, int(raw.get("next_sequence") or 1)),
            "order": {
                str(key): [str(value) for value in values if isinstance(value, str)]
                for key, values in order.items()
                if isinstance(values, list)
            },
            "referenced": {
                str(key): bool(value)
                for key, value in referenced.items()
                if isinstance(key, str)
            },
        }

    # Schema v1 used stale-cycle counters. Those counters cannot prove generation
    # order, so migrate conservatively: existing files are bootstrapped from Git
    # history and nothing is deleted merely because a stale counter reached 10.
    return {
        "schema_version": 2,
        "next_sequence": 1,
        "order": {},
        "referenced": {},
    }


def write_ledger(path: Path, ledger: dict, retention_generations: int) -> None:
    payload = {
        "schema_version": 2,
        "policy": "rolling-content-addressed-provider-generations",
        "retention_generations": retention_generations,
        "next_sequence": int(ledger.get("next_sequence") or 1),
        "order": {
            key: values
            for key, values in sorted((ledger.get("order") or {}).items())
            if values
        },
        "referenced": dict(sorted((ledger.get("referenced") or {}).items())),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bootstrap_missing_order(
    root: Path,
    existing_by_provider: dict[str, list[str]],
    order: dict[str, list[str]],
) -> None:
    for key, paths in existing_by_provider.items():
        current = [value for value in order.get(key, []) if value in paths]
        known = set(current)
        missing = [value for value in paths if value not in known]
        if missing:
            ranked = []
            for relative in missing:
                stamp = git_first_seen(root, relative)
                ranked.append((stamp is None, stamp or 0, relative))
            ranked.sort()
            current.extend(relative for _missing_git, _stamp, relative in ranked)
        order[key] = current


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--retention-generations",
        "--retention-cycles",
        dest="retention_generations",
        type=int,
        default=DEFAULT_RETENTION_GENERATIONS,
    )
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.retention_generations < 1:
        raise SystemExit("--retention-generations must be >= 1")

    root = args.root.resolve()
    providers_dir = root / "providers"
    manifests = choose_manifests(root)
    if not manifests:
        raise SystemExit("No manifest.next.json or published manifest.json found; refusing to prune.")

    protected = referenced_provider_paths(manifests)

    lkg_path = root / "provider-lkg.json"
    if lkg_path.is_file():
        try:
            lkg = json.loads(lkg_path.read_text(encoding="utf-8"))
            for record in (lkg.get("providers", {}) if isinstance(lkg, dict) else {}).values():
                if isinstance(record, dict):
                    retain_recorded_provider_path(protected, record.get("filename"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid provider-lkg.json; refusing to prune: {exc}")

    protected_generated = set(protected)
    provenance_path = root / "PROVENANCE.json"
    if provenance_path.is_file():
        try:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            records = provenance.get("providers", {}) if isinstance(provenance, dict) else {}
            for record in records.values():
                if isinstance(record, dict):
                    retain_recorded_provider_path(protected, record.get("published_filename"))
                    retain_recorded_provider_path(protected_generated, record.get("published_filename"))
                    base = normalize_generated_path(record.get("base_filename"))
                    if base:
                        protected_generated.add(base)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid PROVENANCE.json; refusing to prune: {exc}")

    protected_generated.update(protected)
    if not protected:
        raise SystemExit("No provider JavaScript paths found in authoritative published state; refusing to prune.")

    missing_protected = sorted(path for path in protected if not (root / path).is_file())
    if missing_protected:
        preview = "\n- ".join(missing_protected[:20])
        raise SystemExit(f"Referenced provider files are missing; refusing to prune:\n- {preview}")

    providers_dir.mkdir(parents=True, exist_ok=True)

    revoked = load_security_revocations(root)
    revoked_protected = sorted(revoked & protected_generated)
    if revoked_protected:
        preview = "\n- ".join(revoked_protected[:20])
        raise SystemExit(
            "Security-revoked generated artifacts are still authoritative; refusing to prune:\n- " + preview
        )

    security_removed: list[str] = []
    for relative in sorted(revoked):
        target = root / relative
        if target.is_file():
            security_removed.append(relative)
            if not args.dry_run:
                target.unlink()

    ledger_path = providers_dir / RETENTION_LEDGER
    ledger = load_ledger(ledger_path)
    order = ledger.setdefault("order", {})
    previous_referenced = ledger.setdefault("referenced", {})

    existing_by_provider: dict[str, list[str]] = {}
    for path in sorted(providers_dir.glob("*.js")):
        if not path.is_file() or not HASHED_PROVIDER_RE.match(path.name):
            continue
        relative = path.relative_to(root).as_posix()
        key = provider_key(relative)
        if key:
            existing_by_provider.setdefault(key, []).append(relative)

    bootstrap_missing_order(root, existing_by_provider, order)

    # A rollback/re-reference is a new occurrence in the rolling history. A SHA
    # that stays continuously referenced is not moved on every maintenance run.
    for key, paths in existing_by_provider.items():
        values = order.setdefault(key, [])
        for relative in paths:
            is_referenced = relative in protected
            was_referenced = bool(previous_referenced.get(relative, False))
            if is_referenced and not was_referenced and relative in values:
                values.remove(relative)
                values.append(relative)
            previous_referenced[relative] = is_referenced

    removed: list[str] = []
    retained_overflow: list[str] = []
    for key, paths in existing_by_provider.items():
        values = [value for value in order.get(key, []) if value in paths]
        while len(values) > args.retention_generations:
            removable = next((value for value in values if value not in protected), None)
            if removable is None:
                retained_overflow.extend(values[:-args.retention_generations])
                break
            values.remove(removable)
            removed.append(removable)
            previous_referenced.pop(removable, None)
            if not args.dry_run:
                (root / removable).unlink(missing_ok=True)
        order[key] = values

    existing_after = {
        path.relative_to(root).as_posix()
        for path in providers_dir.glob("*.js")
        if path.is_file() and HASHED_PROVIDER_RE.match(path.name)
    }
    for key in list(order):
        order[key] = [value for value in order[key] if value in existing_after or value in removed and args.dry_run]
        if not order[key]:
            order.pop(key, None)
    for relative in list(previous_referenced):
        if relative not in existing_after and not (args.dry_run and relative in removed):
            previous_referenced.pop(relative, None)

    if not args.dry_run:
        write_ledger(ledger_path, ledger, args.retention_generations)

    mode = "would_remove" if args.dry_run else "removed"
    print(
        "provider prune complete: "
        f"manifests={','.join(p.relative_to(root).as_posix() for p in manifests)}, "
        f"protected={len(protected)}, providers={len(existing_by_provider)}, "
        f"retention_generations={args.retention_generations}, "
        f"{mode}={len(removed)}, security_revoked={len(security_removed)}, "
        f"protected_overflow={len(set(retained_overflow))}"
    )
    for relative in security_removed:
        print(f"- SECURITY_REVOKED {relative}")
    for relative in removed:
        print(f"- {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
