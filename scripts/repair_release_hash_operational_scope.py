#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_release_hashes.py"
TEST = ROOT / "tests" / "release_hash_scope_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = SCRIPT.read_text(encoding="utf-8")
    text = replace_once(
        text,
        'IGNORED_FILES = {\n    "availability-history.json",\n    "availability-report.json",\n}\n',
        'IGNORED_FILES = {\n    "availability-history.json",\n    "availability-report.json",\n}\n'
        'IGNORED_PREFIXES = (\n'
        '    ".github/ci-status/",\n'
        '    ".github/triggers/",\n'
        ')\n',
        "operational prefix declaration",
    )
    text = replace_once(
        text,
        '        if relative in IGNORED_FILES:\n            continue\n',
        '        if relative in IGNORED_FILES:\n            continue\n'
        '        if any(relative.startswith(prefix) for prefix in IGNORED_PREFIXES):\n'
        '            continue\n',
        "operational prefix inventory filter",
    )
    text = replace_once(
        text,
        '                "schema_version": 78,\n',
        '                "schema_version": 79,\n',
        "hash schema bump",
    )
    text = replace_once(
        text,
        '                "excluded_mutable_operational_files": sorted(IGNORED_FILES),\n                "files": files,\n',
        '                "excluded_mutable_operational_files": sorted(IGNORED_FILES),\n'
        '                "excluded_mutable_operational_prefixes": sorted(IGNORED_PREFIXES),\n'
        '                "files": files,\n',
        "hash inventory metadata",
    )
    SCRIPT.write_text(text, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    test = replace_once(
        test,
        'assert "availability-report.json" in module.IGNORED_FILES\n',
        'assert "availability-report.json" in module.IGNORED_FILES\n'
        'assert ".github/ci-status/" in module.IGNORED_PREFIXES\n'
        'assert ".github/triggers/" in module.IGNORED_PREFIXES\n',
        "scope assertions",
    )
    test = replace_once(
        test,
        '    (root / "availability-report.json").write_text(\'{"value":1}\\n\', encoding="utf-8")\n    module.ROOT = root\n',
        '    (root / "availability-report.json").write_text(\'{"value":1}\\n\', encoding="utf-8")\n'
        '    (root / ".github/ci-status").mkdir(parents=True)\n'
        '    (root / ".github/triggers").mkdir(parents=True)\n'
        '    (root / ".github/workflows").mkdir(parents=True)\n'
        '    (root / ".github/ci-status/current-runs.json").write_text(\'{"run":1}\\n\', encoding="utf-8")\n'
        '    (root / ".github/triggers/query-current-actions-main").write_text("probe-1\\n", encoding="utf-8")\n'
        '    (root / ".github/workflows/release.yml").write_text("name: durable\\n", encoding="utf-8")\n'
        '    module.ROOT = root\n',
        "operational fixture setup",
    )
    test = replace_once(
        test,
        '    assert "availability-report.json" not in before\n',
        '    assert "availability-report.json" not in before\n'
        '    assert ".github/ci-status/current-runs.json" not in before\n'
        '    assert ".github/triggers/query-current-actions-main" not in before\n'
        '    assert ".github/workflows/release.yml" in before\n',
        "operational inventory assertions",
    )
    test = replace_once(
        test,
        '    (root / "availability-report.json").write_text(\'{"value":2}\\n\', encoding="utf-8")\n    assert module.inventory(include_file_hashes=False) == before\n',
        '    (root / "availability-report.json").write_text(\'{"value":2}\\n\', encoding="utf-8")\n'
        '    (root / ".github/ci-status/current-runs.json").write_text(\'{"run":2}\\n\', encoding="utf-8")\n'
        '    (root / ".github/triggers/query-current-actions-main").write_text("probe-2\\n", encoding="utf-8")\n'
        '    assert module.inventory(include_file_hashes=False) == before\n',
        "operational mutation stability assertion",
    )
    TEST.write_text(test, encoding="utf-8")

    print("release hash operational scope migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
