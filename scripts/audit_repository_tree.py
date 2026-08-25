#!/usr/bin/env python3
"""Inventory every tracked NiakVIO path and fail only on structural corruption.

The scanner is deliberately conservative: temp-looking files, large files, duplicate
content and report snapshots are review candidates, not automatic deletion targets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {
    ".c", ".cc", ".cfg", ".conf", ".cpp", ".css", ".csv", ".env", ".gradle",
    ".h", ".hpp", ".html", ".ini", ".java", ".js", ".json", ".kts", ".kt",
    ".liquid", ".lock", ".md", ".mjs", ".py", ".properties", ".rst", ".sh",
    ".svg", ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
}
TEXT_FILENAMES = {".editorconfig", ".gitattributes", ".gitignore", "CODEOWNERS", "Dockerfile", "LICENSE", "Makefile"}
TEMP_PATTERNS = (
    re.compile(r"(^|/)(?:tmp|temp)[-_]", re.I),
    re.compile(r"(?:\.bak|\.backup|\.old|\.orig|\.rej|\.swp|~)$", re.I),
    re.compile(r"(^|/)(?:debug|scratch|wip)[-_]", re.I),
)
REPORT_HINTS = re.compile(r"(?:report|diagnostic|findings|failure|snapshot|current-runs|audit|baseline|evidence)", re.I)
CONFLICT_BLOCK = re.compile(r"^<<<<<<< .+?\n.*?^=======\s*$\n.*?^>>>>>>> .+?$", re.MULTILINE | re.DOTALL)
LARGE_BYTES = 1 * 1024 * 1024
VERY_LARGE_BYTES = 5 * 1024 * 1024


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def tracked_entries() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for record in git("ls-files", "-s", "-z").split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        rows.append((path.decode("utf-8", errors="surrogateescape"), meta.split(b" ", 1)[0].decode("ascii")))
    return rows


def looks_text(path: Path, data: bytes) -> bool:
    if path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if b"\0" in data[:8192]:
        return False
    try:
        data[:65536].decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def has_conflict_block(text: str) -> bool:
    """Require a complete Git conflict triplet; decorative ======== is harmless."""
    return bool(CONFLICT_BLOCK.search(text))


def audit() -> dict[str, Any]:
    entries = tracked_entries()
    findings: dict[str, list[Any]] = defaultdict(list)
    hashes: dict[str, list[str]] = defaultdict(list)
    lower_paths: dict[str, list[str]] = defaultdict(list)
    extension_counts: dict[str, int] = defaultdict(int)
    sizes: list[dict[str, Any]] = []
    total_bytes = 0

    for path_str, mode in entries:
        path = ROOT / path_str
        lower_paths[path_str.casefold()].append(path_str)
        extension_counts[path.suffix.lower() or "<none>"] += 1

        if mode == "120000":
            target = os.readlink(path)
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
                inside = True
            except ValueError:
                inside = False
            if inside and not resolved.exists():
                findings["broken_symlinks"].append({"path": path_str, "target": target})
            continue

        if not path.is_file():
            findings["missing_tracked_paths"].append(path_str)
            continue

        data = path.read_bytes()
        size = len(data)
        total_bytes += size
        sizes.append({"path": path_str, "bytes": size})
        hashes[hashlib.sha256(data).hexdigest()].append(path_str)

        if size == 0:
            findings["zero_byte_files"].append(path_str)
        if size >= VERY_LARGE_BYTES:
            findings["very_large_files"].append({"path": path_str, "bytes": size})
        elif size >= LARGE_BYTES:
            findings["large_files"].append({"path": path_str, "bytes": size})
        if any(pattern.search(path_str) for pattern in TEMP_PATTERNS):
            findings["temporary_or_backup_candidates"].append(path_str)
        if REPORT_HINTS.search(path_str):
            findings["report_snapshot_candidates"].append(path_str)

        if not looks_text(path, data):
            continue
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            findings["non_utf8_text_candidates"].append(path_str)
            continue

        if data and not data.strip():
            findings["whitespace_only_files"].append(path_str)
        if data.startswith(b"\xef\xbb\xbf"):
            findings["utf8_bom_files"].append(path_str)
        if b"\r\n" in data:
            findings["crlf_text_files"].append(path_str)
        if data and not data.endswith(b"\n"):
            findings["missing_final_newline"].append(path_str)
        if has_conflict_block(text):
            findings["merge_conflict_marker_candidates"].append(path_str)
        trailing = sum(1 for line in text.splitlines() if line.endswith((" ", "\t")))
        if trailing:
            findings["trailing_whitespace"].append({"path": path_str, "lines": trailing})
        if path.suffix.lower() == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                findings["invalid_json"].append({"path": path_str, "line": exc.lineno, "column": exc.colno, "message": exc.msg})

    for paths in lower_paths.values():
        if len(paths) > 1:
            findings["case_insensitive_path_collisions"].append(sorted(paths))
    for sha, paths in hashes.items():
        if len(paths) > 1:
            findings["exact_duplicate_files"].append({"sha256": sha, "paths": sorted(paths)})

    sizes.sort(key=lambda row: (-row["bytes"], row["path"]))
    for key, rows in findings.items():
        rows.sort(key=lambda row: json.dumps(row, sort_keys=True) if isinstance(row, (dict, list)) else str(row))

    hard_keys = (
        "missing_tracked_paths",
        "broken_symlinks",
        "invalid_json",
        "merge_conflict_marker_candidates",
        "case_insensitive_path_collisions",
    )
    hard_failures = {key: findings.get(key, []) for key in hard_keys if findings.get(key)}
    return {
        "schemaVersion": 2,
        "trackedFiles": len(entries),
        "trackedBytes": total_bytes,
        "extensionCounts": dict(sorted(extension_counts.items())),
        "largestFiles": sizes[:50],
        "findings": dict(sorted(findings.items())),
        "hardFailures": hard_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-hard", action="store_true")
    args = parser.parse_args()
    report = audit()
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    summary = {key: len(rows) for key, rows in report["findings"].items() if rows}
    print(
        f"FIELD_REPOSITORY_TREE_AUDIT tracked={report['trackedFiles']} bytes={report['trackedBytes']} "
        f"findings={json.dumps(summary, sort_keys=True)}",
        file=sys.stderr,
    )
    if args.fail_hard and report["hardFailures"]:
        print(json.dumps(report["hardFailures"], ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
