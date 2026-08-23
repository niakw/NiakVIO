#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Durable fail-closed transformations for generated Core rebuild code."""
from __future__ import annotations

from textwrap import dedent


SAFE_DOMAIN_FN = dedent(r'''
def _scan_runtime_domain_iife_end(text: str, start: int) -> int | None:
    """Return the end of one complete IIFE statement starting at ``start``."""
    if start < 0 or start >= len(text) or text[start] != "(":
        return None
    paren = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = start
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
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
            elif char == "/" and nxt == "/":
                line_comment = True
                index += 1
            elif char == "/" and nxt == "*":
                block_comment = True
                index += 1
            elif char == "(":
                paren += 1
            elif char == ")":
                paren -= 1
                if paren < 0:
                    return None
                if paren == 0:
                    end = index + 1
                    while end < len(text) and text[end] in " \t":
                        end += 1
                    if end < len(text) and text[end] == ";":
                        end += 1
                    if text[end:end + 2] == "\r\n":
                        end += 2
                    elif text[end:end + 1] in ("\r", "\n"):
                        end += 1
                    return end
        index += 1
    return None


def _runtime_domain_wrapper_span_from_key(text: str, key_index: int) -> tuple[int, int] | None:
    """Own a markerless/minified bootstrap only through its reserved runtime key."""
    window_start = max(0, key_index - 768)
    starts = [
        window_start + match.start()
        for match in re.finditer(r"\(\s*function\s*\(", text[window_start:key_index], re.I)
    ]
    marker_comment = "/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */"
    for start in reversed(starts):
        end = _scan_runtime_domain_iife_end(text, start)
        if end is None or not (start <= key_index < end):
            continue
        candidate = text[start:end]
        required = (
            "__nuvioDomainOverrideV1",
            ".fetch",
            "rules",
            "state",
            "atob",
        )
        if not all(needle in candidate for needle in required):
            continue
        marker_start = text.rfind(marker_comment, max(0, start - 160), start)
        if marker_start >= 0:
            between = text[marker_start + len(marker_comment):start]
            if re.fullmatch(r"\s*;?\s*", between):
                start = marker_start
        return start, end
    return None


def _runtime_domain_wrapper_spans(text: str) -> list[tuple[int, int]]:
    """Return every structurally-owned runtime-domain bootstrap, or fail closed."""
    key = "__nuvioDomainOverrideV1"
    positions = [match.start() for match in re.finditer(re.escape(key), text)]
    spans: list[tuple[int, int]] = []
    for position in positions:
        if any(start <= position < end for start, end in spans):
            continue
        span = _runtime_domain_wrapper_span_from_key(text, position)
        if span is None:
            raise ValueError("unowned runtime-domain reserved key")
        if any(not (span[1] <= start or span[0] >= end) for start, end in spans):
            raise ValueError("overlapping runtime-domain wrappers")
        spans.append(span)
    return sorted(spans)


def _runtime_domain_wrapper_span(text: str, marker_start: int) -> tuple[int, int] | None:
    """Return a marked bootstrap only when the reserved-key IIFE proves ownership."""
    key_index = text.find("__nuvioDomainOverrideV1", marker_start)
    if key_index < 0:
        return None
    span = _runtime_domain_wrapper_span_from_key(text, key_index)
    if span is None or span[0] != marker_start:
        return None
    return span


def _inject_runtime_domain_overrides(text: str, replacements: dict[str, Any]) -> tuple[str, int]:
    """Embed one canonical host-rewrite bootstrap, including after Terser strips its marker.

    The stable reserved key survives compression even when the comment does not.
    Every occurrence must belong to the exact bounded IIFE shape; an unowned key
    fails closed. All proven duplicates are removed and one canonical bootstrap is
    placed at the earliest owned position, so repeated rebuilds cannot grow bytes.
    """
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
    spans = _runtime_domain_wrapper_spans(text)

    # Strip every structurally-owned copy. Stale marker comments outside an owned
    # statement are metadata only and are removed without consuming adjacent code.
    parts: list[str] = []
    cursor = 0
    insertion: int | None = None
    for start, end in spans:
        segment = text[cursor:start].replace(marker_comment, "")
        parts.append(segment)
        if insertion is None:
            insertion = sum(len(part) for part in parts)
        cursor = end
    parts.append(text[cursor:].replace(marker_comment, ""))
    base = "".join(parts)

    if not rules:
        return base, 0 if base == original_text else max(1, len(spans))

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

    # Preserve the established in-place replacement contract for one canonical
    # marked wrapper. Markerless/minified or duplicate wrappers use the structural
    # path below; this keeps older fixed-point assertions meaningful without making
    # the comment authoritative again.
    existing_span = spans[0] if len(spans) == 1 else None
    if existing_span is not None and marker_comment in text[existing_span[0]:existing_span[1]]:
        output = text[:existing_span[0]] + bootstrap + text[existing_span[1]:]
        return output, 0 if output == original_text else len(rules)

    insert_at = insertion if insertion is not None else 0
    output = base[:insert_at] + bootstrap + base[insert_at:]
    return output, 0 if output == original_text else len(rules)
''').lstrip("\n")


SAFE_EXPORT_FN = dedent(r'''
def _balanced_terminal_object_end(text: str, open_brace: int, limit: int) -> int | None:
    """Return the end of one balanced object assignment, or fail closed."""
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = open_brace
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
            elif char == "/" and nxt == "/":
                line_comment = True
                index += 1
            elif char == "/" and nxt == "*":
                block_comment = True
                index += 1
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    return None
                if depth == 0:
                    return index + 1
        index += 1
    return None


def _terminal_provider_export_end(text: str, object_end: int, limit: int) -> int | None:
    """Accept only a terminal object export or a narrow global fallback ternary.

    Obfuscated bundles commonly finish with either::

      module[decoder(...) ]={'getStreams':getStreams};
      cond ? module[decoder(...) ]={'getStreams':getStreams}
           : (global[decoder(...)]=getStreams, global[...]=onSettings);

    The module assignment is already proven by the caller. Any suffix is accepted
    only when it consists exclusively of global/globalThis/self assignments whose
    right-hand sides are identifiers and at least one assigns ``getStreams``. The
    complete statement must be adjacent to the selected post-export Core marker.
    """
    cursor = object_end
    while cursor < limit and text[cursor].isspace():
        cursor += 1
    if cursor >= limit:
        return object_end
    if text[cursor] == ";":
        end = cursor + 1
        return end if not text[end:limit].strip() else None
    if text[cursor] != ":":
        return None

    suffix = text[cursor:limit]
    target = r"(?:globalThis|global|self)\s*(?:\.[A-Za-z_$][\w$]*|\[[^\]\r\n;]{1,160}\])"
    value = r"[A-Za-z_$][\w$]*"
    assignment = rf"{target}\s*=\s*{value}"
    fallback = re.fullmatch(
        rf"\s*:\s*\(?\s*({assignment})(?:\s*,\s*{assignment})*\s*\)?\s*;?\s*",
        suffix,
    )
    if not fallback or "getStreams" not in suffix:
        return None
    return limit


def _provider_export_floor(text: str) -> int:
    """Return a proven provider/Core boundary, never a generic CommonJS guess.

    Normal Nuvio bundles expose ``__provider`` through one of the exact bridges
    below. Some upstream-obfuscated CommonJS bundles instead end with an object
    assignment such as ``module[decoder(...)]=...``. That shape is accepted only
    when the terminal object literally exports ``getStreams`` and the complete
    terminal statement is adjacent to a known Core-tail marker *after* the export.
    Core comments which Terser floated before provider bytes are ignored rather
    than becoming false upper bounds for provider ownership.
    """
    exact_patterns = (
        r"\bmodule\.exports\s*=\s*__provider\b",
        r"\bglobalThis\.getStreams\s*=\s*__provider\.getStreams\b",
        r"\bglobal\.getStreams\s*=\s*__provider\.getStreams\b",
        r"\bself\.getStreams\s*=\s*__provider\.getStreams\b",
    )
    exact_ends = [
        match.end()
        for pattern in exact_patterns
        for match in re.finditer(pattern, text)
    ]
    if exact_ends:
        return max(exact_ends)

    terminal_core_markers = (
        "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
        "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
        "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
        "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
        "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
        "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
        "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
        "NUVIO_GLOBAL_STREAM_FACTS_V1",
        "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
        "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
    )
    core_starts = sorted({
        match.start()
        for marker in terminal_core_markers
        for match in re.finditer(re.escape(f"/* {marker}"), text)
    })
    if not core_starts:
        return -1

    assignment = re.compile(
        r"\bmodule\s*(?:\.exports|\[[^\]\r\n;]{1,160}\])\s*=\s*\{"
    )
    candidates = list(assignment.finditer(text))
    for match in reversed(candidates):
        open_brace = text.find("{", match.start(), match.end())
        if open_brace < 0:
            continue
        object_end = _balanced_terminal_object_end(text, open_brace, len(text))
        if object_end is None:
            continue
        segment = text[match.start():object_end]
        if re.search(r"(?:[\"']getStreams[\"']\s*:|\bgetStreams\s*:)", segment) is None:
            continue
        post_markers = [position for position in core_starts if position > object_end]
        if not post_markers:
            continue
        core_start = min(post_markers)
        statement_end = _terminal_provider_export_end(text, object_end, core_start)
        if statement_end is None:
            continue
        return statement_end
    return -1
''').lstrip("\n")


def _replace_provider_export_floor(text: str) -> str:
    export_start = text.index("def _provider_export_floor(")
    helper_start = text.rfind("def _balanced_terminal_object_end(", 0, export_start)
    start = helper_start if helper_start >= 0 else export_start
    end = text.index("\ndef _strip_generated_core_tail", export_start)
    return text[:start] + SAFE_EXPORT_FN + text[end:]


def harden_generated_apply(text: str) -> str:
    """Harden the generated apply module after the owning normalizer renders it."""
    inject_start = text.index("def _inject_runtime_domain_overrides(")
    helper_start = text.rfind("def _scan_runtime_domain_iife_end(", 0, inject_start)
    if helper_start < 0:
        helper_start = text.rfind("def _runtime_domain_wrapper_span(", 0, inject_start)
    start = helper_start if helper_start >= 0 else inject_start
    end = text.index("\ndef _strip_legacy_global_stream_guards", inject_start)
    text = text[:start] + SAFE_DOMAIN_FN + text[end:]
    text = _replace_provider_export_floor(text)

    if "CommonJS export remains the safest generic floor" in text:
        raise ValueError("unsafe generic provider-export fallback remains")
    if text.count("def _scan_runtime_domain_iife_end(") != 1:
        raise ValueError("runtime-domain IIFE scanner must be generated exactly once")
    if text.count("def _runtime_domain_wrapper_span_from_key(") != 1:
        raise ValueError("markerless runtime-domain ownership parser must be generated exactly once")
    if text.count("def _runtime_domain_wrapper_spans(") != 1:
        raise ValueError("runtime-domain duplicate collector must be generated exactly once")
    if text.count("def _runtime_domain_wrapper_span(") != 1:
        raise ValueError("bounded runtime-domain parser must be generated exactly once")
    if text.count("def _balanced_terminal_object_end(") != 1:
        raise ValueError("terminal CommonJS object parser must be generated exactly once")
    if text.count("def _terminal_provider_export_end(") != 1:
        raise ValueError("terminal provider export statement parser must be generated exactly once")
    if text.count("def _provider_export_floor(") != 1:
        raise ValueError("provider-export floor must be generated exactly once")
    if 'r"\\bmodule\\.exports\\s*=\\s*__provider\\b"' not in text:
        raise ValueError("proven provider export bridge is missing")
    if "terminal_core_markers = (" not in text or "getStreams" not in text:
        raise ValueError("terminal obfuscated CommonJS boundary guard is missing")
    if 'for match in re.finditer(re.escape(f"/* {marker}"), text)' not in text:
        raise ValueError("floated Core markers are not filtered by post-export ownership")
    if "unowned runtime-domain reserved key" not in text:
        raise ValueError("markerless runtime-domain ownership must fail closed")
    return text
