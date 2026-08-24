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
    if "following invocation ``(global, rules)``" in current:
        return
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
    CORE.write_text(text[:start] + fixed + text[end:], encoding="utf-8")


def patch_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    if "def test_runtime_domain_iife_ownership_consumes_call_arguments()" not in text:
        anchor = "def test_runtime_domain_duplicate_bootstraps_collapse_fail_closed() -> None:\n"
        if anchor not in text:
            raise RuntimeError("runtime-domain regression anchor missing")
        regression = '''def test_runtime_domain_iife_ownership_consumes_call_arguments() -> None:\n    rules = {"old.example": "new.example"}\n    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\\n"\n    canonical, _ = inject_domain_overrides(provider, rules)\n    repeated, _ = inject_domain_overrides(canonical, rules)\n    assert repeated == canonical\n\n    markerless = canonical.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\\n", "", 1)\n    rebuilt, _ = inject_domain_overrides(markerless, rules)\n    assert rebuilt == canonical\n    invocation = '})(typeof globalThis!=="undefined"?globalThis:this,'\n    assert rebuilt.count(invocation) == 1\n\n\n'''
        text = text.replace(anchor, regression + anchor, 1)
    call = "    test_runtime_domain_iife_ownership_consumes_call_arguments()\n"
    if call not in text:
        anchor = "    test_runtime_domain_duplicate_bootstraps_collapse_fail_closed()\n"
        if anchor not in text:
            raise RuntimeError("runtime-domain regression call anchor missing")
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
