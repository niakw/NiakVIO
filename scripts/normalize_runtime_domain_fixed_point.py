#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize and verify byte-stable runtime-domain bootstrap ownership."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from textwrap import dedent
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "scripts" / "core_rebuild_safety.py"

SCANNER = dedent(r'''
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
''').lstrip("\n")

RUNTIME_HELPERS = dedent(r'''
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
    except (TypeError, ValueError, json.JSONDecodeError):
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
        except (TypeError, ValueError, json.JSONDecodeError):
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
''').lstrip("\n")


def normalized(text: str) -> str:
    scanner_start = text.index("def _scan_runtime_domain_iife_end(")
    scanner_end = text.index("\n\ndef _runtime_domain_wrapper_span_from_key(", scanner_start)
    text = text[:scanner_start] + SCANNER + text[scanner_end:]

    inject_anchor = "\n\ndef _inject_runtime_domain_overrides("
    helper_starts = [
        position
        for marker in (
            "def _runtime_domain_expected_payload(",
            "def _runtime_domain_span_matches_rules(",
            "def _strip_runtime_domain_orphan_calls(",
        )
        if (position := text.find(marker)) >= 0
    ]
    if helper_starts:
        helper_start = min(helper_starts)
        helper_end = text.index(inject_anchor, helper_start)
        text = text[:helper_start] + RUNTIME_HELPERS + text[helper_end:]
    else:
        text = text.replace(inject_anchor, "\n\n" + RUNTIME_HELPERS + inject_anchor, 1)

    old = '''    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"\n    marker_comment = f"/* {marker} */"\n    spans = _runtime_domain_wrapper_spans(text)\n'''
    new = '''    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"\n    marker_comment = f"/* {marker} */"\n    text, orphan_count = _strip_runtime_domain_orphan_calls(text, rules)\n    spans = _runtime_domain_wrapper_spans(text)\n    existing_span = spans[0] if len(spans) == 1 else None\n    if rules and existing_span is not None:\n        candidate = text[existing_span[0]:existing_span[1]]\n        if _runtime_domain_span_matches_rules(candidate, rules):\n            return text, 0 if text == original_text else max(1, orphan_count)\n'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        previous = '''    marker = "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1"\n    marker_comment = f"/* {marker} */"\n    text, orphan_count = _strip_runtime_domain_orphan_calls(text, rules)\n    spans = _runtime_domain_wrapper_spans(text)\n'''
        if previous not in text:
            raise ValueError("runtime-domain span-discovery anchor missing")
        text = text.replace(previous, new, 1)

    stale_existing_re = re.compile(
        r"\n    existing_span = spans\[0\] if len\(spans\) == 1 else None\n"
        r"    if existing_span is not None and marker_comment in text\[existing_span\[0\]:existing_span\[1\]\]:\n"
        r"        output = text\[:existing_span\[0\]\] \+ bootstrap \+ text\[existing_span\[1\]:\]\n"
        r"        return output, 0 if output == original_text else len\(rules\)\n"
    )
    text = stale_existing_re.sub("", text, count=1)

    for stale in (
        "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, rules)\n",
        "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, insertion, rules)\n",
        "    base, orphan_count = _strip_runtime_domain_orphan_calls(base, insertion, payload)\n",
    ):
        text = text.replace(stale, "")

    if text.count("def _runtime_domain_expected_payload(") != 1:
        raise ValueError("runtime-domain expected payload helper must exist exactly once")
    if text.count("def _runtime_domain_span_matches_rules(") != 1:
        raise ValueError("runtime-domain span matcher must exist exactly once")
    if text.count("def _strip_runtime_domain_orphan_calls(") != 1:
        raise ValueError("runtime-domain orphan cleaner must exist exactly once")
    if text.count("_strip_runtime_domain_orphan_calls(text, rules)") != 1:
        raise ValueError("runtime-domain orphan cleaner must run once before span discovery")
    if text.count("_runtime_domain_span_matches_rules(candidate, rules)") != 1:
        raise ValueError("runtime-domain markerless fixed-point reuse is missing")
    if "_strip_runtime_domain_orphan_calls(base" in text:
        raise ValueError("post-span orphan cleanup remains")
    return text


def behavior_contract(text: str) -> None:
    start = text.index("SAFE_DOMAIN_FN = dedent(r'''") + len("SAFE_DOMAIN_FN = dedent(r'''")
    end = text.index("''').lstrip(\"\\n\")", start)
    source = text[start:end]
    namespace: dict[str, object] = {"re": re, "json": json, "Any": Any}
    exec(source, namespace)
    inject = namespace["_inject_runtime_domain_overrides"]
    rules = {"old.example": "new.example", "older.example": "new.example"}
    provider = "const providerByte=1;function getStreams(){};module.exports=__provider;\n"

    canonical, _ = inject(provider, rules)
    canonical_again, _ = inject(canonical, rules)
    assert canonical_again == canonical

    markerless = canonical.replace("/* NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1 */\n", "", 1)
    repaired, _ = inject(markerless, rules)
    assert repaired == markerless
    for _ in range(10):
        repeated, _ = inject(repaired, rules)
        assert repeated == repaired
        repaired = repeated
    assert repaired.count("__nuvioDomainOverrideV1") == 1
    assert repaired.endswith(provider)

    stale = markerless.replace("new.example", "stale.example")
    refreshed, _ = inject(stale, rules)
    assert refreshed != stale
    refreshed_again, _ = inject(refreshed, rules)
    assert refreshed_again == refreshed

    duplicate = markerless + markerless + provider
    collapsed, _ = inject(duplicate, rules)
    assert collapsed.count("__nuvioDomainOverrideV1") == 1
    collapsed_again, _ = inject(collapsed, rules)
    assert collapsed_again == collapsed

    import base64
    single_payload = json.dumps(
        [[base64.b64encode(b"old.example").decode("ascii"), "new.example"]],
        separators=(",", ":"),
    )
    orphans = (
        f'typeof globalThis!=="undefined"?globalThis:this,{single_payload};',
        f'(typeof globalThis!=="undefined"?globalThis:this,{single_payload});',
        f'(typeof globalThis!=="undefined"?globalThis:this,{single_payload})',
    )
    damaged = "\n".join(orphans * 3) + "\n" + repaired
    cleaned, _ = inject(damaged, rules)
    for orphan in orphans:
        assert orphan not in cleaned
    assert cleaned.count("__nuvioDomainOverrideV1") == 1

    foreign = orphans[0].replace("new.example", "foreign.example")
    preserved, _ = inject(foreign + "\n" + repaired, rules)
    assert foreign in preserved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")
    current = CORE.read_text(encoding="utf-8")
    expected = normalized(current)
    if args.check:
        if current != expected:
            raise SystemExit("runtime-domain fixed-point normalizer is not materialized")
        behavior_contract(current)
        print("runtime-domain fixed-point contract verified: full IIFE ownership + markerless reuse + authorized orphan cleanup")
        return 0
    changed = current != expected
    if changed:
        CORE.write_text(expected, encoding="utf-8")
    behavior_contract(expected)
    print(f"runtime-domain fixed-point contract materialized changed={int(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
