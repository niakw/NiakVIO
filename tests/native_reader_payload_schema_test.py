#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

brain = (ROOT / "engine_v2/scripts/diagnose-native-reader.mjs").read_text(encoding="utf-8")
normalizer = (ROOT / "scripts/normalize_core_runtime_compat.py").read_text(encoding="utf-8")

count_line = "  systemicExtractionGroupCount: systemicExtraction.systemicGroups.length,"
groups_line = "  systemicExtractionGroups: systemicExtraction.systemicGroups,"
old_collision = "  systemicExtractionGroups: systemicExtraction.systemicGroups.length,"

assert brain.count(count_line) == 1
assert brain.count(groups_line) == 1
assert old_collision not in brain

assert count_line in normalizer
assert groups_line in normalizer
assert old_collision not in normalizer

print("native reader payload schema test passed: systemic extraction count and groups are distinct")
