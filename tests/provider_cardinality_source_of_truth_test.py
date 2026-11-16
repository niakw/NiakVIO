#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
patterns=[
 re.compile(r"\b(?:EXPECTED(?:_[A-Z_]+)?|CURRENT_PROVIDER_COUNT|EXPECTED_CURRENT|EXPECTED_ACTIVE|EXPECTED_PROVIDERS)\s*=\s*(?:44|46|96)\b"),
 re.compile(r"len\((?:providers?|provider_ids|include|rows|current_[A-Za-z0-9_]+)\)\s*(?:==|!=)\s*(?:44|46|96)\b"),
 re.compile(r"(?:exactly|expected|requires?)\s+(?:44|46|96)[ -](?:provider|row)",re.I),
]
bad=[]
scan_paths=[
 *list((ROOT/"scripts").rglob("*.py")),
 *list((ROOT/"tests").rglob("*.py")),
 *list((ROOT/".github"/"workflows").glob("*.yml")),
 *list((ROOT/".github"/"workflows").glob("*.yaml")),
]
for path in scan_paths:
  text=path.read_text(encoding="utf-8")
  for pat in patterns:
   for match in pat.finditer(text):
    # Historical constants may be mentioned in comments/docstrings, but never as executable assignments/comparisons.
    line=text.count("\n",0,match.start())+1
    snippet=match.group(0)
    prefix=text[text.rfind("\n",0,match.start())+1:match.start()].lstrip()
    if prefix.startswith("#") and pat is patterns[2]: continue
    # A literal string that asserts a forbidden historical expression is a
    # regression guard, not executable provider cardinality.
    if prefix.count('"') % 2 == 1 or prefix.count("'") % 2 == 1:
        continue
    bad.append(f"{path.relative_to(ROOT)}:{line}: {snippet}")
assert not bad,"hard-coded current provider cardinality remains:\n"+"\n".join(bad)
assert not (ROOT/".github/workflows/main-route-proof-reconstruction.yml").exists(), (
    "superseded 96-provider route reconstruction workflow must stay retired"
)
print("provider cardinality source-of-truth contract passed scope=scripts+tests+workflows")
