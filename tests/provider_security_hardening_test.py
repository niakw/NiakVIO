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

logs = '''var TMDB_API_KEY="secret";function f(u){console.log(u+TMDB_API_KEY);console["warn"](TMDB_API_KEY);globalThis.console.error(u)}'''
hardened, report = harden_text(logs)
assert report["consoleShadow"] is True, report
assert "var console={" in hardened
assert "globalThis.console" not in hardened
assert MARKER in hardened
js_ok(hardened)

again, again_report = harden_text(hardened)
assert again == hardened
assert again_report["alreadyHardened"] is True
assert known_unsafe_findings(hardened) == [], known_unsafe_findings(hardened)

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
    original = b'function f(u){return u.includes("example.com"),console.log(u)}'
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
print("staged provider security hardening tests passed")
