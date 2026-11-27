#!/usr/bin/env python3
"""Bounded static Dean-Edwards player unpacking for diagnostic analysis only.

Never executes JavaScript. The implementation mirrors the production runtime
unpacker closely enough for source-shape comparison and returns inert text.
"""
from __future__ import annotations

import re

MAX_SOURCE = 1_048_576
MAX_BLOCKS = 8
MAX_PAYLOAD = 262_144
MAX_WORDS = 10_000


def _decode_string(src: str, start: int) -> tuple[str, int] | None:
    if start < 0 or start >= len(src) or src[start] not in {"'", '"'}:
        return None
    quote = src[start]
    out: list[str] = []
    escaped = False
    i = start + 1
    while i < len(src):
        ch = src[i]
        if escaped:
            out.append({"n": "\n", "r": "\r", "t": "\t"}.get(ch, ch))
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == quote:
            return "".join(out), i + 1
        else:
            out.append(ch)
            if len(out) > MAX_PAYLOAD:
                return None
        i += 1
    return None


def _skip_ws(src: str, i: int) -> int:
    while i < len(src) and src[i].isspace():
        i += 1
    return i


def _integer(src: str, i: int) -> tuple[int, int] | None:
    i = _skip_ws(src, i)
    match = re.match(r"\d+", src[i:])
    if not match:
        return None
    return int(match.group(0)), i + len(match.group(0))


def _key(value: int, radix: int) -> str:
    if value < 0:
        return ""
    prefix = "" if value < radix else _key(value // radix, radix)
    digit = value % radix
    suffix = chr(digit + 29) if digit > 35 else "0123456789abcdefghijklmnopqrstuvwxyz"[digit]
    return prefix + suffix


def _blocks(source: str) -> list[str]:
    marker = "eval(function(p,a,c,k,e,d)"
    out: list[str] = []
    pos = 0
    while len(out) < MAX_BLOCKS:
        start = source.find(marker, pos)
        if start < 0:
            break
        depth = 0
        quote = ""
        escaped = False
        end = -1
        i = start
        while i < len(source):
            ch = source[i]
            if escaped:
                escaped = False
                i += 1
                continue
            if quote:
                if ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = ""
                i += 1
                continue
            if ch in {"'", '"'}:
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
            i += 1
        if end > start:
            out.append(source[start:end])
            pos = end
        else:
            pos = start + len(marker)
    return out


def _decode_block(block: str) -> str | None:
    call = block.find("}(")
    if call < 0:
        return None
    i = _skip_ws(block, call + 2)
    payload_row = _decode_string(block, i)
    if not payload_row:
        return None
    payload, i = payload_row
    i = _skip_ws(block, i)
    if i >= len(block) or block[i] != ",":
        return None
    radix_row = _integer(block, i + 1)
    if not radix_row:
        return None
    radix, i = radix_row
    if not 2 <= radix <= 62:
        return None
    i = _skip_ws(block, i)
    if i >= len(block) or block[i] != ",":
        return None
    count_row = _integer(block, i + 1)
    if not count_row:
        return None
    count, i = count_row
    if not 0 <= count <= MAX_WORDS:
        return None
    i = _skip_ws(block, i)
    if i >= len(block) or block[i] != ",":
        return None
    words_row = _decode_string(block, _skip_ws(block, i + 1))
    if not words_row:
        return None
    words_raw, end = words_row
    if not re.match(r"\s*\.split\(\s*['\"]\|['\"]\s*\)", block[end:end + 32]):
        return None
    words = words_raw.split("|")[:MAX_WORDS]
    dictionary: dict[str, str] = {}
    for value in range(count - 1, -1, -1):
        key = _key(value, radix)
        dictionary[key] = words[value] if value < len(words) and words[value] else key
    return re.sub(r"\b\w+\b", lambda m: dictionary.get(m.group(0), m.group(0)), payload)


def unpack_packed_player(code: str) -> str:
    source = str(code or "")[:MAX_SOURCE]
    if "p,a,c,k,e,d" not in source:
        return source
    result = source
    for block in _blocks(source):
        decoded = _decode_block(block)
        if decoded:
            result = result.replace(block, decoded, 1)
    return result
