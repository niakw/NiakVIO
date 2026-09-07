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
from provider_patches.global_provider_security_hardening_v1 import harden_bundle


def js_ok(text: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(text)
        name = handle.name
    completed = subprocess.run(["node", "--check", name], capture_output=True, text=True)
    Path(name).unlink(missing_ok=True)
    assert completed.returncode == 0, completed.stderr


# Structured-parse repair is Learning-only since 2026-09-03. The global security
# transform must not rewrite these provider semantics behind Learning's ownership.
cinema = '''"use strict";\nfunction x(rawFile){\n const unescaped = rawFile.replace(/\\\\(.)/g, "$1");\n return JSON.parse(unescaped);\n}\n'''
hardened, report = harden_text(cinema)
assert report["structuredParseChanges"] == 0, report
assert hardened == cinema, (report, hardened)
js_ok(hardened)

anizone = r'''const jsonStr = jsonMatch[1].replace(/\\\\/g, "\\").replace(/\\u([0-9a-fA-F]{4})/g, (m, grp) => String.fromCharCode(parseInt(grp, 16))).replace(/\\'/g, "'");
const parsed = JSON.parse(jsonStr);'''
hardened, report = harden_text(anizone)
assert report["structuredParseChanges"] == 0, report
assert hardened == anizone, (report, hardened)
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

core_tail = '''/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
 /* START NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */
function coreHlsLog(v){console.warn("trusted-core-hls",v)}
 /* END NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */
'''
provider_prefix = 'function p(u){console.warn(u)};globalThis.getStreams=async function(){return []};\n'
secured_bundle, bundle_report = harden_bundle(provider_prefix + core_tail)
boundary = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
assert "__nuvioProviderSilentLog" in secured_bundle.split(boundary, 1)[0]
assert 'function coreHlsLog(v){console.warn("trusted-core-hls",v)}' in secured_bundle
assert secured_bundle.count("/* START NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */") == 1
assert secured_bundle.count("/* END NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */") == 1
assert secured_bundle.count("/* START NIAKVIO_FIX:CORE.PROVIDER_SECURITY_BOUNDARY.V1 */") == 1
assert secured_bundle.count("/* END NIAKVIO_FIX:CORE.PROVIDER_SECURITY_BOUNDARY.V1 */") == 1
assert secured_bundle.index("/* END NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */") < secured_bundle.index("/* START NIAKVIO_FIX:CORE.PROVIDER_SECURITY_BOUNDARY.V1 */")
assert bundle_report["consoleSinkChanges"] == 1, bundle_report

print("provider security hardening tests passed")

with tempfile.TemporaryDirectory() as raw:
    stage = Path(raw)
    (stage / "providers").mkdir()
    source = stage / "providers" / "one.js"
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
    registry_path = stage / "candidates.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    rejected = False
    try:
        harden_stage(stage)
    except ValueError as exc:
        rejected = "not security-normalized" in str(exc)
    assert rejected
    assert source.read_bytes() == original

    secured_text = (
        "/* NUVIO_PROVIDER_SECURITY_HARDENING_V1:test-fixture */\n"
        "var __nuvioProviderSilentLog=function(){};\n"
        "globalThis.__nuvioGlobalProviderSecurityBoundaryV1=true;\n"
        "globalThis.getStreams=async function(){return []};\n"
    )
    secured = secured_text.encode("utf-8")
    source.write_bytes(secured)
    registry["candidates"][0]["sha256"] = hashlib.sha256(secured).hexdigest()
    registry["candidates"][0]["bytes"] = len(secured)
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    before = source.read_bytes()
    summary = harden_stage(stage)
    after = source.read_bytes()
    assert summary["candidate_count"] == 1, summary
    assert summary["applied_count"] == 0, summary
    assert summary["already_hardened_count"] == 1, summary
    assert summary["requires_runtime_retest"] is False, summary
    assert before == after == secured
    updated = json.loads(registry_path.read_text())["candidates"][0]
    assert updated["sha256"] == hashlib.sha256(secured).hexdigest()
    assert updated["local_patches"] == []
    assert known_unsafe_findings(secured_text) == []
print("staged provider security validation-only tests passed")
