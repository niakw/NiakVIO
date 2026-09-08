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
from provider_patch_blocks import PROVIDER_BEGIN_MARKER, PROVIDER_END_MARKER


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

# Several escaped capture variants occur in upstream/provider source. They must
# all be removed only when the decoded variable is the one immediately parsed.
variants = [
    r'''const clean = raw.replace(/\\\\(.)/g, '$1');
const parsed = JSON.parse(clean);''',
    r'''const clean = raw.replace(/\\(.)/g, "$1");
const parsed = JSON.parse(clean);''',
    r'''const clean = raw.replace(/\\(.)/g,"$1");
const parsed = JSON.parse(clean);''',
]
for source in variants:
    fixed, fixed_report = harden_text(source)
    assert fixed_report["structuredParseChanges"] == 1, (source, fixed_report)
    assert "replace(" not in fixed.split("JSON.parse", 1)[0], fixed
    js_ok(fixed)

# An unrelated replace using the same shape must remain unchanged.
non_parse = r'''const display = raw.replace(/\\(.)/g, "$1");
return display;'''
non_parse_fixed, non_parse_report = harden_text(non_parse)
assert non_parse_fixed == non_parse
assert non_parse_report["structuredParseChanges"] == 0

# JSON.parse of the raw value is already safe and must remain byte-stable.
safe_parse = '''const parsed = JSON.parse(raw);'''
safe_fixed, safe_report = harden_text(safe_parse)
assert safe_fixed == safe_parse
assert safe_report["structuredParseChanges"] == 0

hostname_source = '''function x(url){return url.includes("example.com") || url.indexOf('stream.test')!==-1 || url.includes(hostVar)}'''
hardened, report = harden_text(hostname_source)
assert report["hostnameChanges"] == 2, report
assert '__nuvioHostMatches(url,"example.com")' in hardened
assert "__nuvioHostMatches(url,'stream.test')" in hardened
assert "url.includes(hostVar)" in hardened
assert known_unsafe_findings(hardened) == [], known_unsafe_findings(hardened)
js_ok(hardened)

# Literals that merely look like host fragments but are paths are not hostname checks.
path_literal = '''function x(url){return url.includes("/api/search") || url.indexOf('/watch/')!==-1}'''
path_fixed, path_report = harden_text(path_literal)
assert path_fixed == path_literal
assert path_report["hostnameChanges"] == 0

console_source = '''function x(){console.log("a");console.warn("b");console.error("c");console.info("d");console.debug("e");}'''
hardened, report = harden_text(console_source)
assert report["consoleSinkChanges"] == 5, report
for sink in ("console.log", "console.warn", "console.error", "console.info", "console.debug"):
    assert sink not in hardened
assert hardened.count("var __nuvioProviderSilentLog=function(){};") == 1
assert known_unsafe_findings(hardened) == [], known_unsafe_findings(hardened)
js_ok(hardened)

# Already-shadowed providers should be idempotent and must not gain duplicate helpers.
hardened_again, again_report = harden_text(hardened)
assert hardened_again == hardened
assert again_report["alreadyHardened"] is True
assert hardened_again.count("var __nuvioProviderSilentLog=function(){};") == 1

# A legacy/orphan helper without the current marker is normalized, not duplicated.
orphan_shadow = '''var __nuvioProviderSilentLog=function(){};
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

# Provider byte hardening and preventive Core security are separate owners.
# Harden the provider bytes first, then compose the resulting Provider and Core
# inside the single v3 envelope. The Core Lego must never rewrite existing Core
# bytes or mutate the already-hardened provider prefix.
core_tail = '''/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
 /* START NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */
function coreHlsLog(v){console.warn("trusted-core-hls",v)}
 /* END NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */
'''
provider_source = 'function p(u){console.warn(u)};globalThis.getStreams=async function(){return []};\n'
hardened_provider, provider_report = harden_text(provider_source)
assert provider_report["consoleSinkChanges"] == 1, provider_report
bundle_input = (
    PROVIDER_BEGIN_MARKER + "\n"
    + hardened_provider.rstrip() + "\n"
    + core_tail
    + PROVIDER_END_MARKER + "\n"
)
secured_bundle, bundle_report = harden_bundle(bundle_input)
boundary = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
assert "__nuvioProviderSilentLog" in secured_bundle.split(boundary, 1)[0]
assert 'function coreHlsLog(v){console.warn("trusted-core-hls",v)}' in secured_bundle
assert secured_bundle.count("/* START NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */") == 1
assert secured_bundle.count("/* END NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */") == 1
assert secured_bundle.count("/* START NIAKVIO_FIX:CORE.PROVIDER_SECURITY_BOUNDARY.V1 */") == 1
assert secured_bundle.count("/* END NIAKVIO_FIX:CORE.PROVIDER_SECURITY_BOUNDARY.V1 */") == 1
assert secured_bundle.index("/* END NIAKVIO_FIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */") < secured_bundle.index("/* START NIAKVIO_FIX:CORE.PROVIDER_SECURITY_BOUNDARY.V1 */")
assert bundle_report["changed"] is True, bundle_report
assert bundle_report["providerMutation"] is False, bundle_report
assert bundle_report["postBuildMutation"] is False, bundle_report

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
            "status": "ok",
        }],
    }
    registry_path = stage / "registry.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    summary = harden_stage(stage, registry_path)
    assert summary["changed"] == 1
    assert summary["remainingFindings"] == 0
    secured = source.read_text(encoding="utf-8")
    assert "__nuvioHostMatches" in secured
    assert "console.log" not in secured
    assert known_unsafe_findings(secured) == []
    updated = json.loads(registry_path.read_text(encoding="utf-8"))
    row = updated["candidates"][0]
    assert row["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert row["bytes"] == len(source.read_bytes())
    assert "scripts/provider_security_hardening.py" in row["local_patches"]

    # Stage hardening is idempotent and must not change the already-secured bytes.
    before = source.read_bytes()
    second = harden_stage(stage, registry_path)
    assert second["changed"] == 0
    assert source.read_bytes() == before
