#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for relative in ("README.md", "README.fr.md", "VALIDATION.md"):
    text = (ROOT / relative).read_text(encoding="utf-8")
    assert "NIAKVIO_NATIVE_ADAPTIVE_LAB_DOCS_V1" in text, relative
    assert "96" in text, relative
    assert "Hub-46" in text, relative
    assert "rotating-popular-corpus.json" in text, relative

validation = (ROOT / "VALIDATION.md").read_text(encoding="utf-8")
assert "32 œuvres" in validation
assert "1 movie + 1 TV + 1 anime" in validation
assert "0 streams" in validation
assert "clean miss" in validation
assert "native-hub46/manifest.json" in validation
assert "La liste des fixtures est centralisée dans `.github/triggers/nuvio-client-lab.json`" not in validation

english = (ROOT / "README.md").read_text(encoding="utf-8")
assert "32 works per lane" in english
assert "1 movie + 1 TV episode + 1 anime episode" in english
assert "Historical fixtures" in english

french = (ROOT / "README.fr.md").read_text(encoding="utf-8")
assert "32 œuvres par lane" in french
assert "1 film + 1 épisode TV + 1 épisode anime" in french
assert "fixtures historiques" in french

print("NATIVE_ADAPTIVE_LAB_DOCS_OK catalogue=96 physical_scope=46 reserves=3x32 initial=1+1+1 clean_miss_only=true")
