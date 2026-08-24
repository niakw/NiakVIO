"""One-shot Core fixed-point bootstrap; removes itself after patching the checkout."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "core_rebuild_safety.py"
TEST = ROOT / "tests" / "core_terminal_export_floor_test.py"
SELF = Path(__file__).resolve()
TEMP_WORKFLOW = ROOT / ".github" / "workflows" / "core-runtime-domain-invocation-fix-once.yml"


SCANNER = r'''def _scan_runtime_domain_iife_end(text: str, start: int) -> int | None:
    """Return the end of one complete invoked function expression.

    The first balanced parenthesis closes only ``(function(...) {...})``.
    Ownership is valid only when the immediately-following invocation is also
    balanced and consumed. This prevents leaving ``(global, rules)`` tails.
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


ORPHAN_HELPER = r'''
def _strip_runtime_domain_orphan_calls(
    text: str,
    insertion: int | None,
    rules: dict[str, str],
) -> tuple[str, int]:
    """Remove only historical generated call tails owned by current domain rules.

    Old builds could delete the function-expression half of the bootstrap while
    retaining its invocation arguments. Terser may additionally remove the outer
    parentheses. A tail is removable only at the proven bootstrap insertion point
    and only if every decoded ``oldHost -> newHost`` pair is still authorized by
    the current normalized rule map. Foreign targets fail closed and remain bytes.
    """
    if insertion is None or not rules:
        return text, 0

    import base64
    import json

    head = text[:insertion]
    tail = text[insertion:]
    prefixes = (
        ('(typeof globalThis!=="undefined"?globalThis:this,', ');'),
        ('typeof globalThis!=="undefined"?globalThis:this,', ';'),
    )
    decoder = json.JSONDecoder()
    removed = 0

    while True:
        whitespace_end = 0
        while whitespace_end < len(tail) and tail[whitespace_end] in " \t\r\n":
            whitespace_end += 1
        candidate = tail[whitespace_end:]
        matched = False

        for prefix, suffix in prefixes:
            if not candidate.startswith(prefix):
                continue
            payload_text = candidate[len(prefix):]
            try:
                payload, payload_end = decoder.raw_decode(payload_text)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if not isinstance(payload, list) or not payload:
                continue

            authorized = True
            for row in payload:
                if not isinstance(row, list) or len(row) != 2:
                    authorized = False
                    break
                encoded_old, new_host = row
                if not isinstance(encoded_old, str) or not isinstance(new_host, str):
                    authorized = False
                    break
                try:
                    old_host = base64.b64decode(encoded_old, validate=True).decode("utf-8").lower().strip().rstrip("/")
                except Exception:
                    authorized = False
                    break
                normalized_new = new_host.lower().strip().rstrip("/")
                if rules.get(old_host) != normalized_new:
                    authorized = False
                    break
            if not authorized:
                continue

            after_payload = payload_text[payload_end:]
            if not after_payload.startswith(suffix):
                continue
            consumed = len(prefix) + payload_end + len(suffix)
            tail = candidate[consumed:]
            removed += 1
            matched = True
            break

        if not matched:
            break

    if removed == 0:
        return text, 0
    return head + tail, removed
'''.lstrip("\n")


def patch_core() -> None:
    text = CORE.read_text(encoding="utf-8")

    start = text.index("def _scan_runtime_domain_iife_end(")
    end = text.index("\n\ndef _runtime_domain_wrapper_span_from_key(", start)
    text = text[:start] + SCANNER + text[end:]

    helper_start = text.find("def _strip_runtime_domain_orphan_calls(")
    inject_anchor = "\n\ndef _inject_runtime_domain_overrides("
    if inject_anchor not in text:
        raise RuntimeError("runtime-domain injection anchor missing")
    if helper_start >= 0:
        helper_end = text.index(inject_anchor, helper_start)
        text = text[:helper_start] + ORPHAN_HELPER + text[helper_end:]
    else:
        text = text.replace(inject_anchor, "\n\n" + ORPHAN_HELPER + inject_anchor, 1)

    old_cleanup = "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, insertion, payload)\n"
    new_cleanup = "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, insertion, rules)\n"
    if old_cleanup in text:
        text = text.replace(old_cleanup, new_cleanup, 1)
    elif new_cleanup not in text:
        payload_anchor = '    payload = json.dumps(encoded_rules, separators=(",", ":"))\n'
        if payload_anchor not in text:
            raise RuntimeError("runtime-domain payload anchor missing")
        text = text.replace(payload_anchor, payload_anchor + new_cleanup, 1)

    old_condition = "    if existing_span is not None and marker_comment in text[existing_span[0]:existing_span[1]]:\n"
    new_condition = "    if existing_span is not None and orphan_count == 0 and marker_comment in text[existing_span[0]:existing_span[1]]:\n"
    if old_condition in text:
        text = text.replace(old_condition, new_condition, 1)
    elif new_condition not in text:
        raise RuntimeError("runtime-domain existing-span anchor missing")

    CORE.write_text(text, encoding="utf-8")


def patch_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    name = "test_runtime_domain_historical_orphan_subsets_collapse_fail_closed"
    if f"def {name}()" not in text:
        anchor = "def test_runtime_domain_duplicate_bootstraps_collapse_fail_closed() -> None:\n"
        if anchor not in text:
            raise RuntimeError("runtime-domain regression anchor missing")
        regression = '''def test_runtime_domain_historical_orphan_subsets_collapse_fail_closed() -> None:\n    rules = {"old.example": "new.example", "older.example": "new.example"}\n    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\\n"\n    canonical, _ = inject_domain_overrides(provider, rules)\n    repeated, _ = inject_domain_overrides(canonical, rules)\n    assert repeated == canonical\n\n    import base64, json\n    subset = [[base64.b64encode(b"old.example").decode("ascii"), "new.example"]]\n    subset_payload = json.dumps(subset, separators=(",", ":"))\n    provider_start = canonical.index(provider)\n    orphan = f'typeof globalThis!=="undefined"?globalThis:this,{subset_payload};'\n    damaged = canonical[:provider_start] + orphan + orphan + canonical[provider_start:]\n    repaired, _ = inject_domain_overrides(damaged, rules)\n    assert repaired == canonical\n\n    foreign = orphan.replace("new.example", "foreign.example")\n    foreign_input = canonical[:provider_start] + foreign + canonical[provider_start:]\n    foreign_output, _ = inject_domain_overrides(foreign_input, rules)\n    assert foreign in foreign_output\n    assert foreign_output.count("__nuvioDomainOverrideV1") == 1\n\n\n'''
        text = text.replace(anchor, regression + anchor, 1)

    call = f"    {name}()\n"
    anchor = "    test_runtime_domain_duplicate_bootstraps_collapse_fail_closed()\n"
    if call not in text:
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
    # Only durable Core/test changes survive in the runner checkout. A successful
    # Core publication therefore deletes this bootstrap and its temporary workflow.
    if SELF.exists():
        SELF.unlink()
