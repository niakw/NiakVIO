#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_hub46_manifest as hub46  # noqa: E402


def main() -> int:
    source = hub46.load_json(ROOT / "manifest.json")
    matrix = hub46.load_json(ROOT / "automation/evidence/hub-lab-matrix-46.json")
    built = hub46.build(source, matrix)
    rows = built.get("scrapers") or []
    assert len(rows) == 46, len(rows)

    expected = [value.casefold() for value in hub46.matrix_ids(matrix)]
    actual = [str(row.get("id") or "").casefold() for row in rows]
    assert actual == expected, (actual, expected)
    assert len(set(actual)) == 46

    global_ids = {str(row.get("id") or "").casefold() for row in source.get("scrapers") or []}
    assert set(actual) <= global_ids
    for row in rows:
        filename = str(row.get("filename") or "")
        assert filename.startswith("providers/"), (row.get("id"), filename)
        assert not filename.startswith("/")
        assert ".." not in Path(filename).parts

    scope = built.get("labScope") or {}
    assert scope.get("providerCount") == 46
    assert scope.get("authority") == "automation/evidence/hub-lab-matrix-46.json"

    if (ROOT / "manifest-hub46.json").exists():
        hub46.generate(
            ROOT / "manifest.json",
            ROOT / "automation/evidence/hub-lab-matrix-46.json",
            ROOT / "manifest-hub46.json",
            check=True,
        )

    for script in (
        "run_native_corpus_desktop_suite.sh",
        "run_native_corpus_mobile_suite.sh",
        "run_native_corpus_tv_suite.sh",
        "run_native_corpus_ios_suite.sh",
    ):
        text = (ROOT / "scripts" / script).read_text(encoding="utf-8")
        assert "manifest-hub46.json" in text, script

    print("native physical Hub-46 manifest contract tests passed: providers=46 root_relative=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
