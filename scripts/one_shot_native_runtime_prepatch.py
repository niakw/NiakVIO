#!/usr/bin/env python3
from pathlib import Path

p = Path("scripts/analyze_native_corpus_results.cjs")
text = p.read_text(encoding="utf-8")
old = "if (declaredRuntimeErrors.length || declaredContradictions.length || transportFailures.length || readerFailures.length) process.exitCode = 1;"
new = """if (\n  declaredRuntimeErrors.length ||\n  declaredContradictions.length ||\n  transportFailures.length ||\n  readerFailures.length\n) {\n  process.exitCode = 1;\n}"""
count = text.count(old)
if count != 1:
    raise SystemExit(f"compact analyzer gate count={count} expected=1")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("compact analyzer gate normalized")
