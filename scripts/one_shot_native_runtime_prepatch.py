#!/usr/bin/env python3
from pathlib import Path

# Normalize the compact final gate into the exact structural form consumed by the
# one-shot migration. This changes formatting only; semantics are still the old
# transport-gating semantics until the migration runs immediately afterwards.
p = Path("scripts/analyze_native_corpus_results.cjs")
text = p.read_text(encoding="utf-8")
old = "if (declaredRuntimeErrors.length || declaredContradictions.length || transportFailures.length || readerFailures.length) process.exitCode = 1;"
new = """if (\n  declaredRuntimeErrors.length ||\n  declaredContradictions.length ||\n  transportFailures.length ||\n  readerFailures.length\n) {\n  process.exitCode = 1;\n}"""
count = text.count(old)
if count != 1:
    raise SystemExit(f"compact analyzer gate count={count} expected=1")
p.write_text(text.replace(old, new, 1), encoding="utf-8")

# The collection analyzer was independently refactored to local state/failureStage
# variables. Retarget only the one-shot migration anchor to that current syntax.
migration = Path("scripts/one_shot_native_runtime_migration.py")
source = migration.read_text(encoding="utf-8")
old_block = '''    replace(\n        "scripts/analyze_native_corpus_collection.cjs",\n        "if (row.state === 'ready' && row.failure_stage === 'none') {",\n        "if ((row.state === 'ready' || row.state === 'ended') && row.failure_stage === 'none') {",\n    )\n'''
new_block = '''    replace(\n        "scripts/analyze_native_corpus_collection.cjs",\n        "if (state === 'ready' && (failureStage === 'none' || failureStage === '')) {",\n        "if ((state === 'ready' || state === 'ended') && (failureStage === 'none' || failureStage === '')) {",\n    )\n'''
count = source.count(old_block)
if count != 1:
    raise SystemExit(f"collection migration anchor block count={count} expected=1")
migration.write_text(source.replace(old_block, new_block, 1), encoding="utf-8")
print("compact analyzer and collection migration anchors normalized")
