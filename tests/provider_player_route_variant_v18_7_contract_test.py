#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
text = BASE.read_text(encoding="utf-8")
marker = "/* NIAKVIO_PROVIDER_PLAYER_ROUTE_VARIANT_V18_7 */"
assert text.count(marker) == 1, text.count(marker)
assert "for (const variant of _spv187PlayerRouteVariants(responseUrl))" in text
assert "depth: row.depth, referer: responseUrl" in text

section = text.split(marker, 1)[1].split("async function _crawlDirectMedia", 1)[0]
lower = section.casefold()
for forbidden in ("mugiwara", "smoothpre", "ansembed", "jujutsu", "vidhide"):
    assert forbidden not in lower, forbidden

program = """
function _text(value){return String(value==null?'':value);}
function _crawlCanonical(raw){
  try{const u=new URL(raw);if(!/^https?:$/i.test(u.protocol))return '';u.hash='';return u.toString();}
  catch(_){return '';}
}
%s
const cases=%s;
for(const row of cases){
  const got=_spv187PlayerRouteVariants(row.input);
  if(JSON.stringify(got)!==JSON.stringify(row.expected)){
    console.error(JSON.stringify({row,got}));process.exit(31);
  }
}
""" % (
    section,
    json.dumps([
        {
            "input": "https://player.example/embed/abc123?token=x#fragment",
            "expected": ["https://player.example/v/abc123?token=x"],
        },
        {
            "input": "https://player.example/download/opaque-id",
            "expected": ["https://player.example/v/opaque-id"],
        },
        {
            "input": "https://player.example/e/opaque-id",
            "expected": ["https://player.example/v/opaque-id"],
        },
        {
            "input": "https://player.example/watch/opaque-id",
            "expected": [],
        },
        {"input": "javascript:alert(1)", "expected": []},
    ]),
)

with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
    handle.write(program)
    name = handle.name
try:
    completed = subprocess.run(["node", name], cwd=ROOT, capture_output=True, text=True)
finally:
    Path(name).unlink(missing_ok=True)
assert completed.returncode == 0, completed.stdout + completed.stderr

print("provider player route variant V18.7 contract tests passed")
