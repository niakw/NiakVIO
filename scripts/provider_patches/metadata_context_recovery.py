"""Recover fixture metadata through generic bundled-provider wrappers.

This profile is selected only after a deep run observes a metadata-only lookup
with no request to a provider-owned host. It repairs two structural patterns
without referring to any provider id, domain, or minified function name:

1. a wrapper accepts a fifth settings/context argument but forwards only a
   newly-created ``{signal: ...}`` object to the scraper;
2. the scraper aborts when its title aggregation is empty instead of using the
   title already supplied by the fixture context.
"""
from __future__ import annotations

import re
from typing import Any

_IDENTIFIER = r"[A-Za-z_$][A-Za-z0-9_$]*"
_MARKER = "[Nuvio Runtime Repair] Using fixture title metadata"


def _patch_context_passthrough(source: str) -> tuple[str, int]:
    count = 0
    # Match generator wrappers with at least five positional parameters, where
    # the fifth one is the settings/context object. Restrict replacements to the
    # body of that generator so unrelated {signal:...} calls are untouched.
    generator = re.compile(
        rf"function\*\(\s*(?P<p1>{_IDENTIFIER})\s*,\s*(?P<p2>{_IDENTIFIER})\s*,"
        rf"\s*(?P<p3>{_IDENTIFIER})\s*,\s*(?P<p4>{_IDENTIFIER})\s*,"
        rf"\s*(?P<context>{_IDENTIFIER})\s*=\s*\{{\}}\s*\)\s*\{{"
    )
    cursor = 0
    pieces: list[str] = []
    while True:
        match = generator.search(source, cursor)
        if not match:
            pieces.append(source[cursor:])
            break
        pieces.append(source[cursor : match.end()])
        # Bundles used here put the wrapper body before the next `function` or
        # module initializer. Limiting the window keeps the substitution local;
        # the runtime smoke test rejects any malformed result.
        next_function = source.find("function ", match.end())
        window_end = next_function if next_function >= 0 else min(len(source), match.end() + 12000)
        body = source[match.end() : window_end]
        p1, p2, p3, p4, context = (match.group(key) for key in ("p1", "p2", "p3", "p4", "context"))
        call = re.compile(
            rf"(?P<callee>{_IDENTIFIER})\(\s*{re.escape(p1)}\s*,\s*{re.escape(p2)}\s*,"
            rf"\s*{re.escape(p3)}\s*,\s*{re.escape(p4)}\s*,\s*\{{\s*signal\s*:"
            rf"\s*(?P<signal>{_IDENTIFIER})\s*\}}\s*\)"
        )

        def replace_call(call_match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return (
                f"{call_match.group('callee')}({p1},{p2},{p3},{p4},"
                f"Object.assign({{}},{context}||{{}},{{signal:{call_match.group('signal')}}}))"
            )

        patched_body = call.sub(replace_call, body, count=1)
        pieces.append(patched_body)
        cursor = window_end
    return "".join(pieces), count


def _patch_title_fallback(source: str) -> tuple[str, int]:
    if _MARKER in source:
        return source, 0
    count = 0
    generator = re.compile(
        rf"function\*\(\s*(?P<id>{_IDENTIFIER})\s*,\s*(?P<kind>{_IDENTIFIER})\s*,"
        rf"\s*(?P<season>{_IDENTIFIER})\s*,\s*(?P<episode>{_IDENTIFIER})\s*,"
        rf"\s*(?P<context>{_IDENTIFIER})\s*=\s*\{{\}}\s*\)\s*\{{"
    )
    cursor = 0
    pieces: list[str] = []
    while True:
        match = generator.search(source, cursor)
        if not match:
            pieces.append(source[cursor:])
            break
        pieces.append(source[cursor : match.end()])
        next_function = source.find("function ", match.end())
        window_end = next_function if next_function >= 0 else min(len(source), match.end() + 20000)
        body = source[match.end() : window_end]
        context = match.group("context")
        season = match.group("season")
        # The variable checked for emptiness must have been assigned from an
        # awaited call using the current id/type and season shortly beforehand.
        empty_check = re.compile(
            rf"if\s*\(\s*!\s*(?P<titles>{_IDENTIFIER})\s*\|\|\s*(?P=titles)\.length\s*===\s*0\s*\)\s*return\s*\[\s*\]\s*;"
        )
        selected: re.Match[str] | None = None
        for candidate in empty_check.finditer(body):
            titles = candidate.group("titles")
            prefix = body[max(0, candidate.start() - 600) : candidate.start()]
            if re.search(
                rf"{re.escape(titles)}\s*=\s*yield\s+{_IDENTIFIER}\([^;]{{0,300}}season\s*:\s*{re.escape(season)}[^;]{{0,100}}\)",
                prefix,
            ):
                selected = candidate
                break
        if selected is None:
            pieces.append(body)
            cursor = window_end
            continue
        titles = selected.group("titles")
        fallback = (
            f"if(!{titles}||{titles}.length===0){{"
            f"let __nuvioFixtureTitle=({context}&&(({context}.title||{context}.label)||{context}.fixtureTitle)||\"\")"
            f".replace(/\\s*\\(\\d{{4}}\\)\\s*$/,\"\").trim();"
            f"if(!__nuvioFixtureTitle)return[];"
            f"{titles}=[__nuvioFixtureTitle],{titles}.effectiveSeason={season},"
            f"console.log(\"{_MARKER}: \"+__nuvioFixtureTitle)}}"
        )
        body = body[: selected.start()] + fallback + body[selected.end() :]
        count += 1
        pieces.append(body)
        cursor = window_end
    return "".join(pieces), count


def apply(
    source: str,
    *,
    options: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    options = dict(options or {})
    detect_all = [str(value) for value in options.get("detect_all") or []]
    detect_any = [str(value) for value in options.get("detect_any") or []]
    if detect_all and not all(marker in source for marker in detect_all):
        return source
    if detect_any and not any(marker in source for marker in detect_any):
        return source

    patched, context_count = _patch_context_passthrough(source)
    patched, title_count = _patch_title_fallback(patched)
    if context_count == 0 and title_count == 0:
        return source
    return patched
