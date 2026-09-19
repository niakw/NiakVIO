#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
patterns=[
 re.compile(r"\b(?:EXPECTED(?:_[A-Z_]+)?|CURRENT_PROVIDER_COUNT|EXPECTED_CURRENT|EXPECTED_ACTIVE|EXPECTED_PROVIDERS)\s*=\s*(?:44|46|96)\b"),
 re.compile(r"len\([^\n]+?\)\s*(?:==|!=)\s*(?:44|46|96)\b"),
 re.compile(r"(?:exactly|expected|requires?)\s+(?:44|46|96)[ -](?:provider|row)",re.I),
]
bad=[]
for root in (ROOT/"scripts",ROOT/"tests"):
 for path in root.rglob("*.py"):
  text=path.read_text(encoding="utf-8")
  for pat in patterns:
   for match in pat.finditer(text):
    # Historical constants may be mentioned in comments/docstrings, but never as executable assignments/comparisons.
    line=text.count("\n",0,match.start())+1
    snippet=match.group(0)
    prefix=text[text.rfind("\n",0,match.start())+1:match.start()].lstrip()
    if prefix.startswith("#") and pat is patterns[2]: continue
    bad.append(f"{path.relative_to(ROOT)}:{line}: {snippet}")
assert not bad,"hard-coded current provider cardinality remains:\n"+"\n".join(bad)
print("provider cardinality source-of-truth contract passed scope=all-python-scripts-tests")
