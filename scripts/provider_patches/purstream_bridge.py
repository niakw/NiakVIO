"""Strip repository-owned Purstream-to-Movix bridge wrappers.

Purstream resolves only through its own native/provider routes. This cleanup-only
patch never installs a fallback and is safe to reapply when no bridge marker is
present.
"""
from __future__ import annotations

MARKER = "NUVIO_PURSTREAM_BRIDGE_V1"
END = '})(typeof globalThis!=="undefined"?globalThis:this);'


def apply(source: str, **_kwargs) -> str:
    marker = f"/* {MARKER} */"
    output = source
    while True:
        start = output.find(marker)
        if start < 0:
            return output
        end = output.find(END, start)
        if end < 0:
            raise ValueError("unterminated retired Purstream bridge wrapper")
        end += len(END)
        before = output[:start].rstrip()
        after = output[end:].lstrip("\r\n")
        if before and after:
            output = before + "\n" + after
        else:
            output = before or after
