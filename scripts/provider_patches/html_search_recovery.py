"""Provider-agnostic search-first recovery for DLE-like HTML bundles.

The runtime repair loop applies this only after observing the generic failure
signature: a successful provider search followed by obsolete fallback routes
and zero streams. Applicability is then confirmed from structural capabilities
inside the bundle; no provider id or domain is referenced here.
"""
from __future__ import annotations

import re
from typing import Any

_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*$")


def _ident(options: dict[str, Any], key: str) -> str:
    value = str(options.get(key) or "").strip()
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"html_search_recovery: invalid identifier for {key}: {value!r}")
    return value


def _find_matching(source: str, open_pos: int, opener: str, closer: str) -> int:
    """Find a balanced JavaScript delimiter while skipping strings/comments/regex."""
    depth = 0
    i = open_pos
    state = "code"
    quote = ""
    escaped = False
    regex_class = False
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "line_comment":
            if ch in "\r\n":
                state = "code"
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 1
        elif state == "string":
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                state = "code"
        elif state == "template":
            # Template-literal braces belong to the literal/interpolation and
            # must not alter the delimiter depth of the surrounding function.
            # Counting them here caused the matcher to consume code following
            # a minified function and produced syntactically broken bundles.
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "`":
                state = "code"
        elif state == "regex":
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "[":
                regex_class = True
            elif ch == "]":
                regex_class = False
            elif ch == "/" and not regex_class:
                state = "code"
        else:
            if ch == "/" and nxt == "/":
                state = "line_comment"
                i += 1
            elif ch == "/" and nxt == "*":
                state = "block_comment"
                i += 1
            elif ch in "'\"":
                state = "string"
                quote = ch
            elif ch == "`":
                state = "template"
            elif ch == "/":
                previous = source[i - 1] if i else ""
                if previous in "=(:,![{;?&|+*-~%^<>" or not previous:
                    state = "regex"
                    regex_class = False
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError("html_search_recovery: unterminated JavaScript delimiter")


def _replace_function(source: str, name: str, replacement: str) -> str:
    marker = f"function {name}("
    start = source.find(marker)
    if start < 0:
        raise ValueError(f"html_search_recovery: function {name} not found")
    params_open = source.find("(", start + len("function ") + len(name))
    if params_open < 0:
        raise ValueError(f"html_search_recovery: parameters for {name} not found")
    params_close = _find_matching(source, params_open, "(", ")")
    body_open = source.find("{", params_close)
    if body_open < 0:
        raise ValueError(f"html_search_recovery: body for {name} not found")
    body_close = _find_matching(source, body_open, "{", "}")
    return source[:start] + replacement + source[body_close + 1 :]


def apply(
    source: str,
    *,
    options: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    options = dict(options or {})
    detect_all = [str(v) for v in options.get("detect_all", [])]
    detect_any = [str(v) for v in options.get("detect_any", [])]
    if detect_all and not all(marker in source for marker in detect_all):
        return source
    if detect_any and not any(marker in source for marker in detect_any):
        return source

    parser_fn = _ident(options, "parser_function")
    movie_fn = _ident(options, "movie_lookup_function")
    cheerio = _ident(options, "cheerio_loader")
    normalize = _ident(options, "normalize_url")
    extract_id = _ident(options, "extract_id")
    is_series = _ident(options, "is_series")
    query_builder = _ident(options, "query_builder")
    search_request = _ident(options, "search_request")
    fetch_players = _ident(options, "fetch_players")
    resolve_streams = _ident(options, "resolve_streams")
    async_helper = _ident(options, "async_helper")
    marker = str(
        options.get("success_marker")
        or "[Nuvio Runtime Repair] Content found via HTML search"
    )
    minimum_score = max(0, int(options.get("minimum_score", 40)))
    max_candidates = max(1, min(20, int(options.get("max_candidates", 6))))

    parser_name = "__nuvioHtmlSearchParse"
    lookup_name = "__nuvioHtmlMovieLookup"
    if parser_name in source or lookup_name in source:
        return source

    parser = rf'''function {parser_name}(t,n){{let i={cheerio}(t),s=[],a=new Set,c=(f,g,h)=>{{let _={normalize}(f,n);if(!_||a.has(_))return;let m=(g||"").replace(/\s+/g," ").trim();if(!m)return;let A={extract_id}(h||"",f)||((_.match(/(?:id=|\/)(\d{{2,}})(?:[-_/?\.]|$)/i)||[])[1]||"");if(!A)return;a.add(_),s.push({{newsId:String(A),href:_,title:m,isSeries:{is_series}(null,_,m),baseUrl:n}})}};let f=[".short",".short-in","article",".movie-item",".film-item",".item",".poster",".card","[data-id]"];for(let g of f)i(g).each((h,_)=>{{let m=i(_),A=m.find("a[href]").first(),D=A.attr("href")||m.attr("href")||"",T=(m.find(".short-title,.title,.name,h2,h3,h4").first().text()||A.attr("title")||m.find("img").first().attr("alt")||A.text()||"").trim(),x=m.find(".info-button,[onclick]").first().attr("onclick")||A.attr("onclick")||"",C=m.find("[data-id]").first().attr("data-id")||m.attr("data-id")||A.attr("data-id")||"";c(D,T,x||C)}});if(s.length===0)i("a[href]").each((g,h)=>{{let _=i(h),m=_.attr("href")||"",A=(_.attr("title")||_.find("img").attr("alt")||_.text()||"").trim(),D=_.attr("onclick")||_.attr("data-id")||"";A.length>=2&&c(m,A,D)}});return s}}'''

    lookup = f'''function {lookup_name}(t,n,i){{return {async_helper}(this,null,function*(){{let s={query_builder}(n),a=new Set;for(let c of s)try{{let f=yield {search_request}(c,"movie");for(let g of f.slice(0,{max_candidates})){{if(a.has(g.newsId))continue;a.add(g.newsId);if((g._score||0)<{minimum_score})continue;let h=yield {fetch_players}(g.newsId,t,i);if(h&&h.length>0){{let _=yield {resolve_streams}(h);if(_.length>0)return console.log({marker!r}+": "+g.title+" → "+_.length+" streams"),_}}}}}}catch(f){{console.warn(`[Nuvio Runtime Repair] search query failed: ${{f==null?void 0:f.message}}`)}}return[]}})}}'''

    # Do not replace whole minified functions: textual delimiter matching is too
    # fragile around template literals and regular expressions. Inject helpers
    # and redirect only the two observed call sites.
    parser_call = re.compile(rf"\.then\(([$A-Za-z_][\w$]*)=>{re.escape(parser_fn)}\(\1,([$A-Za-z_][\w$]*)\)\)")
    source, parser_count = parser_call.subn(
        lambda match: f".then({match.group(1)}=>{parser_name}({match.group(1)},{match.group(2)}))",
        source,
    )
    lookup_call = re.compile(rf"\byield\s+{re.escape(movie_fn)}\(")
    source, lookup_count = lookup_call.subn(f"yield {lookup_name}(", source)
    if parser_count == 0 or lookup_count == 0:
        raise ValueError(
            f"html_search_recovery: call-site redirection failed "
            f"(parser={parser_count}, lookup={lookup_count})"
        )
    anchor = f"function {movie_fn}("
    position = source.find(anchor)
    if position < 0:
        raise ValueError(f"html_search_recovery: injection anchor {movie_fn} not found")
    source = source[:position] + parser + lookup + source[position:]
    return source
