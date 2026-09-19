#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_shared_player_trace_v21.py"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"

spec = importlib.util.spec_from_file_location("v21", SCRIPT)
if spec is None or spec.loader is None:
    raise SystemExit("unable to load V21 migration")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.patch_worker()
module.patch_proof()
module.patch_recovery()
module.patch_materializer()
module.patch_base()
module.validate_worker()
module.validate_proof()
module.validate_recovery()
module.validate_materializer()
module.validate_base()

base = module.BASE.read_text(encoding="utf-8")
probe = PROBE.read_text(encoding="utf-8")
assert module.MARKER in base
assert module.TRACE_MARKER in base
assert module.PLAYER_MARKER in base
assert "globalThis.__nuvioProviderValueTraceHistoryV21" in base
assert "while (history.length > 48) history.shift();" in base
assert "provider_value_trace_history_v21" in probe
assert "index <= 7" in probe

# Execute the actual generated helper against a synthetic response that follows
# the content-shape algorithm. No provider hostname/name is encoded in the test.
start = base.index("function _spv21DecodedObfuscatedHls")
end = base.index("async function _crawlDirectMedia", start)
helper = base[start:end]

host = "player.example.test"
page = f"https://{host}/embed/abc"
real_url = "https://cdn.example.test/path/master.m3u8?fixture=1"
host_hash = sum(ord(ch) for ch in host) & 255
reversed_plain = "".join(
    chr(ord(ch) ^ ((0x3D + index * 89 + host_hash) & 255))
    for index, ch in enumerate(real_url)
)
binary = reversed_plain[::-1].encode("latin1")
encoded = base64.b64encode(binary).decode("ascii")
html = f'<script>(function(s){{var a=atob(s).split("").reverse().join("");return a}})("{encoded}")</script>'

node = f"""
function _text(v) {{ return v == null ? '' : String(v); }}
{helper}
const decoded = _spv21DecodedObfuscatedHls({json.dumps(html)}, {json.dumps(page)});
if (decoded !== {json.dumps(real_url)}) {{
  console.error(JSON.stringify({{decoded}}));
  process.exit(2);
}}
const troll = {json.dumps('https://cdn.example.test/troll/master.m3u8')};
const host = {json.dumps(host)};
let H=0; for (const c of host) H=(H+c.charCodeAt(0))&255;
let x=''; for (let i=0;i<troll.length;i++) x += String.fromCharCode(troll.charCodeAt(i)^((0x3d+i*89+H)&255));
const enc = Buffer.from(x.split('').reverse().join(''), 'latin1').toString('base64');
const trollHtml = `<script>(function(s){{return atob(s).split('').reverse().join('')}})("${{enc}}")</script>`;
if (_spv21DecodedObfuscatedHls(trollHtml, {json.dumps(page)}) !== '') process.exit(3);
console.log('V21_HELPER_OK');
"""
proc = subprocess.run(["node", "-e", node], cwd=ROOT, text=True, capture_output=True, check=False)
assert proc.returncode == 0, proc.stdout + proc.stderr
assert "V21_HELPER_OK" in proc.stdout

migration_lower = SCRIPT.read_text(encoding="utf-8").casefold()
# Names can appear only in the validator's explicit forbidden-token list, never
# in the runtime helper body inserted into ProviderBase.
runtime_literal = SCRIPT.read_text(encoding="utf-8").split("helper = r'''", 1)[1].split("'''", 1)[0].casefold()
for forbidden in ("animesama", "animevostfr", "french-manga", "purstream", "jujutsu"):
    assert forbidden not in runtime_literal, forbidden
for secret in ("authorization", "set-cookie", "requestheaders", "responsebody"):
    assert secret not in runtime_literal, secret

print("provider shared player/trace V21 tests passed")
