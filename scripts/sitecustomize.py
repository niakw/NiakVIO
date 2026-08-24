"""One-shot durable Core fixed-point repair loaded from the scripts Python path.

This is intentionally tiny and self-deleting.  It patches the durable
``core_rebuild_safety.py`` source before any Core normalizer can regenerate
``apply_provider_overrides.py`` from the stale template.  The published Core
commit keeps only the durable source/test changes; this bootstrap and the
obsolete root shim/workflow are removed from the runner checkout.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "core_rebuild_safety.py"
TEST = ROOT / "tests" / "core_terminal_export_floor_test.py"
SELF = Path(__file__).resolve()
ROOT_SHIM = ROOT / "sitecustomize.py"
TEMP_WORKFLOW = ROOT / ".github" / "workflows" / "core-runtime-domain-invocation-fix-once.yml"


SCANNER = r'''def _scan_runtime_domain_iife_end(text: str, start: int) -> int | None:
    """Return the end of a complete ``(function(){...})(args)`` statement.

    Balancing only the first parenthesized function expression leaves the
    invocation arguments behind.  Those historical tails were the source of
    the +bytes/pass provider fixed-point drift, so ownership is valid only when
    both the function expression and its immediately-following call are fully
    balanced and consumed.
    """
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
    return end'''


ORPHAN_HELPER = r'''def _strip_runtime_domain_orphan_calls(
    text: str,
    rules: dict[str, str],
) -> tuple[str, int]:
    """Remove only standalone historical invocation tails authorized by rules."""
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
                old_host = (
                    base64.b64decode(encoded_old, validate=True)
                    .decode("utf-8")
                    .lower()
                    .strip()
                    .rstrip("/")
                )
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
        except (TypeError, ValueError, json.JSONDecodeError):
            payload, payload_end = None, 0

        match: tuple[int, int] | None = None
        if authorized(payload):
            remainder = tail[payload_end:]
            for start, suffix in candidates:
                if not remainder.startswith(suffix):
                    continue
                end = position + len(needle) + payload_end + len(suffix)
                # Consume only harmless horizontal whitespace/newline after the
                # orphan statement; never cross into provider-owned bytes.
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
    return "".join(output), removed'''


def patch_core() -> None:
    text = CORE.read_text(encoding="utf-8")

    scanner_start = text.index("def _scan_runtime_domain_iife_end(")
    scanner_end = text.index("\n\ndef _runtime_domain_wrapper_span_from_key(", scanner_start)
    text = text[:scanner_start] + SCANNER + text[scanner_end:]

    inject_anchor = "\n\ndef _inject_runtime_domain_overrides("
    helper_start = text.find("def _strip_runtime_domain_orphan_calls(")
    if helper_start >= 0:
        helper_end = text.index(inject_anchor, helper_start)
        text = text[:helper_start] + ORPHAN_HELPER + text[helper_end:]
    else:
        text = text.replace(inject_anchor, "\n\n" + ORPHAN_HELPER + inject_anchor, 1)

    old_order = '''    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"\n    marker_comment = f"/* {marker} */"\n    spans = _runtime_domain_wrapper_spans(text)\n'''
    new_order = '''    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"\n    marker_comment = f"/* {marker} */"\n    # Historical invocation-only debris must be removed before span discovery.\n    # Otherwise deleting a prefix orphan after computing spans shifts the\n    # canonical insertion coordinate and creates another bytes-per-pass drift.\n    text, orphan_count = _strip_runtime_domain_orphan_calls(text, rules)\n    spans = _runtime_domain_wrapper_spans(text)\n'''
    if old_order in text:
        text = text.replace(old_order, new_order, 1)
    elif new_order not in text:
        raise RuntimeError("runtime-domain ordering anchor missing")

    for stale in (
        "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, rules)\n",
        "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, insertion, rules)\n",
        "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, insertion, payload)\n",
    ):
        text = text.replace(stale, "")

    text = text.replace(
        "    if existing_span is not None and orphan_count == 0 and marker_comment in text[existing_span[0]:existing_span[1]]:\n",
        "    if existing_span is not None and marker_comment in text[existing_span[0]:existing_span[1]]:\n",
    )

    if text.count("def _strip_runtime_domain_orphan_calls(") != 1:
        raise RuntimeError("runtime-domain orphan cleaner must exist exactly once")
    if text.count("_strip_runtime_domain_orphan_calls(text, rules)") != 1:
        raise RuntimeError("runtime-domain orphan cleaner must run exactly once before span discovery")
    if "_strip_runtime_domain_orphan_calls(base" in text:
        raise RuntimeError("post-span runtime-domain cleanup remains")

    CORE.write_text(text, encoding="utf-8")


def patch_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    name = "test_runtime_domain_orphan_order_is_byte_stable"
    if f"def {name}()" not in text:
        anchor = "def test_runtime_domain_duplicate_bootstraps_collapse_fail_closed() -> None:\n"
        if anchor not in text:
            raise RuntimeError("runtime-domain regression anchor missing")
        regression = '''def test_runtime_domain_orphan_order_is_byte_stable() -> None:\n    import base64\n\n    rules = {"old.example": "new.example", "older.example": "new.example"}\n    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\\n"\n    canonical, _ = inject_domain_overrides(provider, rules)\n    for _ in range(6):\n        repeated, _ = inject_domain_overrides(canonical, rules)\n        assert repeated == canonical\n\n    payload = json.dumps(\n        [[base64.b64encode(b"old.example").decode("ascii"), "new.example"]],\n        separators=(",", ":"),\n    )\n    plain = f'typeof globalThis!=="undefined"?globalThis:this,{payload};'\n    wrapped = f'(typeof globalThis!=="undefined"?globalThis:this,{payload});'\n    for damaged in (plain + canonical, wrapped + canonical, plain + wrapped + canonical):\n        repaired, _ = inject_domain_overrides(damaged, rules)\n        assert repaired == canonical\n\n    markerless = canonical.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\\n", "", 1)\n    repaired, _ = inject_domain_overrides(markerless, rules)\n    assert repaired == canonical\n\n    foreign = plain.replace("new.example", "foreign.example")\n    foreign_output, _ = inject_domain_overrides(foreign + canonical, rules)\n    assert foreign in foreign_output\n    assert foreign_output.count("__nuvioDomainOverrideV1") == 1\n\n\n'''
        text = text.replace(anchor, regression + anchor, 1)

    call = f"    {name}()\n"
    call_anchor = "    test_runtime_domain_duplicate_bootstraps_collapse_fail_closed()\n"
    if call not in text:
        if call_anchor not in text:
            raise RuntimeError("runtime-domain test runner anchor missing")
        text = text.replace(call_anchor, call + call_anchor, 1)

    TEST.write_text(text, encoding="utf-8")


try:
    patch_core()
    patch_test()
finally:
    for path in (ROOT_SHIM, TEMP_WORKFLOW, SELF):
        if path.exists():
            path.unlink()
