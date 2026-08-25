#!/usr/bin/env python3
"""Compatibility entrypoint for the superseded stream-presentation V11 normalizer.

V11's visible-description-only contract was insufficient for official Nuvio plugin
readers because those clients rebuild or discard provider ``description`` fields.
Keep this filename temporarily for callers that still import it, but delegate every
operation to the authoritative V12 cross-client projection contract.
"""
from __future__ import annotations

from normalize_stream_presentation_v12 import REVISION, assert_contract, main, normalize

__all__ = ["REVISION", "assert_contract", "normalize", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
