#!/usr/bin/env python3
"""Replace per-file git --follow retention bootstrap with one bounded history scan."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/prune_unreferenced_providers.py"
MARKER = "NIAKVIO_PROVIDER_PRUNE_BATCH_HISTORY_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    old_first = '''def git_first_seen(root: Path, relative: str) -> int | None:
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
'''
    new_first = '''# NIAKVIO_PROVIDER_PRUNE_BATCH_HISTORY_V1
def git_first_seen_batch(root: Path, relatives: set[str]) -> dict[str, int]:
    """Best-effort first-add timestamps for all missing generations in one Git scan.

    Content-addressed generation files are immutable and are not renamed, so
    `--follow` is both unnecessary and prohibitively expensive here.
    """
    wanted = {Path(value).as_posix() for value in relatives if value}
    if not wanted:
        return {}
    marker = "__NIAKVIO_COMMIT_TS__"
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", f"--format={marker}%ct", "--name-only", "--", "providers"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if result.returncode != 0:
        return {}
    current_stamp: int | None = None
    found: dict[str, int] = {}
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(marker):
            value = line[len(marker):]
            current_stamp = int(value) if value.isdigit() else None
            continue
        relative = Path(line).as_posix()
        if current_stamp is None or relative not in wanted:
            continue
        previous = found.get(relative)
        if previous is None or current_stamp < previous:
            found[relative] = current_stamp
    return found
'''
    text = once(text, old_first, new_first, "replace-per-file-history")
    old_boot = '''def bootstrap_missing_order(
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
'''
    new_boot = '''def bootstrap_missing_order(
    root: Path,
    existing_by_provider: dict[str, list[str]],
    order: dict[str, list[str]],
) -> None:
    missing_by_provider: dict[str, list[str]] = {}
    all_missing: set[str] = set()
    for key, paths in existing_by_provider.items():
        current = [value for value in order.get(key, []) if value in paths]
        known = set(current)
        missing = [value for value in paths if value not in known]
        missing_by_provider[key] = missing
        all_missing.update(missing)
    first_seen = git_first_seen_batch(root, all_missing)
    for key, paths in existing_by_provider.items():
        current = [value for value in order.get(key, []) if value in paths]
        missing = missing_by_provider.get(key, [])
        if missing:
            ranked = [
                (first_seen.get(relative) is None, first_seen.get(relative) or 0, relative)
                for relative in missing
            ]
            ranked.sort()
            current.extend(relative for _missing_git, _stamp, relative in ranked)
        order[key] = current
'''
    text = once(text, old_boot, new_boot, "batch-bootstrap-order")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (MARKER, "def git_first_seen_batch", "--name-only", "all_missing", "first_seen = git_first_seen_batch"):
        if needle not in value:
            raise AssertionError(f"prune batch history missing {needle}")
    if '"--follow"' in value or "git_first_seen(root, relative)" in value:
        raise AssertionError("per-file --follow retention history still present")


def main() -> int:
    changed = patch()
    print(f"PROVIDER_PRUNE_BATCH_HISTORY_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
