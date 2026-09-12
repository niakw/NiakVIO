#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
text = BASE.read_text(encoding="utf-8")

for needle in (
    "NIAKVIO_PROVIDER_MOVIE_CATALOGUE_IDENTITY_V21_10",
    "function _spv211MovieCatalogueEquivalent(actual, expected, meta)",
    "if (!exact && !_spv211MovieCatalogueEquivalent(actual, expected, meta)) return -10000;",
):
    assert needle in text, needle

start = text.index("function _spv211MovieCatalogueEquivalent")
end = text.index("function _spv211CandidateIdentityScore", start)
helper = text[start:end]

runner = r'''
function _text(value){return String(value==null?"":value)}
HELPER
function check(value,msg){if(!value)throw new Error(msg)}
const expected=["interstellar","interestelar"];
check(_spv211MovieCatalogueEquivalent("interstellar",expected,{year:"2014"})===true,"exact title rejected");
check(_spv211MovieCatalogueEquivalent("interstellar-2014",expected,{year:"2014"})===true,"year presentation suffix rejected");
check(_spv211MovieCatalogueEquivalent("interstellar-1080p-vf",expected,{year:"2014"})===true,"quality/language presentation suffix rejected");
check(_spv211MovieCatalogueEquivalent("interestelar",expected,{year:"2014"})===true,"alias rejected");
check(_spv211MovieCatalogueEquivalent("the-science-of-interstellar",expected,{year:"2014"})===false,"documentary prefix collision accepted");
check(_spv211MovieCatalogueEquivalent("interstellar-documentary",expected,{year:"2014"})===false,"semantic suffix collision accepted");
check(_spv211MovieCatalogueEquivalent("interstellar-2015",expected,{year:"2014"})===false,"wrong year noise accepted");
console.log("MOVIE_CATALOGUE_IDENTITY_V21_10_OK");
'''.replace("HELPER", helper)

with tempfile.TemporaryDirectory() as tmp:
    js = Path(tmp) / "movie-identity.js"
    js.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(js)], check=True, timeout=5)

print("provider movie catalogue identity v21.10 contract passed")
