#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"reapply_published_overrides.py"
spec=importlib.util.spec_from_file_location("reapply_published_overrides_diag",SCRIPT)
module=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

raw="tmp.js:1\n"+"x"*70000+"\n"+" "^31+"^\nSyntaxError: Unexpected token ';'\nNode.js v24\n"
out=module._compact_validation_detail(raw,max_line=1600)
assert "tmp.js:1" in out
assert "<provider source omitted chars=70000>" in out
assert "^" in out
assert "SyntaxError: Unexpected token ';'" in out
assert "Node.js v24" in out
assert "x"*2000 not in out
print("provider validation diagnostic compaction passed")
