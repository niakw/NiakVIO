#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
text = BASE.read_text(encoding="utf-8")
marker = "/* NIAKVIO_PROVIDER_PACKED_PLAYER_V18_6 */"
assert text.count(marker) == 1, text.count(marker)
assert "const decodedPlayerText = _spv186UnpackPackedPlayer(playerText);" in text
assert "urls = _extractUrls(decodedPlayerText, responseUrl);" in text

section = text.split(marker, 1)[1].split("async function _crawlDirectMedia", 1)[0]
lower = section.casefold()
for forbidden in ("mugiwara", "smoothpre", "ansembed", "jujutsu"):
    assert forbidden not in lower, forbidden

# A minimal Dean-Edwards-shaped fixture proves the decoder is structural. The
# function body is deliberately inert: V18.6 parses only the argument payload and
# dictionary and never executes eval or any upstream JavaScript.
packed = (
    "eval(function(p,a,c,k,e,d){return p}"
    "('0:\\"1\\"',2,2,'file|https://cdn.example/video.m3u8'.split('|'),0,{}))"
)
program = """
function _text(value){return String(value==null?'':value);}
%s
const packed=%r;
const decoded=_spv186UnpackPackedPlayer(packed);
if(!decoded.includes('file:\"https://cdn.example/video.m3u8\"')){
  console.error(decoded);process.exit(21);
}
if(_spv186UnpackPackedPlayer('plain')!=='plain')process.exit(22);
""" % (section, packed)

with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
    handle.write(program)
    name = handle.name
try:
    completed = subprocess.run(["node", name], cwd=ROOT, capture_output=True, text=True)
finally:
    Path(name).unlink(missing_ok=True)
assert completed.returncode == 0, completed.stdout + completed.stderr

print("provider packed player V18.6 contract tests passed")
