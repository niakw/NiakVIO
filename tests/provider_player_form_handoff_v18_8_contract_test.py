#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
text = BASE.read_text(encoding="utf-8")
marker = "/* NIAKVIO_PROVIDER_PLAYER_FORM_HANDOFF_V18_8 */"
assert text.count(marker) == 1, text.count(marker)
assert "const formRequest = playerText ? _spv188PlayerForm(playerText, responseUrl) : null;" in text
assert '"Content-Type": "application/x-www-form-urlencoded"' in text
assert "const postDecoded = _spv186UnpackPackedPlayer(postText);" in text

section = text.split(marker, 1)[1].split("async function _crawlDirectMedia", 1)[0]
lower = section.casefold()
for forbidden in ("mugiwara", "smoothpre", "ansembed", "jujutsu", "vidhide", "eval("):
    assert forbidden not in lower, forbidden

cases = [
    {
        "html": '<form id="F1" method="POST" action="/go"><input type="hidden" name="op" value="download1"><input type="hidden" name="token" value="abc&amp;def"></form>',
        "page": "https://player.example/v/code123",
        "url": "https://player.example/go",
        "params": {"op": "download1", "token": "abc&def", "file_code": "code123"},
    },
    {
        "html": '<form id="F1" action="https://evil.example/go"><input type="hidden" name="token" value="x"></form>',
        "page": "https://player.example/v/code123",
        "null": True,
    },
    {
        "html": '<form id="OTHER" method="POST" action="/go"><input type="hidden" name="token" value="x"></form>',
        "page": "https://player.example/v/code123",
        "null": True,
    },
    {
        "html": '<form id="F1" method="GET" action="/go"><input type="hidden" name="token" value="x"></form>',
        "page": "https://player.example/v/code123",
        "null": True,
    },
    {
        "html": '<form id="F1" method="POST" action="/go"><input type="hidden" name="bad name" value="ignored"><input type="hidden" name="file_code" value="explicit-code"></form>',
        "page": "https://player.example/v/code123",
        "url": "https://player.example/go",
        "params": {"file_code": "explicit-code"},
    },
]

program = """
function _text(value){return String(value==null?'':value);}
%s
const cases=%s;
for(const row of cases){
  const got=_spv188PlayerForm(row.html,row.page);
  if(row.null){
    if(got!==null){console.error(JSON.stringify({row,got}));process.exit(41);}
    continue;
  }
  if(!got||got.url!==row.url){console.error(JSON.stringify({row,got}));process.exit(42);}
  const params=Object.fromEntries(new URLSearchParams(got.body));
  if(JSON.stringify(params)!==JSON.stringify(row.params)){
    console.error(JSON.stringify({row,got,params}));process.exit(43);
  }
}
""" % (section, json.dumps(cases))

with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
    handle.write(program)
    name = handle.name
try:
    completed = subprocess.run(["node", name], cwd=ROOT, capture_output=True, text=True)
finally:
    Path(name).unlink(missing_ok=True)
assert completed.returncode == 0, completed.stdout + completed.stderr

print("provider player form handoff V18.8 contract tests passed")
