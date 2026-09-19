#!/usr/bin/env python3
"""NiakVIO-owned static route/request analyzer.

This module extends Provider v3 contract recognition without executing provider
JavaScript. It is intentionally conservative: it evaluates only bounded string
construction patterns that are safe to understand statically (literals, template
strings, concatenation, identifier aliases and a few transparent wrappers).

The analyzer is source-agnostic. It consumes JavaScript text already available to
NiakVIO and produces route/request DATA; no repository identity is required.
"""
from __future__ import annotations

import re
from typing import Any, Callable

try:
    from discover_candidates import decode_static_obfuscated_strings
except Exception:  # pragma: no cover - discovery module may be unavailable in tiny unit fixtures
    decode_static_obfuscated_strings = None  # type: ignore[assignment]

FETCH_NAMES = (
    "fetchJson",
    "fetchText",
    "safeFetch",
    "fetchPlain",
    "fetch",
    "request",
    "postSearch",
)
FETCH_CALL_RE = re.compile(r"\b(" + "|".join(map(re.escape, FETCH_NAMES)) + r")\s*\(", re.I)
ASSIGN_RE = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", re.M)
FUNC_RE = re.compile(r"\b(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)", re.M)
METHOD_RE = re.compile(r"\bmethod\s*:\s*['\"](GET|POST|PUT|PATCH|DELETE)['\"]", re.I)
FORM_RE = re.compile(r"application/x-www-form-urlencoded|URLSearchParams", re.I)
JSON_BODY_RE = re.compile(r"\bbody\s*:\s*JSON\.stringify\s*\((.+?)\)", re.I | re.S)
BODY_RE = re.compile(r"\bbody\s*:\s*([^,}\n]+)", re.I)
HEADER_REFERER_RE = re.compile(r"\b(?:Referer|referer)\s*:")
HEADER_ORIGIN_RE = re.compile(r"\b(?:Origin|origin)\s*:")
OBJECT_KEY_RE = re.compile(r"(?:^|[,\{])\s*(?:['\"]([^'\"]+)['\"]|([A-Za-z_$][\w$-]*))\s*:")
STRING_LITERAL_RE = re.compile(r"^(['\"])(.*)\1$", re.S)
IDENT_RE = re.compile(r"^[A-Za-z_$][\w$]*$")
TRANSPARENT_CALL_RE = re.compile(
    r"^(?:encodeURIComponent|encodeURI|String|String\.raw|decodeURIComponent)\s*\((.*)\)$",
    re.I | re.S,
)


def _decoded_text(text: str) -> tuple[str, list[str]]:
    """Append useful decoded static strings while preserving the original text.

    The decoder is bounded and does not execute JavaScript. Decoded values are
    evidence only; they never become executable unless route/request evidence also
    exists or the normal recognizer already accepts the route family.
    """
    if not decode_static_obfuscated_strings:
        return text, []
    try:
        decoded = decode_static_obfuscated_strings(text)
    except Exception:
        decoded = []
    if not decoded:
        return text, []
    return text + "\n/* NIAKVIO_STATIC_DECODED_EVIDENCE */\n" + "\n".join(decoded), decoded


def _skip_space(text: str, pos: int) -> int:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def _scan_balanced(text: str, start: int, *, stop_at_comma: bool = False) -> tuple[str, int]:
    """Read a bounded JS expression until ; or top-level comma/closing paren.

    This is not a JavaScript parser. It only tracks quotes/templates and bracket
    depth so common URL-building expressions can be recognized safely.
    """
    pos = _skip_space(text, start)
    out: list[str] = []
    paren = bracket = brace = 0
    quote = ""
    escape = False
    template_expr_depth = 0
    limit = min(len(text), pos + 6000)
    while pos < limit:
        ch = text[pos]
        if quote:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif quote == "`" and ch == "$" and pos + 1 < limit and text[pos + 1] == "{":
                out.append("{")
                pos += 1
                template_expr_depth += 1
            elif quote == "`" and template_expr_depth and ch == "}":
                template_expr_depth -= 1
            elif ch == quote and not template_expr_depth:
                quote = ""
            pos += 1
            continue
        if ch in "'\"`":
            quote = ch
            out.append(ch)
            pos += 1
            continue
        if ch == "(":
            paren += 1
        elif ch == ")":
            if paren == 0 and bracket == 0 and brace == 0:
                break
            paren = max(0, paren - 1)
        elif ch == "[":
            bracket += 1
        elif ch == "]":
            bracket = max(0, bracket - 1)
        elif ch == "{":
            brace += 1
        elif ch == "}":
            if brace == 0 and paren == 0 and bracket == 0:
                break
            brace = max(0, brace - 1)
        elif ch == ";" and paren == 0 and bracket == 0 and brace == 0:
            break
        elif ch == "," and stop_at_comma and paren == 0 and bracket == 0 and brace == 0:
            break
        out.append(ch)
        pos += 1
    return "".join(out).strip(), pos


def _first_call_arg(text: str, open_paren: int) -> tuple[str, int]:
    return _scan_balanced(text, open_paren + 1, stop_at_comma=True)


def _split_top_level_plus(expr: str) -> list[str]:
    parts: list[str] = []
    start = 0
    paren = bracket = brace = 0
    quote = ""
    escape = False
    template_expr_depth = 0
    i = 0
    while i < len(expr):
        ch = expr[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif quote == "`" and ch == "$" and i + 1 < len(expr) and expr[i + 1] == "{":
                i += 1
                template_expr_depth += 1
            elif quote == "`" and template_expr_depth and ch == "}":
                template_expr_depth -= 1
            elif ch == quote and not template_expr_depth:
                quote = ""
            i += 1
            continue
        if ch in "'\"`":
            quote = ch
        elif ch == "(":
            paren += 1
        elif ch == ")":
            paren = max(0, paren - 1)
        elif ch == "[":
            bracket += 1
        elif ch == "]":
            bracket = max(0, bracket - 1)
        elif ch == "{":
            brace += 1
        elif ch == "}":
            brace = max(0, brace - 1)
        elif ch == "+" and paren == 0 and bracket == 0 and brace == 0:
            parts.append(expr[start:i].strip())
            start = i + 1
        i += 1
    parts.append(expr[start:].strip())
    return [part for part in parts if part]


def _unquote(token: str) -> str | None:
    token = token.strip()
    match = STRING_LITERAL_RE.match(token)
    if not match:
        return None
    value = match.group(2)
    value = value.replace("\\/", "/")
    value = value.replace("\\'", "'").replace('\\"', '"')
    value = value.replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t")
    return value


def _template_value(token: str, placeholder: Callable[[str], str | None]) -> str | None:
    token = token.strip()
    if len(token) < 2 or token[0] != "`" or token[-1] != "`":
        return None
    body = token[1:-1]
    def repl(match: re.Match[str]) -> str:
        return placeholder(match.group(1)) or ""
    return re.sub(r"\$\{([^{}]{1,300})\}", repl, body).replace("\\/", "/")


def _strip_outer_parens(value: str) -> str:
    value = value.strip()
    changed = True
    while changed and len(value) >= 2 and value[0] == "(" and value[-1] == ")":
        changed = False
        depth = 0
        quote = ""
        escape = False
        for i, ch in enumerate(value):
            if quote:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    quote = ""
                continue
            if ch in "'\"`":
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(value) - 1:
                    break
        else:
            if depth == 0:
                value = value[1:-1].strip()
                changed = True
    return value


def _eval_piece(
    token: str,
    env: dict[str, str],
    placeholder: Callable[[str], str | None],
    depth: int = 0,
) -> str:
    if depth > 6:
        return ""
    token = _strip_outer_parens(token.strip())
    if not token:
        return ""
    literal = _unquote(token)
    if literal is not None:
        return literal
    template = _template_value(token, placeholder)
    if template is not None:
        return template
    if IDENT_RE.match(token):
        if token in env:
            return env[token]
        return placeholder(token) or ""
    transparent = TRANSPARENT_CALL_RE.match(token)
    if transparent:
        inner = transparent.group(1).strip()
        return placeholder(inner) or _eval_expr(inner, env, placeholder, depth + 1)
    # Common member access used by search/detail chains. Keep semantic placeholders
    # only where they add identity; generic .url/.href members contribute no path.
    if re.search(r"\.(?:slug|permalink)\b", token, re.I):
        return "{slug}"
    if re.search(r"\.(?:id|_id|post_id|media_id)\b", token, re.I):
        return "{id}"
    direct = placeholder(token)
    if direct:
        return direct
    return ""


def _eval_expr(
    expr: str,
    env: dict[str, str],
    placeholder: Callable[[str], str | None],
    depth: int = 0,
) -> str:
    if depth > 6:
        return ""
    expr = _strip_outer_parens(expr.strip())
    parts = _split_top_level_plus(expr)
    if len(parts) > 1:
        return "".join(_eval_piece(part, env, placeholder, depth + 1) for part in parts)
    return _eval_piece(expr, env, placeholder, depth + 1)


def _assignment_env(text: str, placeholder: Callable[[str], str | None]) -> dict[str, str]:
    raw: dict[str, str] = {}
    for match in ASSIGN_RE.finditer(text):
        expr, _ = _scan_balanced(text, match.end(), stop_at_comma=False)
        if expr and len(expr) <= 5000:
            raw[match.group(1)] = expr
    env: dict[str, str] = {}
    # Multiple passes resolve aliases/constants without executing anything.
    for _ in range(5):
        changed = False
        for name, expr in raw.items():
            value = _eval_expr(expr, env, placeholder)
            if not value:
                continue
            if len(value) > 1400:
                continue
            if env.get(name) != value:
                env[name] = value
                changed = True
        if not changed:
            break
    return env


def _normalize_route(value: str, recognizer: Any) -> str | None:
    value = str(value or "").strip()
    if not value:
        return None
    # Dynamic hosts are deliberately discarded; path/query DATA is what runtime
    # plans need. Example: 'https://' + workerHost + '/api/search'.
    if value.startswith("https://") or value.startswith("http://"):
        route = recognizer.normalize_dynamic(value)
        if route:
            return route
    first_slash = value.find("/")
    if first_slash > 0 and not value.startswith("/"):
        value = value[first_slash:]
    route = recognizer.normalize_dynamic(value)
    if not route or recognizer.route_is_junk(route):
        return None
    return route


def extract_expression_routes(text: str, recognizer: Any) -> tuple[list[str], dict[str, dict[str, Any]], list[str]]:
    augmented, decoded = _decoded_text(text)
    env = _assignment_env(augmented, recognizer.expression_placeholder)
    routes: list[str] = []
    evidence: dict[str, dict[str, Any]] = {}

    for match in FETCH_CALL_RE.finditer(augmented):
        expr, end = _first_call_arg(augmented, match.end() - 1)
        value = _eval_expr(expr, env, recognizer.expression_placeholder)
        route = _normalize_route(value, recognizer)
        if not route:
            continue
        if route not in routes:
            routes.append(route)
        evidence[route] = {
            "call": match.group(1),
            "expression": expr[:900],
            "position": match.start(),
            "end": end,
            "executedEvidence": True,
            "evidence": "fetch-expression",
            "confidence": 0.98 if expr.strip().startswith(("'", '"', "`")) else 0.94,
        }

    # Route-bearing assignments are useful when a variable is passed to a wrapper
    # whose call shape is too obfuscated for the direct scanner.
    for name, value in env.items():
        route = _normalize_route(value, recognizer)
        if not route:
            continue
        if not recognizer.route_is_executable_candidate(route):
            continue
        if route not in routes:
            routes.append(route)
        evidence.setdefault(route, {
            "call": None,
            "expression": name,
            "position": -1,
            "end": -1,
            "executedEvidence": bool(re.search(r"\b(?:fetch|fetchText|fetchJson|fetchPlain|request)\s*\(\s*" + re.escape(name) + r"\b", augmented, re.I)),
            "evidence": "route-assignment",
            "confidence": 0.9,
        })

    # Decoded strings are evidence but never marked as executed by themselves.
    for value in decoded:
        route = _normalize_route(value, recognizer)
        if not route or not recognizer.route_is_executable_candidate(route):
            continue
        if route not in routes:
            routes.append(route)
        evidence.setdefault(route, {
            "call": None,
            "expression": "decoded-static-string",
            "position": -1,
            "end": -1,
            "executedEvidence": False,
            "evidence": "decoded-static-string",
            "confidence": 0.72,
        })

    return routes[:192], evidence, decoded


def _object_keys(value: str) -> list[str]:
    keys: list[str] = []
    for match in OBJECT_KEY_RE.finditer(value or ""):
        key = str(match.group(1) or match.group(2) or "").strip().casefold()
        if key and key not in keys:
            keys.append(key)
    return keys[:24]


def _function_param_object_keys(text: str) -> dict[str, list[str]]:
    """Infer object-field contracts passed to helper functions.

    Covers patterns such as `_postSearch({q: query, page_token: null})` followed
    by `body: JSON.stringify(payload)` inside `_postSearch(payload)`.
    """
    output: dict[str, list[str]] = {}
    for match in FUNC_RE.finditer(text):
        name = match.group(1)
        params = [part.strip() for part in match.group(2).split(",") if part.strip()]
        if not params:
            continue
        # Look for direct object-literal calls to this helper anywhere in the file.
        call_re = re.compile(r"\b" + re.escape(name) + r"\s*\(\s*\{([^{}]{1,1200})\}\s*\)", re.S)
        keys: list[str] = []
        for call in call_re.finditer(text):
            for key in _object_keys("{" + call.group(1) + "}"):
                if key not in keys:
                    keys.append(key)
        if keys:
            output[name] = keys[:24]
    return output


def _nearest_function(text: str, position: int) -> tuple[str | None, list[str]]:
    best_name: str | None = None
    best_params: list[str] = []
    for match in FUNC_RE.finditer(text, 0, position):
        best_name = match.group(1)
        best_params = [part.strip() for part in match.group(2).split(",") if part.strip()]
    return best_name, best_params


def expression_request_contracts(text: str, recognizer: Any) -> list[dict[str, Any]]:
    augmented, _decoded = _decoded_text(text)
    routes, evidence, _ = extract_expression_routes(text, recognizer)
    helper_keys = _function_param_object_keys(augmented)
    contracts: list[dict[str, Any]] = []
    for route in routes:
        meta = evidence.get(route) or {}
        pos = int(meta.get("position", -1))
        if pos >= 0:
            window = augmented[max(0, pos - 900):min(len(augmented), pos + 1800)]
        else:
            window = augmented
        method_match = METHOD_RE.search(window)
        method = method_match.group(1).upper() if method_match else ("POST" if str(meta.get("call") or "").casefold() == "postsearch" else "GET")
        body_fields: list[str] = []
        json_body = JSON_BODY_RE.search(window)
        if json_body:
            body_expr = json_body.group(1).strip()
            body_fields.extend(_object_keys(body_expr))
            if IDENT_RE.match(body_expr):
                fn_name, params = _nearest_function(augmented, pos)
                if fn_name and body_expr in params:
                    for key in helper_keys.get(fn_name, []):
                        if key not in body_fields:
                            body_fields.append(key)
        if not body_fields:
            body_match = BODY_RE.search(window)
            if body_match:
                value = body_match.group(1)
                for key in re.findall(r"(?:^|[&?])([A-Za-z_$][\w$-]{0,40})=", value):
                    low = key.casefold()
                    if low not in body_fields:
                        body_fields.append(low)
        response = "unknown"
        call = str(meta.get("call") or "")
        if call.casefold() == "fetchjson" or re.search(r"\.json\s*\(\)|JSON\.parse", window):
            response = "json"
        elif re.search(r"\.text\s*\(\)|cheerio\.load|DOMParser", window):
            response = "html-or-text"
        contracts.append({
            "route": route,
            "role": recognizer.route_kind(route),
            "method": method,
            "bodyFields": body_fields[:24],
            "formEncoded": bool(FORM_RE.search(window)),
            "jsonEncoded": bool(json_body or re.search(r"content-type['\"]?\s*:\s*['\"]application/json", window, re.I)),
            "refererRequired": bool(HEADER_REFERER_RE.search(window)),
            "originRequired": bool(HEADER_ORIGIN_RE.search(window)),
            "response": response,
            "executedEvidence": bool(meta.get("executedEvidence")),
            "call": call or None,
            "evidence": meta.get("evidence"),
            "confidence": meta.get("confidence"),
        })
    return contracts


def _merge_contracts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for row in rows:
        route = str(row.get("route") or "").strip()
        method = str(row.get("method") or "GET").upper()
        if not route:
            continue
        key = (route, method)
        if key not in merged:
            merged[key] = dict(row)
            order.append(key)
            continue
        target = merged[key]
        for field in ("bodyFields",):
            values = list(target.get(field) or [])
            for value in row.get(field) or []:
                if value not in values:
                    values.append(value)
            target[field] = values
        for field in ("formEncoded", "jsonEncoded", "refererRequired", "originRequired", "executedEvidence"):
            target[field] = bool(target.get(field) or row.get(field))
        if target.get("response") in (None, "unknown") and row.get("response") not in (None, "unknown"):
            target["response"] = row.get("response")
        if not target.get("call") and row.get("call"):
            target["call"] = row.get("call")
        target["confidence"] = max(float(target.get("confidence") or 0), float(row.get("confidence") or 0)) or None
        if not target.get("evidence") and row.get("evidence"):
            target["evidence"] = row.get("evidence")
    return [merged[key] for key in order][:128]


def install(recognizer: Any) -> None:
    """Install the analyzer into provider_contract_recognizer in-process.

    Kept as a small compatibility layer so the current reconstruction entry point
    can adopt richer route recognition without a risky monolithic rewrite.
    """
    if getattr(recognizer, "_NIAKVIO_ROUTE_ANALYZER_INSTALLED", False):
        return
    old_extract = recognizer.extract_routes
    old_contracts = recognizer.recognize_request_contracts
    old_family = recognizer.infer_family

    def enhanced_extract(text: str) -> list[str]:
        augmented, _ = _decoded_text(text)
        base = list(old_extract(augmented))
        extra, _evidence, _decoded = extract_expression_routes(text, recognizer)
        for route in extra:
            if route not in base and not recognizer.route_is_junk(route):
                base.append(route)
        return base[:192]

    def enhanced_contracts(text: str, routes: list[str] | None = None) -> list[dict[str, Any]]:
        augmented, _ = _decoded_text(text)
        selected = routes if isinstance(routes, list) else enhanced_extract(text)
        base = list(old_contracts(augmented, selected))
        extra = expression_request_contracts(text, recognizer)
        return _merge_contracts(base + extra)

    def enhanced_family(text: str, routes: list[str], contracts: list[dict[str, Any]] | None = None) -> str:
        augmented, _ = _decoded_text(text)
        return old_family(augmented, routes, contracts)

    recognizer.extract_routes = enhanced_extract
    recognizer.recognize_request_contracts = enhanced_contracts
    recognizer.infer_family = enhanced_family
    recognizer._NIAKVIO_ROUTE_ANALYZER_INSTALLED = True
