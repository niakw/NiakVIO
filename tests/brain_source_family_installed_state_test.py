#!/usr/bin/env python3
from __future__ import annotations
import shutil
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/"scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0,str(SCRIPTS))
from brain_source_family_state import source_family_artifact_paths, source_family_parser_installed

paths=source_family_artifact_paths()
assert len(paths)==3 and source_family_parser_installed(ROOT)
with tempfile.TemporaryDirectory(prefix="brain-source-installed-") as td:
    root=Path(td)
    for rel in paths:
        dst=root/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/rel,dst)
    assert source_family_parser_installed(root)
    (root/paths[2]).unlink()
    assert not source_family_parser_installed(root)
    shutil.copy2(ROOT/paths[2],root/paths[2])
    module=root/paths[0]
    src=module.read_text("utf-8")
    module.write_text(src.replace("AXIS = 'reader-slots'","AXIS = 'episode-slots'"),"utf-8")
    assert not source_family_parser_installed(root)
print("Brain source-family installed state: exact 3-artifact parser replay passes; missing/drifted capability fails closed")
