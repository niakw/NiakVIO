#!/usr/bin/env python3
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "local" / "test_targeted_vf_repair.py").read_text(encoding="utf-8")
tree = ast.parse(source)
ids = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "IDS":
                ids = ast.literal_eval(node.value)
expected = ["coflix", "dulourd", "french-manga", "frenchstream", "movix", "sekai", "streamzo"]
assert ids == expected, (ids, expected)
assert "publication_performed" in source and "False" in source
print("targeted VF repair configuration tests passed")
