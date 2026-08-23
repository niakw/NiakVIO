#!/usr/bin/env python3
"""Global security hardening for provider JavaScript artifacts.

This layer is intentionally provider-agnostic. It turns recurring security
findings into deterministic transformations that run for every candidate before
runtime validation/publication.
"""
from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAFE_PARSE_PATH = ROOT / "scripts" / "provider_patches" / "safe_structured_parse_v1.py"
MARKER = "NUVIO_PROVIDER_SECURITY_HARDENING_V1"

_DOMAIN = r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}"
_HOST_INCLUDES = re.compile(
    rf"(?P<expr>\b[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)"
    rf"\.includes\(\s*(?P<q>[\"'])(?P<host>{_DOMAIN})(?P=q)\s*\)"
)
_UNSAFE_LITERAL_DECODE = re.compile(
    r'''JSON\.parse\(\s*[\'"]"[\'"]\s*\+\s*(?P<expr>[^;\n]+?)\.replace\(/"/g,\s*[\'\"]\\\\"[\'\"]\)\s*\+\s*[\'\"]"[\'\"]\s*\)'''
)
_CONSOLE_DECL = re.compile(r"\b(?:var|let|const|class|function)\s+console\b")
_CONSOLE_USE = re.compile(r"(?<![\w$])(?:console|globalThis\.console|window\.console)\s*[\[.]")
_GLOBAL_CONSOLE = re.compile(r"\b(?:globalThis|window)\.console(?=\s*[\[.])")
_SILENT_LOG_DECL = re.compile(
    r"\bvar\s+__nuvioProviderSilentLog\s*=\s*function\s*\(\s*\)\s*\{\s*\}\s*;?"
)
_SILENT_LOG_USE = re.compile(r"\b__nuvioProviderSilentLog\b")

_HOST_HELPER = r'''function __nuvioHostMatches(value,expected){
  try{
    var raw=String(value==null?"":value).trim();
    var wanted=String(expected==null?"":expected).toLowerCase().replace(/^\.+|\.+$/g,"");
    if(!raw||!wanted)return false;
    var parsed=new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(raw)?raw:"https://"+raw);
    var host=String(parsed.hostname||"").toLowerCase().replace(/\.$/,"");
    return host===wanted||host.endsWith("."+wanted);
  }catch(_error){return false}
}'''

_LITERAL_HELPER = r'''function __nuvioDecodeEscapedLiteral(value){
  var input=String(value==null?"":value),out="";
  for(var i=0;i<input.length;i++){
    var ch=input.charAt(i);
    if(ch!=="\\"||i+1>=input.length){out+=ch;continue}
    var next=input.charAt(++i),hex;
    if(next==="n"){out+="\n";continue}
    if(next==="r"){out+="\r";continue}
    if(next==="t"){out+="\t";continue}
    if(next==="b"){out+="\b";continue}
    if(next==="f"){out+="\f";continue}
    if(next==="v"){out+="\v";continue}
    if(next==="0"){out+="\0";continue}
    if(next==="x"&&/^[0-9a-fA-F]{2}$/.test(hex=input.slice(i+1,i+3))){
      out+=String.fromCharCode(parseInt(hex,16));i+=2;continue
    }
    if(next==="u"&&/^[0-9a-fA-F]{4}$/.test(hex=input.slice(i+1,i+5))){
      out+=String.fromCharCode(parseInt(hex,16));i+=4;continue
    }
    if(next==="\\"||next==='"'||next==="'"||next==="/"){out+=next;continue}
    out+="\\"+next;
  }
  return out;
}'''

_SILENT_LOG_HELPER = r'''var __nuvioProviderSilentLog=function(){};'''
_CONSOLE_OBJECT = r'''var console={
  log:__nuvioProviderSilentLog,warn:__nuvioProviderSilentLog,
  error:__nuvioProviderSilentLog,info:__nuvioProviderSilentLog,
  debug:__nuvioProviderSilentLog,trace:__nuvioProviderSilentLog,
  dir:__nuvioProviderSilentLog
};'''
_CONSOLE_SHADOW = "/* NUVIO_PROVIDER_CONSOLE_SHADOW_V1 */\n" + _SILENT_LOG_HELPER + "\n" + _CONSOLE_OBJECT


def _load_safe_parse():
    spec = importlib.util.spec_from_file_location("nuvio_safe_structured_parse", SAFE_PARSE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SAFE_PARSE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _insert_prelude(source: str, snippets: list[str], digest: str) -> str:
    if not snippets:
        return source
    cursor = 0
    while True:
        whitespace = re.match(r"\s*", source[cursor:])
        if whitespace:
            cursor += whitespace.end()
        if source.startswith("/*", cursor):
            end = source.find("*/", cursor + 2)
            if end < 0:
                break
            cursor = end + 2
            continue
        if source.startswith("//", cursor):
            end = source.find("\n", cursor + 2)
            cursor = len(source) if end < 0 else end + 1
            continue
        break
    directive = re.match(r'''(?:"use strict"|'use strict')\s*;''', source[cursor:])
    if directive:
        cursor += directive.end()
    marker = "" if MARKER in source else f"\n/* {MARKER}:{digest} */\n"
    payload = marker + "\n".join(snippets) + "\n"
    return source[:cursor] + payload + source[cursor:]


def harden_text(source: str) -> tuple[str, dict[str, Any]]:
    had_marker = MARKER in source
    structured = _load_safe_parse().apply(source)
    structured_changed = structured != source
    source = structured

    source, literal_changes = _UNSAFE_LITERAL_DECODE.subn(
        lambda match: f"__nuvioDecodeEscapedLiteral({match.group('expr')})",
        source,
    )
    source, hostname_changes = _HOST_INCLUDES.subn(
        lambda match: f'__nuvioHostMatches({match.group("expr")},"{match.group("host").lower()}")',
        source,
    )

    snippets: list[str] = []
    if literal_changes and "function __nuvioDecodeEscapedLiteral(" not in source:
        snippets.append(_LITERAL_HELPER)
    if hostname_changes and "function __nuvioHostMatches(" not in source:
        snippets.append(_HOST_HELPER)

    # Terser is allowed to preserve/move comments. Marker presence therefore is
    # never treated as proof that its owning declarations survived. Reconstruct
    # the concrete shadow declarations from structure whenever a previous pass
    # left only part of them behind.
    console_shadow = False
    console_shadow_repair = False
    silent_log_declared = _SILENT_LOG_DECL.search(source) is not None
    silent_log_used = _SILENT_LOG_USE.search(source) is not None
    console_declared = _CONSOLE_DECL.search(source) is not None

    if silent_log_used and not silent_log_declared:
        snippets.append(_SILENT_LOG_HELPER)
        console_shadow_repair = True
        silent_log_declared = True

    if _CONSOLE_USE.search(source) and not console_declared:
        source = _GLOBAL_CONSOLE.sub("console", source)
        if silent_log_declared:
            snippets.append("/* NUVIO_PROVIDER_CONSOLE_SHADOW_V1 */\n" + _CONSOLE_OBJECT)
        else:
            snippets.append(_CONSOLE_SHADOW)
        console_shadow = True

    changed = structured_changed or bool(
        literal_changes or hostname_changes or console_shadow or console_shadow_repair
    )
    report = {
        "changed": changed,
        "alreadyHardened": had_marker and not changed,
        "structuredParseChanges": 1 if structured_changed else 0,
        "literalDecodeChanges": literal_changes,
        "hostnameChanges": hostname_changes,
        "consoleShadow": console_shadow,
        "consoleShadowRepair": console_shadow_repair,
    }
    if not changed:
        return source, report

    digest_input = "|".join(
        str(report[key])
        for key in (
            "structuredParseChanges",
            "literalDecodeChanges",
            "hostnameChanges",
            "consoleShadow",
            "consoleShadowRepair",
        )
    )
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:12]
    source = _insert_prelude(source, snippets, digest)
    return source, report


def harden_bytes(data: bytes) -> tuple[bytes, dict[str, Any]]:
    source = data.decode("utf-8", errors="strict")
    hardened, report = harden_text(source)
    return hardened.encode("utf-8"), report


def known_unsafe_findings(source: str) -> list[str]:
    findings: list[str] = []
    if _HOST_INCLUDES.search(source):
        findings.append("hostname_substring")
    if _UNSAFE_LITERAL_DECODE.search(source):
        findings.append("incomplete_literal_escape")
    try:
        if _load_safe_parse().apply(source) != source:
            findings.append("destructive_structured_unescape")
    except Exception:
        findings.append("structured_parse_scan_failed")
    if _SILENT_LOG_USE.search(source) and not _SILENT_LOG_DECL.search(source):
        findings.append("provider_console_shadow_orphan_helper")
    if _CONSOLE_USE.search(source) and not _CONSOLE_DECL.search(source):
        findings.append("provider_console_unsandboxed")
    return findings


def assert_hardened(source: str) -> None:
    findings = known_unsafe_findings(source)
    if findings:
        raise ValueError("provider security hardening incomplete: " + ",".join(sorted(set(findings))))
