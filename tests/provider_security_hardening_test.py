#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_security_hardening import MARKER, harden_text, known_unsafe_findings
from harden_staged_provider_security import harden_stage


def js_ok(text: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(text)
        name = handle.name
    completed = subprocess.run(["node", "--check", name], capture_output=True, text=True)
    Path(name).unlink(missing_ok=True)
    assert completed.returncode == 0, completed.stderr


cinema = '''"use strict";\nfunction x(rawFile){\n const unescaped = rawFile.replace(/\\\\(.)/g, "$1");\n return JSON.parse(unescaped);\n}\n'''
hardened, report = harden_text(cinema)
assert report["structuredParseChanges"] == 1, report
assert '.replace(/\\\\(.)/g, "$1")' not in hardened
assert "JSON.parse(unescaped)" in hardened
js_ok(hardened)

anizone = r'''const jsonStr = jsonMatch[1].replace(/\\\\/g, "\\").replace(/\\u([0-9a-fA-F]{4})/g, (m, grp) => String.fromCharCode(parseInt(grp, 16))).replace(/\\'/g, "'");
const parsed = JSON.parse(jsonStr);'''
hardened, report = harden_text(anizone)
assert report["structuredParseChanges"] == 1, report
assert '.replace(/\\\\/g, "\\")' not in hardened
assert "String.fromCharCode(parseInt(grp, 16))" in hardened
js_ok(hardened)

unsafe = r'''function s(v){return String(v)}
function unescapeJs(v){try{return JSON.parse('"'+s(v).replace(/"/g,'\\"')+'"')}catch(_){return v}}
var packed=unescapeJs(input);'''
hardened, report = harden_text(unsafe)
assert report["literalDecodeChanges"] == 1, (report, hardened)
assert "__nuvioDecodeEscapedLiteral(s(v))" in hardened
assert "JSON.parse('\\\"'+" not in hardened
js_ok(hardened)

hosts = '''function bad(e){let t=e.toLowerCase();return t.includes("test-videos.co.uk")||t.includes("big_buck_bunny")||t.includes("sample-videos.com")||t.includes("example.com");}'''
hardened, report = harden_text(hosts)
assert report["hostnameChanges"] == 3, report
assert '__nuvioHostMatches(t,"test-videos.co.uk")' in hardened
assert '__nuvioHostMatches(t,"sample-videos.com")' in hardened
assert '__nuvioHostMatches(t,"example.com")' in hardened
assert 't.includes("big_buck_bunny")' in hardened
js_ok(hardened)

# JavaScript-obfuscator output used by multiple imported providers accumulates a
# complete UTF-8 %HH byte stream and then routes it through decodeURIComponent.
# That generic URI-decoding boundary is the source of CodeQL's incomplete-string-
# encoding alerts. The Core rewrites only this structural byte-decoder shape and
# leaves normal URL decodeURIComponent calls alone.
percent_decoder = r'''function decodeTable(value){
  var raw="abc", encoded="";
  for(var i=0;i<raw.length;i++){encoded+="%"+("00"+raw.charCodeAt(i).toString(16)).slice(-2)}
  return decodeURIComponent(encoded);
}
function legitimate(url){return decodeURIComponent(url)}
'''
hardened, report = harden_text(percent_decoder)
assert report["percentDecodeChanges"] == 1, (report, hardened)
assert "return __nuvioDecodeUtf8PercentBytes(encoded)" in hardened
assert "function __nuvioDecodeUtf8PercentBytes(" in hardened
assert "return decodeURIComponent(url)" in hardened
assert "incomplete_percent_byte_decode" not in known_unsafe_findings(hardened)
js_ok(hardened)

# Prove strict UTF-8 compatibility for the replacement, including a 4-byte code
# point and URIError on malformed input, without depending on TextDecoder support.
percent_runtime = hardened + r'''
if(__nuvioDecodeUtf8PercentBytes("%63%61%66%C3%A9")!=="café")process.exit(21);
if(__nuvioDecodeUtf8PercentBytes("%F0%9F%8D%91")!=="🍑")process.exit(22);
var threw=false;try{__nuvioDecodeUtf8PercentBytes("%C3%28")}catch(e){threw=e instanceof URIError}
if(!threw)process.exit(23);
'''
with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
    handle.write(percent_runtime)
    percent_name = handle.name
completed = subprocess.run(["node", percent_name], capture_output=True, text=True)
Path(percent_name).unlink(missing_ok=True)
assert completed.returncode == 0, completed.stdout + completed.stderr

# MalluMV-style HTML entity decoding used to decode &amp; before &lt;/&gt;/etc.
# That means &amp;lt; becomes a literal '<' in one chain: a genuine double-unescape.
# The generic Core keeps the same fixed entity map but decodes ampersand last.
html_entities = r'''function decodeOne(raw){return raw
  .replace(/&raquo;/g, '»')
  .replace(/&amp;/g, '&')
  .replace(/&lt;/g, '<')
  .replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'");}
'''
hardened, report = harden_text(html_entities)
assert report["htmlEntityDecodeReorders"] == 1, (report, hardened)
assert hardened.index("/&lt;/g") < hardened.index("/&amp;/g"), hardened
assert hardened.index("/&#39;/g") < hardened.index("/&amp;/g"), hardened
assert "double_html_entity_unescape" not in known_unsafe_findings(hardened)
js_ok(hardened)
html_runtime = hardened + r'''
if(decodeOne("&lt;b&gt;")!=="<b>")process.exit(31);
if(decodeOne("Tom &amp; Jerry")!=="Tom & Jerry")process.exit(32);
if(decodeOne("&amp;lt;b&amp;gt;")!=="&lt;b&gt;")process.exit(33);
'''
with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
    handle.write(html_runtime)
    html_name = handle.name
completed = subprocess.run(["node", html_name], capture_output=True, text=True)
Path(html_name).unlink(missing_ok=True)
assert completed.returncode == 0, completed.stdout + completed.stderr

# Imported providers must not retain CodeQL-recognized console sinks at all. A
# local no-op sink is stronger than merely shadowing console because tainted values
# no longer flow into console.log/error/warn calls in the generated source graph.
logs = '''var TMDB_API_KEY="secret";function f(u){console.log(u+TMDB_API_KEY);console["warn"](TMDB_API_KEY);globalThis.console.error(u)}'''
hardened, report = harden_text(logs)
assert report["consoleSinkChanges"] == 3, (report, hardened)
assert "console.log" not in hardened
assert 'console["warn"]' not in hardened
assert "globalThis.console.error" not in hardened
assert hardened.count("__nuvioProviderSilentLog") >= 4
assert "var __nuvioProviderSilentLog=function(){};" in hardened
assert MARKER in hardened
assert "provider_console_sensitive_sink" not in known_unsafe_findings(hardened)
js_ok(hardened)

again, again_report = harden_text(hardened)
assert again == hardened
assert again_report["alreadyHardened"] is True
assert known_unsafe_findings(hardened) == [], known_unsafe_findings(hardened)

# A formatter/minifier may relocate a preserved marker while a later Core-tail
# rebuild removes only the silent helper declaration. Marker presence must not
# suppress structural repair of remaining helper uses.
orphan_shadow = '''/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:deadbeef */
/* NUVIO_PROVIDER_CONSOLE_SHADOW_V1 */
var console={log:__nuvioProviderSilentLog,warn:__nuvioProviderSilentLog,error:__nuvioProviderSilentLog};
function getStreams(){console.log("x");return []}
globalThis.getStreams=getStreams;'''
assert "provider_console_shadow_orphan_helper" in known_unsafe_findings(orphan_shadow)
repaired_shadow, repaired_report = harden_text(orphan_shadow)
assert repaired_shadow.count("var __nuvioProviderSilentLog=function(){};") == 1
assert "console.log" not in repaired_shadow
assert known_unsafe_findings(repaired_shadow) == [], known_unsafe_findings(repaired_shadow)
js_ok(repaired_shadow)
repaired_again, repaired_again_report = harden_text(repaired_shadow)
assert repaired_again == repaired_shadow
assert repaired_again_report["alreadyHardened"] is True

# A relocated marker without any concrete declarations is stale metadata, not
# evidence that standard console sinks are already safe.
marker_only = '''/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:deadbeef */
function getStreams(){console.log("x");return []}
globalThis.getStreams=getStreams;'''
marker_repaired, marker_report = harden_text(marker_only)
assert marker_report["consoleSinkChanges"] == 1, marker_report
assert "var __nuvioProviderSilentLog=function(){};" in marker_repaired
assert "console.log" not in marker_repaired
assert known_unsafe_findings(marker_repaired) == []
js_ok(marker_repaired)

mutated = hardened + '\nfunction later(u){return u.includes("evil.example")}'
rehardened, re_report = harden_text(mutated)
assert re_report["hostnameChanges"] == 1, re_report
assert '__nuvioHostMatches(u,"evil.example")' in rehardened
assert rehardened.count("function __nuvioHostMatches(") == 1
js_ok(rehardened)
print("provider security hardening tests passed")

with tempfile.TemporaryDirectory() as raw:
    stage = Path(raw)
    (stage / "providers").mkdir()
    source = stage / "providers" / "one.js"
    # Stage hardening validates the resulting artifact with the same provider
    # validator used by production. Keep the fixture intentionally unsafe while
    # still exposing the mandatory getStreams contract; otherwise this test would
    # be testing an invalid pseudo-provider rather than the hardening pipeline.
    original = (
        b'function f(u){return u.includes("example.com"),console.log(u)};'
        b'globalThis.getStreams=async function(){return []}'
    )
    source.write_bytes(original)
    registry = {
        "candidates": [{
            "key": "x:one",
            "canonical_id": "one",
            "local_path": "providers/one.js",
            "sha256": hashlib.sha256(original).hexdigest(),
            "bytes": len(original),
            "local_patches": [],
        }]
    }
    (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")
    summary = harden_stage(stage)
    assert summary["candidate_count"] == 1 and summary["applied_count"] == 1, summary
    updated = json.loads((stage / "candidates.json").read_text())["candidates"][0]
    data = source.read_bytes()
    assert updated["sha256"] == hashlib.sha256(data).hexdigest()
    assert updated["sha256"] != hashlib.sha256(original).hexdigest()
    assert any(record.get("type") == "provider_security_hardening" for record in updated["local_patches"])
    assert known_unsafe_findings(data.decode("utf-8")) == []
print("staged provider security hardening tests passed")