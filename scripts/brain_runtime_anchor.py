"""Locate an exact published anchor before deterministic security hardening.

Published provider code is hardened after Lego composition. Match that same
normalization, then map only the selected span back to its original bytes.
Never rewrite or relax ownership outside the approved mutation span.
"""
from difflib import SequenceMatcher
from provider_security_hardening import harden_text


def runtime_anchor(source: str, find: str) -> str:
    if source.count(find) == 1:
        return find
    normalized, _ = harden_text(source)
    if normalized.count(find) != 1:
        raise ValueError('generated Bloc anchor absent or ambiguous after security normalization')
    start = normalized.index(find)
    end = start + len(find)
    opcodes = SequenceMatcher(None, source, normalized, autojunk=False).get_opcodes()

    def original_offset(position):
        for kind, left, right, begin, stop in opcodes:
            if kind == 'equal' and begin <= position <= stop:
                return left + position - begin
            if position == begin:
                return left
            if position == stop:
                return right
        raise ValueError('generated Bloc anchor boundary crosses a security rewrite')

    left, right = original_offset(start), original_offset(end)
    if right <= left:
        raise ValueError('generated Bloc anchor has no original runtime bytes')
    return source[left:right]
