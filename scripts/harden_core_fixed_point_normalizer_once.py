#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""One-shot migration of the durable Core fixed-point normalizer.

The generated apply_provider_overrides.py must locate an existing runtime-domain
wrapper without ever scanning through provider-derived bytes. Preserved comments
can survive Terser while the IIFE is reformatted, so searching for a later call
suffix is unsafe. This migration teaches the owning normalizer to identify the
whole marked JavaScript statement with a bounded structural scan, and removes
the generic CommonJS fallback from provider-export boundary discovery.
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "normalize_core_fixed_point_contract.py"
MARKER = "def _harden_generated_apply(text: str) -> str:"

HELPER = dedent(r'''
def _harden_generated_apply(text: str) -> str:
    """Make generated Core rebuild parsing structural and fail-closed."""
    domain_fn = dedent(r'''
def _runtime_domain_wrapper_span(text: str, marker_start: int) -> tuple[int, int] | None:
    """Return the marked pre-provider JS statement without crossing provider bytes."""
    marker_comment = "/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */"
    marker_end = marker_start + len(marker_comment)
    provider_starts = [
        match.start()
        for pattern in (
            r"\b(?:var|let|const)\s+__provider\b",
            r"\bmodule\.exports\s*=\s*__provider\b",
        )
        for match in re.finditer(pattern, text[marker_end:])
    ]
    limit = marker_end + min(provider_starts) if provider_starts else len(text)

    paren = brace = bracket = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    saw_code = False
    index = marker_end
    while index < limit:
        char = text[index]
        nxt = text[index + 1] if index + 1 < limit else ""
        if line_comment:
            if char in "\r\n":
                line_comment = False
        elif block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        else:
            if char in ("'", '"', "`"):
                quote = char
                saw_code = True
            elif char == "/" and nxt == "/":
                line_comment = True
                index += 1
            elif char == "/" and nxt == "*":
                block_comment = True
                index += 1
            elif char == "(":
                paren += 1
                saw_code = True
            elif char == ")":
                paren -= 1
                if paren < 0:
                    return None
            elif char == "{":
                brace += 1
                saw_code = True
            elif char == "}":
                brace -= 1
                if brace < 0:
                    return None
            elif char == "[":
                bracket += 1
                saw_code = True
            elif char == "]":
                bracket -= 1
                if bracket < 0:
                    return None
            elif char == ";" and paren == 0 and brace == 0 and bracket == 0 and saw_code:
                end = index + 1
                if text[end:end + 2] == "\r\n":
                    end += 2
                elif text[end:end + 1] in ("\r", "\n"):
                    end += 1
                return marker_start, end
            elif not char.isspace():
                saw_code = True
        index += 1
    return None


def _inject_runtime_domain_overrides(text: str, replacements: dict[str, Any]) -> tuple[str, int]:
    """Embed host rewriting without allowing marker scans to consume provider code."""
    from urllib.parse import urlparse

    original_text = text
    rules: dict[str, str] = {}
    for old, new in replacements.items():
        old_value = str(old).lower().strip().rstrip("/")
        new_value = str(new).lower().strip().rstrip("/")
        old_host = urlparse(old_value).hostname if "://" in old_value else old_value
        new_host = urlparse(new_value).hostname if "://" in new_value else new_value
        if old_host and new_host and old_host != new_host:
            rules[old_host] = new_host

    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"
    marker_comment = f"/* {marker} */"
    existing_span: tuple[int, int] | None = None
    if marker_comment in text:
        existing_start = text.find(marker_comment)
        existing_span = _runtime_domain_wrapper_span(text, existing_start)
        if existing_span is None:
            raise ValueError("runtime domain override marker is not a bounded pre-provider statement")

    if not rules:
        if existing_span is None:
            return text, 0
        output = text[:existing_span[0]] + text[existing_span[1]:]
        return output, 0 if output == original_text else 1

    import base64
    encoded_rules = [
        [base64.b64encode(old.encode("utf-8")).decode("ascii"), new]
        for old, new in sorted(rules.items())
    ]
    payload = json.dumps(encoded_rules, separators=(",", ":"))
    bootstrap = """/* %s */
;(function(g,rules){
  if(!g||typeof g.fetch!=="function")return;
  var key="__nuvioDomainOverrideV1";
  var state=g[key];
  if(!state){
    state={native:g.fetch.bind(g),rules:Object.create(null)};
    g[key]=state;
    g.fetch=function(input,init){
      var next=input;
      try{
        var raw=(typeof Request!=="undefined"&&input instanceof Request)?input.url:String(input);
        var url=new URL(raw);
        var replacement=state.rules[String(url.hostname).toLowerCase()];
        if(replacement){
          url.hostname=replacement;
          next=(typeof Request!=="undefined"&&input instanceof Request)?new Request(url.toString(),input):url.toString();
        }
      }catch(_error){}
      return state.native(next,init);
    };
  }
  for(var i=0;i<rules.length;i++){
    try{state.rules[atob(rules[i][0])]=rules[i][1];}catch(_error){}
  }
})(typeof globalThis!=="undefined"?globalThis:this,%s);
""" % (marker, payload)

    if existing_span is None:
        output = bootstrap + text
    else:
        output = text[:existing_span[0]] + bootstrap + text[existing_span[1]:]
    return output, 0 if output == original_text else len(rules)
''').lstrip("\n")
    start = text.index("def _inject_runtime_domain_overrides(")
    end = text.index("\ndef _strip_legacy_global_stream_guards", start)
    text = text[:start] + domain_fn + text[end:]

    unsafe_fallback = dedent(r'''
        # A minority of upstream bundles export a provider object directly rather
        # than through __provider. CommonJS export remains the safest generic floor.
        generic = [match.end() for match in re.finditer(r"\bmodule\.exports\s*=", text)]
        return max(generic) if generic else -1
''')
    if unsafe_fallback in text:
        text = text.replace(unsafe_fallback, "        return -1\n", 1)
    elif "CommonJS export remains the safest generic floor" in text:
        raise ValueError("unable to replace generic provider-export fallback")
    return text


''')


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print("Core fixed-point normalizer hardening already materialized")
        return 0

    anchor = "def normalize_apply(text: str) -> str:\n"
    if anchor not in text:
        raise SystemExit("normalize_apply anchor missing")
    text = text.replace(anchor, HELPER + anchor, 1)

    tail = "    return text\n\n\ndef normalize_reapply(text: str) -> str:\n"
    replacement = "    return _harden_generated_apply(text)\n\n\ndef normalize_reapply(text: str) -> str:\n"
    if tail not in text:
        raise SystemExit("normalize_apply return anchor missing")
    text = text.replace(tail, replacement, 1)
    TARGET.write_text(text, encoding="utf-8")
    print("Core fixed-point normalizer hardened: bounded runtime-domain wrapper + proven provider export only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
