#!/usr/bin/env python3
"""Limit oversized GitHub Actions run blocks before GitHub rejects dispatch."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
file=ROOT/".github/workflows/provider-recognition-repair-v6.yml"
lines=file.read_text(encoding="utf-8").splitlines()
sizes=[]
for i, line in enumerate(lines):
    m=re.match(r"^(\s*)run:\s*\|[-+]?\s*$",line)
    if not m:
        continue
    indentation=len(m.group(1))
    body=[]
    for row in lines[i+1:]:
        if row.strip() and len(row)-len(row.lstrip(" "))<=indentation:
            break
        body.append(row[indentation+2:] if row.startswith(" "*(indentation+2)) else row)
    length=len("\n".join(body))
    sizes.append((i+1,length))
    if length>=20500:
        raise AssertionError(f"Action step run at line {i+1} exceeds 20500 safety budget: {length}")
assert sizes and any(line>1500 for line, _ in sizes), "canonical evidence run step not scanned"
source=file.read_text(encoding="utf-8")
assert "bash scripts/persist_repair_race_evidence.sh" in source
assert 'if [ "$force_candidate_applied" = "1" ]; then exit 1; fi' in source
print("Recognition Actions run 21k budget + safe evidence fallback passed",sizes[-3:])
