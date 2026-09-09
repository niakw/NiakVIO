#!/usr/bin/env python3
"""Inject a Lab-only native->QuickJS dual-ID context bridge into NuvioDesktop.

This transform is deliberately observational. The IMDb ID is resolved outside
QuickJS by the Lab and passed through NIAKVIO_LAB_IMDB_ID. No TMDB credential is
exposed to provider JavaScript. The provider bytes remain untouched.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARKER = "NIAKVIO_LAB_DUAL_ID_CONTEXT_V1"
ANCHOR = '''                evaluate<Any?>(polyfillCode)\n\n                val wrappedCode = """'''
INJECTION = '''                evaluate<Any?>(polyfillCode)\n\n                // NIAKVIO_LAB_DUAL_ID_CONTEXT_V1: host-resolved identity only; no secret enters JS.\n                val labImdbId = System.getenv("NIAKVIO_LAB_IMDB_ID")?.trim().orEmpty()\n                val mediaContextJson = JsonObject(\n                    mapOf(\n                        "tmdbId" to JsonPrimitive(tmdbId),\n                        "imdbId" to JsonPrimitive(labImdbId),\n                        "canonicalMediaType" to JsonPrimitive(mediaType),\n                        "tmdbNamespace" to JsonPrimitive(mediaType),\n                    )\n                ).toString()\n                evaluate<Any?>("globalThis.__nuvioMediaContext = $mediaContextJson;")\n\n                val wrappedCode = """'''


def augment(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"FIELD_NATIVE_DESKTOP_DUAL_ID_CONTEXT already=true source={path}")
        return False
    count = text.count(ANCHOR)
    if count != 1:
        raise SystemExit(f"dual-id runtime anchor count={count}")
    text = text.replace(ANCHOR, INJECTION, 1)
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_DESKTOP_DUAL_ID_CONTEXT added=true source={path} provider_bytes_mutated=false secret_exposed=false")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    augment(Path(args.source).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
