"""One-shot Core fixed-point bootstrap; removes itself after patching the checkout."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "core_rebuild_safety.py"
TEST = ROOT / "tests" / "core_terminal_export_floor_test.py"
SELF = Path(__file__).resolve()
TEMP_WORKFLOW = ROOT / ".github" / "workflows" / "core-runtime-domain-invocation-fix-once.yml"


def patch_core() -> None:
    text = CORE.read_text(encoding="utf-8")

    start = text.index("def _scan_runtime_domain_iife_end(")
    end = text.index("\n\ndef _runtime_domain_wrapper_span_from_key(", start)
    current = text[start:end]
    if "following invocation ``(global, rules)``" not in current:
        fixed = r'''def _scan_runtime_domain_iife_end(text: str, start: int) -> int | None:
    """Return the end of one complete invoked function expression.

    The first balanced parenthesis closes the ``(function(...) {...})``
    expression, not the IIFE statement. Ownership must also consume the
    following invocation ``(global, rules)``; otherwise every rebuild leaves
    that argument expression behind and appends another copy.
    """
    if start < 0 or start >= len(text) or text[start] != "(":
        return None

    def balanced_paren_end(open_index: int) -> int | None:
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

    expression_end = balanced_paren_end(start)
    if expression_end is None:
        return None
    call_start = expression_end
    while call_start < len(text) and text[call_start] in " \t\r\n":
        call_start += 1
    if call_start >= len(text) or text[call_start] != "(":
        return None
    end = balanced_paren_end(call_start)
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
        text = text[:start] + fixed + text[end:]

    if "def _strip_runtime_domain_orphan_calls(" not in text:
        anchor = "\n\ndef _inject_runtime_domain_overrides("
        if anchor not in text:
            raise RuntimeError("runtime-domain injection anchor missing")
        helper = r'''

def _strip_runtime_domain_orphan_calls(
    text: str,
    insertion: int | None,
    payload: str,
) -> tuple[str, int]:
    """Remove only exact generated call-argument tails left by the old IIFE scanner.

    Historical builds sometimes removed ``(function(...) {...})`` but left its
    immediately-following ``(global, rules);`` invocation behind. Terser may
    also drop the redundant outer parentheses. Only the exact current encoded
    rules payload at the proven wrapper insertion point is owned here; unrelated
    provider expressions and different rule payloads remain untouched.
    """
    if insertion is None:
        return text, 0
    head = text[:insertion]
    tail = text[insertion:]
    variants = (
        f'(typeof globalThis!=="undefined"?globalThis:this,{payload});',
        f'typeof globalThis!=="undefined"?globalThis:this,{payload};',
    )
    removed = 0
    while True:
        whitespace_end = 0
        while whitespace_end < len(tail) and tail[whitespace_end] in " \t\r\n":
            whitespace_end += 1
        candidate = tail[whitespace_end:]
        matched = next((value for value in variants if candidate.startswith(value)), None)
        if matched is None:
            break
        tail = candidate[len(matched):]
        removed += 1
    if removed == 0:
        return text, 0
    return head + tail, removed
'''
        text = text.replace(anchor, helper + anchor, 1)

    payload_anchor = '    payload = json.dumps(encoded_rules, separators=(",", ":"))\n'
    cleanup_line = "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, insertion, payload)\n"
    if cleanup_line not in text:
        if payload_anchor not in text:
            raise RuntimeError("runtime-domain payload anchor missing")
        text = text.replace(payload_anchor, payload_anchor + cleanup_line, 1)

    old_condition = "    if existing_span is not None and marker_comment in text[existing_span[0]:existing_span[1]]:\n"
    new_condition = "    if existing_span is not None and orphan_count == 0 and marker_comment in text[existing_span[0]:existing_span[1]]:\n"
    if new_condition not in text:
        if old_condition not in text:
            raise RuntimeError("runtime-domain existing-span anchor missing")
        text = text.replace(old_condition, new_condition, 1)

    CORE.write_text(text, encoding="utf-8")


def patch_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    if "def test_runtime_domain_iife_ownership_consumes_call_arguments()" not in text:
        anchor = "def test_runtime_domain_duplicate_bootstraps_collapse_fail_closed() -> None:\n"
        if anchor not in text:
            raise RuntimeError("runtime-domain regression anchor missing")
        regression = '''def test_runtime_domain_iife_ownership_consumes_call_arguments() -> None:\n    rules = {"old.example": "new.example"}\n    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\\n"\n    canonical, _ = inject_domain_overrides(provider, rules)\n    repeated, _ = inject_domain_overrides(canonical, rules)\n    assert repeated == canonical\n\n    markerless = canonical.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\\n", "", 1)\n    rebuilt, _ = inject_domain_overrides(markerless, rules)\n    assert rebuilt == canonical\n    invocation = '})(typeof globalThis!=="undefined"?globalThis:this,'\n    assert rebuilt.count(invocation) == 1\n\n\n'''
        text = text.replace(anchor, regression + anchor, 1)

    if "def test_runtime_domain_orphan_invocations_collapse_fail_closed()" not in text:
        anchor = "def test_runtime_domain_duplicate_bootstraps_collapse_fail_closed() -> None:\n"
        if anchor not in text:
            raise RuntimeError("runtime-domain orphan regression anchor missing")
        regression = '''def test_runtime_domain_orphan_invocations_collapse_fail_closed() -> None:\n    rules = {"old.example": "new.example"}\n    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\\n"\n    canonical, _ = inject_domain_overrides(provider, rules)\n    provider_start = canonical.index(provider)\n    call_start = canonical.index('(typeof globalThis!=="undefined"?globalThis:this,')\n    call_end = canonical.index(";", call_start) + 1\n    orphan = canonical[call_start:call_end]\n    terser_orphan = orphan[1:-1] + ";"\n\n    damaged = canonical[:provider_start] + orphan + terser_orphan + canonical[provider_start:]\n    repaired, _ = inject_domain_overrides(damaged, rules)\n    assert repaired == canonical\n\n    markerless = damaged.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\\n", "", 1)\n    repaired_markerless, _ = inject_domain_overrides(markerless, rules)\n    assert repaired_markerless == canonical\n\n    foreign = terser_orphan.replace("new.example", "foreign.example")\n    foreign_input = canonical[:provider_start] + foreign + canonical[provider_start:]\n    foreign_output, _ = inject_domain_overrides(foreign_input, rules)\n    assert foreign in foreign_output\n    assert foreign_output.count("__nuvioDomainOverrideV1") == 1\n\n\n'''
        text = text.replace(anchor, regression + anchor, 1)

    calls = (
        "    test_runtime_domain_iife_ownership_consumes_call_arguments()\n",
        "    test_runtime_domain_orphan_invocations_collapse_fail_closed()\n",
    )
    anchor = "    test_runtime_domain_duplicate_bootstraps_collapse_fail_closed()\n"
    if anchor not in text:
        raise RuntimeError("runtime-domain regression call anchor missing")
    for call in reversed(calls):
        if call not in text:
            text = text.replace(anchor, call + anchor, 1)

    TEST.write_text(text, encoding="utf-8")


try:
    patch_core()
    patch_test()
    if TEMP_WORKFLOW.exists():
        TEMP_WORKFLOW.unlink()
finally:
    # The checkout keeps only the durable source + regression changes. The Core
    # publication step will therefore remove this bootstrap from main as well.
    if SELF.exists():
        SELF.unlink()
