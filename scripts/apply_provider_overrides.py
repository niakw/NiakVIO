#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply durable provider overrides and reusable structural patch profiles.

Stable literal/domain replacements are applied during discovery and promotion.
Structural profiles can declare ``phase: runtime``; those profiles are only
applied by the deep-repair loop after a matching runtime failure signature has
been observed. This keeps the build provider-agnostic while preventing blind
rewrites of every downloaded bundle.
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
from pathlib import Path
from typing import Any, Iterable
from override_text_utils import replace_literal

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
GLOBAL_STREAM_PRESENTATION = "scripts/provider_patches/global_stream_presentation_v1.py"
GLOBAL_RUNTIME_MEDIA_SAFETY = "scripts/provider_patches/runtime_capability_media_safety_v4.py"
GLOBAL_RUNTIME_COMPAT = "scripts/provider_patches/global_runtime_compat_v1.py"
GLOBAL_PROVIDER_BRANDING = "scripts/provider_patches/global_provider_branding_v1.py"
CORE_START_MARKER = "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"
GENERATED_CORE_TAIL_MARKERS = (
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_RUNTIME_COMPAT_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
)


def load_overrides() -> dict[str, Any]:
    if not CONFIG.exists():
        return {}
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    from provider_engine_normalizer import sanitize_provider_hooks
    sanitized, _removed = sanitize_provider_hooks(value, ROOT)
    return sanitized


def _load_patch_module(patch_script: str, provider_id: str):
    patch_path = (ROOT / str(patch_script)).resolve()
    if ROOT not in patch_path.parents or not patch_path.is_file():
        raise ValueError(f"invalid provider patch script: {patch_script}")
    module_name = (
        f"nuvio_provider_patch_{provider_id}_"
        f"{hashlib.sha256(str(patch_path).encode()).hexdigest()[:8]}"
    )
    spec = importlib.util.spec_from_file_location(module_name, patch_path)
    if not spec or not spec.loader:
        raise ValueError(f"cannot load provider patch script: {patch_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def profile_matches(text: str, profile: dict[str, Any]) -> bool:
    """Return whether a profile's structural capability markers match a bundle."""
    all_markers = [str(v) for v in profile.get("detect_all") or []]
    any_markers = [str(v) for v in profile.get("detect_any") or []]
    none_markers = [str(v) for v in profile.get("detect_none") or []]
    if all_markers and not all(marker in text for marker in all_markers):
        return False
    if any_markers and not any(marker in text for marker in any_markers):
        return False
    if none_markers and any(marker in text for marker in none_markers):
        return False
    return bool(all_markers or any_markers or profile.get("auto_apply"))


def _apply_patch_script(
    text: str,
    provider_id: str,
    patch_script: str,
    options: dict[str, Any],
    profile_name: str | None,
) -> str:
    module = _load_patch_module(patch_script, provider_id)
    apply_fn = getattr(module, "apply", None)
    if not callable(apply_fn):
        raise ValueError(f"provider patch {patch_script} has no callable apply()")
    kwargs = {
        "options": options,
        "context": {"provider_id": provider_id, "profile": profile_name},
    }
    signature = inspect.signature(apply_fn)
    if "options" in signature.parameters or any(
        parameter.kind == parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    ):
        result = apply_fn(text, **kwargs)
    else:
        result = apply_fn(text)
    if not isinstance(result, str):
        raise TypeError(f"provider patch {patch_script} must return str")
    return result


def _normalize_profile_names(values: Iterable[str] | None) -> set[str]:
    return {str(value) for value in (values or []) if str(value).strip()}


def _replace_named_function(text: str, function_name: str, replacement: str) -> tuple[str, bool]:
    """Replace a classic named JavaScript function using balanced braces."""
    match = re.search(rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return text, False
    start = match.start()
    brace = text.find("{", match.start(), match.end())
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = brace
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
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[:start] + replacement + text[index + 1 :], True
        index += 1
    raise ValueError(f"unterminated function body: {function_name}")


def _apply_fixed_endpoint(text: str, provider_id: str, config: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    fixed = config.get("fixed_endpoint")
    if not isinstance(fixed, dict):
        return text, None
    function_name = str(fixed.get("resolver_function") or "").strip()
    api = str(fixed.get("api") or "").rstrip("/")
    referer = str(fixed.get("referer") or "").rstrip("/") + "/"
    if not function_name or not api:
        raise ValueError(f"provider_patches.{provider_id}.fixed_endpoint is incomplete")
    marker = f"NUVIO_FIXED_ENDPOINT:{api}"
    if marker in text:
        return text, None
    replacement = (
        f"function {function_name}(){{"
        f"/* {marker} */"
        f"return Promise.resolve({{api:{json.dumps(api)},referer:{json.dumps(referer)}}});"
        "}"
    )
    output, changed = _replace_named_function(text, function_name, replacement)
    if not changed:
        return text, None
    return output, {
        "type": "fixed_endpoint",
        "resolver_function": function_name,
        "api": api,
        "referer": referer,
    }


def _scan_runtime_domain_iife_end(text: str, start: int) -> int | None:
    """Return the end of a complete ``(function(){...})(args)`` statement."""
    if start < 0 or start >= len(text) or text[start] != "(":
        return None

    def balanced(open_index: int) -> int | None:
        if open_index < 0 or open_index >= len(text) or text[open_index] != "(":
            return None
        depth = 0
        quote: str | None = None
        escaped = False
        line_comment = False
        block_comment = False
        index = open_index
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
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth < 0:
                        return None
                    if depth == 0:
                        return index + 1
            index += 1
        return None

    expression_end = balanced(start)
    if expression_end is None:
        return None
    call_start = expression_end
    while call_start < len(text) and text[call_start] in " \t\r\n":
        call_start += 1
    if call_start >= len(text) or text[call_start] != "(":
        return None
    end = balanced(call_start)
    if end is None:
        return None
    while end < len(text) and text[end] in " \t":
        end += 1
    if end < len(text) and text[end] == ";":
        end += 1
    if text[end:end + 2] == "\r\n":
        end += 2
    elif text[end:end + 1] in ("\r", "\n"):
        end += 1
    return end


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


def _runtime_domain_expected_payload(rules: dict[str, str]) -> list[list[str]]:
    import base64
    return [
        [base64.b64encode(old.encode("utf-8")).decode("ascii"), new]
        for old, new in sorted(rules.items())
    ]


def _runtime_domain_span_matches_rules(candidate: str, rules: dict[str, str]) -> bool:
    """Return whether one owned IIFE already carries exactly the requested rules."""
    if not rules:
        return False
    needle = 'typeof globalThis!=="undefined"?globalThis:this,'
    position = candidate.rfind(needle)
    if position < 0:
        return False
    tail = candidate[position + len(needle):]
    try:
        payload, payload_end = json.JSONDecoder().raw_decode(tail)
    except (TypeError, ValueError):
        return False
    remainder = tail[payload_end:].strip()
    if remainder not in (")", ");"):
        return False
    return payload == _runtime_domain_expected_payload(rules)


def _strip_runtime_domain_orphan_calls(
    text: str,
    rules: dict[str, str],
) -> tuple[str, int]:
    """Remove only historical invocation tails whose payload matches generated rules."""
    if not rules:
        return text, 0

    import base64

    needle = 'typeof globalThis!=="undefined"?globalThis:this,'
    decoder = json.JSONDecoder()
    output: list[str] = []
    cursor = 0
    search_at = 0
    removed = 0

    def statement_boundary(start: int) -> bool:
        if start <= 0:
            return True
        index = start - 1
        while index >= 0 and text[index] in " \t":
            index -= 1
        return index < 0 or text[index] in ";}\r\n"

    def authorized(payload: object) -> bool:
        if not isinstance(payload, list) or not payload:
            return False
        for row in payload:
            if not isinstance(row, list) or len(row) != 2:
                return False
            encoded_old, new_host = row
            if not isinstance(encoded_old, str) or not isinstance(new_host, str):
                return False
            try:
                old_host = base64.b64decode(encoded_old, validate=True).decode("utf-8").lower().strip().rstrip("/")
            except Exception:
                return False
            if rules.get(old_host) != new_host.lower().strip().rstrip("/"):
                return False
        return True

    while True:
        position = text.find(needle, search_at)
        if position < 0:
            break
        candidates: list[tuple[int, str]] = []
        if position > 0 and text[position - 1] == "(" and statement_boundary(position - 1):
            candidates.extend(((position - 1, ");"), (position - 1, ")")))
        if statement_boundary(position):
            candidates.append((position, ";"))

        tail = text[position + len(needle):]
        try:
            payload, payload_end = decoder.raw_decode(tail)
        except (TypeError, ValueError):
            payload, payload_end = None, 0

        match: tuple[int, int] | None = None
        if authorized(payload):
            remainder = tail[payload_end:]
            for start, suffix in candidates:
                if not remainder.startswith(suffix):
                    continue
                end = position + len(needle) + payload_end + len(suffix)
                while end < len(text) and text[end] in " \t":
                    end += 1
                if text[end:end + 2] == "\r\n":
                    end += 2
                elif text[end:end + 1] in ("\r", "\n"):
                    end += 1
                match = (start, end)
                break
        if match is None:
            search_at = position + len(needle)
            continue
        start, end = match
        output.append(text[cursor:start])
        cursor = end
        search_at = end
        removed += 1

    if removed == 0:
        return text, 0
    output.append(text[cursor:])
    return "".join(output), removed


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
    text, orphan_count = _strip_runtime_domain_orphan_calls(text, rules)
    spans = _runtime_domain_wrapper_spans(text)
    existing_span = spans[0] if len(spans) == 1 else None
    if rules and existing_span is not None:
        candidate = text[existing_span[0]:existing_span[1]]
        if _runtime_domain_span_matches_rules(candidate, rules):
            return text, 0 if text == original_text else max(1, orphan_count)

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

    insert_at = insertion if insertion is not None else 0
    output = base[:insert_at] + bootstrap + base[insert_at:]
    return output, 0 if output == original_text else len(rules)

def _strip_legacy_global_stream_guards(text: str) -> tuple[str, int]:
    """Remove the obsolete one-size-fits-all output guards."""
    pattern = re.compile(
        r"\n?/\* NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V[123] \*/[\s\S]*$",
        re.MULTILINE,
    )
    output, count = pattern.subn("", text)
    if not count:
        return text, 0
    return output.rstrip() + ("\n" if output else ""), count



def _balanced_terminal_object_end(text: str, open_brace: int, limit: int) -> int | None:
    """Return the end of one balanced brace-delimited declaration, or fail closed."""
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


def _balanced_terminal_paren_end(text: str, open_paren: int, limit: int) -> int | None:
    """Return the end of one balanced parenthesized signature, or fail closed."""
    if open_paren < 0 or open_paren >= limit or text[open_paren] != "(":
        return None
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = open_paren
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
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    return None
                if depth == 0:
                    return index + 1
        index += 1
    return None


def _object_exports_getstreams(segment: str) -> bool:
    """Accept explicit or ES object-shorthand getStreams keys, never value-only hits."""
    if re.search(r"(?:[\"']getStreams[\"']\s*:|\bgetStreams\s*:)", segment):
        return True
    return re.search(r"(?:\{|,)\s*getStreams\s*(?=,|})", segment) is not None


def _safe_binding_object(value: str) -> bool:
    """Accept only a flat identifier-binding object which exports getStreams."""
    value = value.strip()
    if not value.startswith("{") or not value.endswith("}"):
        return False
    end = _balanced_terminal_object_end(value, 0, len(value))
    if end != len(value) or not _object_exports_getstreams(value):
        return False
    identifier = r"[A-Za-z_$][\w$]*"
    key = rf"(?:[A-Za-z_$][\w$]*|[\"'][A-Za-z_$][\w$]*[\"'])"
    prop = rf"(?:{key}\s*:\s*{identifier}|{identifier})"
    return re.fullmatch(
        rf"\{{\s*(?:{prop})(?:\s*,\s*{prop})*\s*,?\s*\}}",
        value,
    ) is not None


def _safe_global_assignments(body: str) -> bool:
    """Accept a list of global bindings to identifiers or safe provider objects."""
    body = body.strip().rstrip(";").strip()
    if body.startswith("(") and body.endswith(")"):
        body = body[1:-1].strip()
    if not body:
        return False
    target = re.compile(
        r"(?:globalThis|global|self)\s*(?:\.[A-Za-z_$][\w$]*|\[[^\]\r\n;]{1,160}\])\s*=\s*"
    )
    identifier = re.compile(r"[A-Za-z_$][\w$]*")
    position = 0
    count = 0
    while position < len(body):
        while position < len(body) and body[position].isspace():
            position += 1
        match = target.match(body, position)
        if not match:
            return False
        position = match.end()
        while position < len(body) and body[position].isspace():
            position += 1
        if position < len(body) and body[position] == "{":
            end = _balanced_terminal_object_end(body, position, len(body))
            if end is None or not _safe_binding_object(body[position:end]):
                return False
            position = end
        else:
            match_value = identifier.match(body, position)
            if not match_value:
                return False
            position = match_value.end()
        count += 1
        while position < len(body) and body[position].isspace():
            position += 1
        if position >= len(body):
            break
        if body[position] not in ",;":
            return False
        position += 1
    return count > 0


def _safe_else_global_suffix(suffix: str) -> bool:
    """Accept only an else branch containing global provider bindings."""
    cleaned = re.sub(r"//[^\r\n]*", "", suffix)
    cleaned = re.sub(r"/\*(?:[^*]|\*(?!/))*\*/", "", cleaned).strip()
    if cleaned.startswith(";"):
        cleaned = cleaned[1:].lstrip()
    braced = re.fullmatch(r"\}\s*else\s*\{([\s\S]*)\}\s*;?\s*", cleaned)
    if braced:
        return _safe_global_assignments(braced.group(1))
    unbraced = re.fullmatch(
        r"else\s+typeof\s+(?:globalThis|global|self)\s*!==?\s*[\"']undefined[\"']\s*&&\s*([\s\S]+?)\s*;?\s*",
        cleaned,
    )
    if unbraced:
        return _safe_global_assignments(unbraced.group(1))
    return False


def _terminal_named_function_suffix_end(text: str, cursor: int, limit: int) -> int | None:
    """Consume only classic named function declarations up to an owned Core marker."""
    position = cursor
    consumed = False
    while True:
        while position < limit and text[position].isspace():
            position += 1
        if position >= limit:
            return limit if consumed else cursor
        match = re.match(r"function\s+[A-Za-z_$][\w$]*\s*\(", text[position:limit])
        if not match:
            return None
        open_paren = text.find("(", position, position + match.end())
        signature_end = _balanced_terminal_paren_end(text, open_paren, limit)
        if signature_end is None:
            return None
        body_start = signature_end
        while body_start < limit and text[body_start].isspace():
            body_start += 1
        if body_start >= limit or text[body_start] != "{":
            return None
        end = _balanced_terminal_object_end(text, body_start, limit)
        if end is None:
            return None
        position = end
        consumed = True


def _terminal_getstreams_function_end(text: str, core_start: int) -> int | None:
    """Bound providers whose public API is a terminal getStreams declaration.

    This covers bundles such as DooFlix that deliberately rely on the runtime global
    declaration instead of a CommonJS export. Nested calls/default expressions in
    the parameter list are scanned structurally; executable suffixes still fail closed.
    """
    matches = list(re.finditer(r"\bfunction\s+getStreams\s*\(", text[:core_start]))
    for match in reversed(matches):
        open_paren = text.find("(", match.start(), match.end())
        signature_end = _balanced_terminal_paren_end(text, open_paren, core_start)
        if signature_end is None:
            continue
        body_start = signature_end
        while body_start < core_start and text[body_start].isspace():
            body_start += 1
        if body_start >= core_start or text[body_start] != "{":
            continue
        end = _balanced_terminal_object_end(text, body_start, core_start)
        if end is None:
            continue
        cursor = end
        while cursor < core_start and text[cursor].isspace():
            cursor += 1
        if cursor < core_start and text[cursor] == ";":
            cursor += 1
        if not text[cursor:core_start].strip():
            return cursor
    return None


def _terminal_provider_export_end(text: str, object_end: int, limit: int) -> int | None:
    """Accept only proven provider glue between an object export and owned Core."""
    raw_suffix = text[object_end:limit]
    if re.fullmatch(r"\s*\)+\s*;?\s*", raw_suffix):
        return limit
    if _safe_else_global_suffix(raw_suffix):
        return limit

    cursor = object_end
    while cursor < limit and text[cursor].isspace():
        cursor += 1
    if cursor >= limit:
        return object_end
    if text[cursor] == ";":
        end = cursor + 1
        if not text[end:limit].strip():
            return end
        function_end = _terminal_named_function_suffix_end(text, end, limit)
        return function_end if function_end is not None and not text[function_end:limit].strip() else None
    if text[cursor] != ":":
        return None
    if _safe_global_assignments(text[cursor + 1:limit]):
        return limit
    return None


def _provider_export_floor(text: str) -> int:
    """Return a proven provider/Core boundary, never a generic CommonJS guess."""
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
        "NUVIO_STREAM_OUTPUT_SANITIZER_V",
        "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",
        "NUVIO_DESKTOP_RUNTIME_COMPAT_V1",
        "NUVIO_TV_DIRECT_MEDIA_V2",
        "NUVIO_ANIMEZEY_STREAM_HOST_V1",
        "NUVIO_TV_PLAYABLE_FIRST_V1",
        "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
        "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
        "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
        "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
        "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
        "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
        "NUVIO_GLOBAL_STREAM_FACTS_V1",
        "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
        "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
        "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V",
        "NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1",
        "NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V",
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
        if not _object_exports_getstreams(segment):
            continue
        post_markers = [position for position in core_starts if position > object_end]
        if not post_markers:
            continue
        core_start = min(post_markers)
        statement_end = _terminal_provider_export_end(text, object_end, core_start)
        if statement_end is None:
            continue
        return statement_end

    for core_start in core_starts:
        function_end = _terminal_getstreams_function_end(text, core_start)
        if function_end is not None:
            return function_end
    return -1

def _strip_generated_core_tail(text: str) -> tuple[str, bool]:
    """Recover provider bytes without ever cutting before the export bridge.

    Terser is allowed to preserve comments while changing their attachment to
    AST nodes. Therefore a Core boundary/marker found before the provider export
    is stale metadata, not a truncation point. Stale boundary comments are
    removed, then only markers at or after the export floor may delimit the
    generated Core tail. Unknown export shapes fail closed and retain all bytes.
    """
    original = text
    boundary_needle = f"/* {CORE_START_MARKER} */"
    floor = _provider_export_floor(text)
    if floor < 0:
        return text, False

    boundary_index = text.find(boundary_needle, floor)
    if boundary_index >= floor:
        prefix = text[:boundary_index].replace(boundary_needle, "").rstrip()
        return prefix, True

    # A preserved comment may have floated before the provider bridge. It must
    # not suppress insertion of a fresh post-export boundary on reconstruction.
    if boundary_needle in text:
        text = text.replace(boundary_needle, "")
        floor = _provider_export_floor(text)
        if floor < 0:
            return original, False

    legacy_markers = tuple(GENERATED_CORE_TAIL_MARKERS) + (
        "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2",
        "NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1",
        "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1",
        "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
        "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1",
        "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
    )
    starts = []
    for marker in legacy_markers:
        index = text.find(f"/* {marker}", floor)
        if index >= floor:
            starts.append(index)
    if starts:
        return text[:min(starts)].rstrip(), True
    return text, text != original

def apply_overrides(
    provider_id: str,
    data: bytes,
    *,
    phase: str = "discovery",
    profile_names: Iterable[str] | None = None,
) -> tuple[bytes, list[dict[str, Any]]]:
    """Apply stable replacements and profiles allowed for the selected phase."""
    config = load_overrides()
    text = data.decode("utf-8")
    original_text = text
    applied: list[dict[str, Any]] = []
    if phase == "discovery":
        text, removed_core_tail = _strip_generated_core_tail(text)
        if removed_core_tail:
            applied.append({
  "type": "rebuild_generated_core_tail",
  "phase": phase,
  "scope": "global_core_tail",
            })
    provider_id = provider_id.casefold()
    specific = (config.get("provider_patches") or {}).get(provider_id, {})
    if not isinstance(specific, dict):
        raise ValueError(f"provider_patches.{provider_id} must be an object")

    replacements = dict(config.get("domain_replacements") or {})
    replacements.update(specific.get("replacements") or {})
    replacements.update(specific.get("route_replacements") or {})
    for old, new in replacements.items():
        old_text, new_text = str(old), str(new)
        text, count = replace_literal(text, old_text, new_text)
        if count:
            applied.append({
                "type": "replace",
                "from": old_text,
                "to": new_text,
                "count": count,
                "phase": phase,
            })

    text, fixed_record = _apply_fixed_endpoint(text, provider_id, specific)
    if fixed_record:
        fixed_record["phase"] = phase
        applied.append(fixed_record)

    runtime_replacements = specific.get("runtime_domain_replacements") or {}
    if not isinstance(runtime_replacements, dict):
        raise ValueError(f"provider_patches.{provider_id}.runtime_domain_replacements must be an object")
    text, runtime_rule_count = _inject_runtime_domain_overrides(text, runtime_replacements)
    if runtime_rule_count:
        applied.append({"type": "runtime_domain_overrides", "count": runtime_rule_count, "phase": phase})

    text, removed_guards = _strip_legacy_global_stream_guards(text)
    if removed_guards:
        applied.append({"type": "remove_legacy_global_stream_guard", "count": removed_guards, "phase": phase})

    profiles = config.get("patch_profiles") or {}
    if not isinstance(profiles, dict):
        raise ValueError("patch_profiles must be an object")

    explicitly_requested = _normalize_profile_names(profile_names)
    explicitly_requested.update(str(value) for value in (specific.get("profiles") or []))
    unknown = explicitly_requested - set(profiles)
    if unknown:
        raise ValueError("unknown patch profile(s): " + ", ".join(sorted(unknown)))

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        profile_phase = str(profile.get("phase") or "discovery")
        requested = profile_name in explicitly_requested and profile_phase == phase
        automatic = bool(profile.get("auto_apply")) and profile_phase == phase
        if not (requested or automatic):
            continue
        if not profile_matches(text, profile):
            continue
        patch_script = profile.get("patch_script")
        if not patch_script:
            raise ValueError(f"patch profile {profile_name} has no patch_script")
        options = dict(profile.get("options") or {})
        options.setdefault("detect_all", profile.get("detect_all") or [])
        options.setdefault("detect_any", profile.get("detect_any") or [])
        before = text
        text = _apply_patch_script(text, provider_id, str(patch_script), options, str(profile_name))
        if text != before:
            applied.append({
                "type": "patch_profile",
                "profile": str(profile_name),
                "path": str(patch_script),
                "phase": profile_phase,
            })

    patch_scripts: list[str] = []
    configured_scripts = specific.get("patch_scripts")
    if configured_scripts is not None:
        if not isinstance(configured_scripts, list):
            raise ValueError(f"provider_patches.{provider_id}.patch_scripts must be an array")
        patch_scripts.extend(str(value) for value in configured_scripts if str(value).strip())
    legacy_patch_script = specific.get("patch_script")
    if legacy_patch_script and str(legacy_patch_script) not in patch_scripts:
        patch_scripts.append(str(legacy_patch_script))

    script_options = specific.get("patch_script_options") or {}
    if not isinstance(script_options, dict):
        raise ValueError(f"provider_patches.{provider_id}.patch_script_options must be an object")
    for patch_script in patch_scripts if phase == "discovery" else []:
        per_script_options = script_options.get(patch_script)
        if per_script_options is None:
            per_script_options = specific.get("patch_options") or {}
        if not isinstance(per_script_options, dict):
            raise ValueError(
                f"provider_patches.{provider_id}.patch_script_options[{patch_script!r}] must be an object"
            )
        before = text
        text = _apply_patch_script(text, provider_id, patch_script, dict(per_script_options), None)
        if text != before:
            applied.append({"type": "patch_script", "path": patch_script, "phase": phase})

    if phase == "discovery":
        playback_policy = config.get("playback_integrity_policy") or {}
        if not isinstance(playback_policy, dict):
            raise ValueError("playback_integrity_policy must be an object")
        global_hooks = playback_policy.get("global_discovery_hooks") or []
        if not isinstance(global_hooks, list):
            raise ValueError("playback_integrity_policy.global_discovery_hooks must be an array")
        pre_media_hooks = playback_policy.get("pre_media_discovery_hooks") or []
        post_media_hooks = playback_policy.get("post_media_discovery_hooks") or []
        if not isinstance(pre_media_hooks, list) or not isinstance(post_media_hooks, list):
            raise ValueError("playback integrity staged hook lists must be arrays")
        global_options = playback_policy.get("hls_runtime_options") or {}
        if not isinstance(global_options, dict):
            raise ValueError("playback_integrity_policy.hls_runtime_options must be an object")

        provider_floor = _provider_export_floor(text)
        boundary_needle = f"/* {CORE_START_MARKER} */"
        if provider_floor >= 0 and text.find(boundary_needle, provider_floor) < 0:
            text = text.rstrip() + f"\n{boundary_needle}\n"

        def _apply_playback_stage(hooks: list[str]) -> None:
            nonlocal text
            if not playback_policy.get("enabled", True):
                return
            for patch_script in [str(value) for value in hooks if str(value).strip()]:
                options = dict(global_options) if patch_script.endswith("hls_runtime_integrity_v1.py") else {}
                provider_options = script_options.get(patch_script)
                if provider_options is not None:
                    if not isinstance(provider_options, dict):
                        raise ValueError(
                            f"provider_patches.{provider_id}.patch_script_options[{patch_script!r}] must be an object"
                        )
                    options.update(provider_options)
                before = text
                text = _apply_patch_script(text, provider_id, patch_script, options, None)
                if text != before:
                    applied.append({
                        "type": "patch_script",
                        "path": patch_script,
                        "phase": phase,
                        "scope": "global_playback_integrity",
                    })

        _apply_playback_stage(pre_media_hooks)
        capability = str(specific.get("capability") or "").strip().casefold()
        catalogue_policy = config.get("catalogue_resolution_policy") or {}
        if not isinstance(catalogue_policy, dict):
            raise ValueError("catalogue_resolution_policy must be an object")
        catalogue_capabilities = {
            str(value).strip().casefold()
            for value in catalogue_policy.get("capabilities", [])
            if str(value).strip()
        }
        official_site = str(specific.get("official_site") or "").strip()
        if catalogue_policy.get("enabled", False) and capability in catalogue_capabilities and official_site:
            patch_script = str(catalogue_policy.get("global_discovery_hook") or "").strip()
            if not patch_script:
                raise ValueError("catalogue_resolution_policy.global_discovery_hook is required")
            options = dict(catalogue_policy.get("options") or {})
            provider_options = script_options.get(patch_script)
            if provider_options is not None:
                if not isinstance(provider_options, dict):
                    raise ValueError(
                        f"provider_patches.{provider_id}.patch_script_options[{patch_script!r}] must be an object"
                    )
                options.update(provider_options)
            options.update({"base_url": official_site, "provider_name": provider_id})
            before = text
            text = _apply_patch_script(text, provider_id, patch_script, options, None)
            if text != before:
                applied.append({
                    "type": "patch_script",
                    "path": patch_script,
                    "phase": phase,
                    "scope": "global_catalogue_resolution",
                })

        media_policy = config.get("media_enrichment_policy") or {}
        if not isinstance(media_policy, dict):
            raise ValueError("media_enrichment_policy must be an object")
        media_capabilities = {
            str(value).strip().casefold()
            for value in media_policy.get("capabilities", [])
            if str(value).strip()
        }
        if media_policy.get("enabled", False) and capability in media_capabilities:
            patch_script = str(media_policy.get("global_discovery_hook") or "").strip()
            if not patch_script:
                raise ValueError("media_enrichment_policy.global_discovery_hook is required")
            options = dict(media_policy.get("options") or {})
            provider_options = script_options.get(patch_script)
            if provider_options is not None:
                if not isinstance(provider_options, dict):
                    raise ValueError(
                        f"provider_patches.{provider_id}.patch_script_options[{patch_script!r}] must be an object"
                    )
                options.update(provider_options)
            before = text
            text = _apply_patch_script(text, provider_id, patch_script, options, None)
            if text != before:
                applied.append({
                    "type": "patch_script",
                    "path": patch_script,
                    "phase": phase,
                    "scope": "global_media_enrichment",
                })

        # Runtime media safety is a Core-wide responsibility. Apply the dedicated
        # current implementation after provider/catalogue/media recovery and before
        # the final HLS/audio ordering hook. Provider-specific legacy entries may
        # still invoke the same module earlier; its stable marker makes that harmless,
        # while the public HLS adapter below repositions the single wrapper around
        # the final recovered rows.
        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_RUNTIME_MEDIA_SAFETY, {}, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_RUNTIME_MEDIA_SAFETY,
                "phase": phase,
                "scope": "global_runtime_media_safety",
            })

        _apply_playback_stage(post_media_hooks)
        staged_hooks = {str(value) for value in pre_media_hooks + post_media_hooks if str(value).strip()}
        legacy_tail_hooks = [
            str(value) for value in global_hooks
            if str(value).strip() and str(value) not in staged_hooks
        ]
        _apply_playback_stage(legacy_tail_hooks)

        # Runtime portability is a Core concern. Apply it to every reconstructed
        # provider after provider-specific network/playback recovery but before any
        # stream wrapper. It only normalizes JS host semantics (URL/fetch/timers).
        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_RUNTIME_COMPAT, {}, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_RUNTIME_COMPAT,
                "phase": phase,
                "scope": "global_runtime_compat",
            })

        # Presentation is a Core-wide finalization layer, not a provider capability.
        # Apply it after catalogue/media/playback recovery to every reconstructed
        # provider bundle. It only normalizes structured facts and optionally enriches
        # non-empty rows with TMDB metadata; it never changes playback URL/headers.
        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_STREAM_PRESENTATION, {}, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_STREAM_PRESENTATION,
                "phase": phase,
                "scope": "global_stream_presentation",
            })

        # Provider branding is deliberately the final Core stream layer. Upstream
        # stream names can contain quality/language/codec facts; presentation must
        # read those originals before the committed emoji/name replaces the local
        # row label and title prefix.
        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_PROVIDER_BRANDING, {}, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_PROVIDER_BRANDING,
                "phase": phase,
                "scope": "global_provider_branding",
            })

    if text == original_text:
        return data, []
    return text.encode("utf-8"), applied
