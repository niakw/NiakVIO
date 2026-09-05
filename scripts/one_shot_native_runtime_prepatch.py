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

# Global catalogue recovery is a positive-output identity guard. A provider that
# returned zero streams must remain zero; only explicitly authoritative provider
# adapters may execute catalogue recovery themselves.
patch = Path("scripts/provider_patches/global_catalogue_alias_recovery_v2.py")
patch_text = patch.read_text(encoding="utf-8")
old_revision = '"implementationRevision": "authoritative-recovery-v12-html-scanner",'
new_revision = '"implementationRevision": "authoritative-recovery-v13-positive-output-only",'
if patch_text.count(old_revision) != 1:
    raise SystemExit(f"alias recovery revision anchor count={patch_text.count(old_revision)} expected=1")
patch_text = patch_text.replace(old_revision, new_revision, 1)
old_empty_recovery = 'if(!m||!m.titles||!m.titles.length)return v;var recovered=[];try{recovered=await recover(q,m,workDeadline())}catch(_){recovered=[]}return recovered&&recovered.length?recovered:v'
if patch_text.count(old_empty_recovery) != 1:
    raise SystemExit(f"alias zero-output recovery anchor count={patch_text.count(old_empty_recovery)} expected=1")
patch_text = patch_text.replace(old_empty_recovery, 'return v', 1)
patch.write_text(patch_text, encoding="utf-8")

alias_test = Path("tests/global_catalogue_alias_recovery_test.py")
alias_test_text = alias_test.read_text(encoding="utf-8")
old_test_revision = '"implementationRevision":"authoritative-recovery-v12-html-scanner"'
new_test_revision = '"implementationRevision":"authoritative-recovery-v13-positive-output-only"'
if alias_test_text.count(old_test_revision) != 1:
    raise SystemExit(f"alias test revision anchor count={alias_test_text.count(old_test_revision)} expected=1")
alias_test.write_text(alias_test_text.replace(old_test_revision, new_test_revision, 1), encoding="utf-8")

print("runtime anchors normalized; alias recovery forced positive-output-only")
