"""Locate an exact published anchor before deterministic runtime formatting.

Published provider code is hardened and minimized after Lego composition. Match that same
normalization, then map only the selected span back to its original bytes.
Never rewrite or relax ownership outside the approved mutation span.
"""
from difflib import SequenceMatcher
import re
from provider_security_hardening import harden_text
from provider_v3_minimizer import minimize_text


def runtime_anchor(source: str, find: str) -> str:
    if source.count(find) == 1:
        return find
    normalized, _ = harden_text(source)
    if normalized.count(find) != 1:
        return minimized_runtime_anchor(source, normalized, find)
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


def minimized_runtime_anchor(source: str, hardened: str, find: str) -> str:
    """Map published one-line code back to readable composition bytes.

    Token-sized alignment avoids a quadratic character diff over the whole
    ProviderBase. Matching still uses the exact deterministic minimizer output.
    """
    normalized = minimize_text(hardened).text
    wanted = minimize_text(find).text
    if not wanted or normalized.count(wanted) != 1:
        raise ValueError('generated Bloc anchor absent or ambiguous after canonical normalization')
    left_tokens = list(re.finditer(r'\S+', source))
    right_tokens = list(re.finditer(r'\S+', normalized))
    matcher = SequenceMatcher(None, [row.group() for row in left_tokens],
                              [row.group() for row in right_tokens], autojunk=False)
    blocks = matcher.get_opcodes()

    def offset(position):
        for kind, a, b, c, d in blocks:
            if c == d:
                continue
            start, end = right_tokens[c].start(), right_tokens[d - 1].end()
            if kind == 'equal' and start <= position <= end:
                for index in range(c, d):
                    token = right_tokens[index]
                    if token.start() <= position <= token.end():
                        return left_tokens[a + index - c].start() + position - token.start()
            if position == start and a < len(left_tokens):
                return left_tokens[a].start()
            if position == end and b > a:
                return left_tokens[b - 1].end()
        raise ValueError('generated Bloc boundary crosses a canonical rewrite')

    start = normalized.index(wanted)
    left, right = offset(start), offset(start + len(wanted))
    if right <= left:
        raise ValueError('generated Bloc anchor has no original composition bytes')
    anchor = source[left:right]
    # Alignment only proposes boundaries. Prove the selected original bytes
    # independently normalize to the complete requested span before editing.
    # The surrounding source supplies logging declarations during hardening.
    original_hardened = hardened_span(source, hardened, left, right)
    if minimize_text(original_hardened).text != wanted or source.count(anchor) != 1:
        raise ValueError('generated Bloc canonical span does not match its original bytes')
    return anchor


def hardened_span(source: str, hardened: str, left: int, right: int) -> str:
    """Normalize a local span without adding a second logging prelude."""
    span = source[left:right]
    # Preserve the declared logger context. Other rewrites that need additional
    # declarations cannot be proved from a fragment and deliberately fail closed.
    if '__nuvioProviderSilentLog' in hardened:
        prefix = 'var __nuvioProviderSilentLog=function(){};\n'
        normalized, _ = harden_text(prefix + span)
        if normalized.startswith(prefix):
            return normalized[len(prefix):]
    return harden_text(span)[0]
