#!/usr/bin/env python3
"""Remove the obsolete embedded/obfuscated TMDB key mechanism from Core.

Provider bundles may consume TMDB metadata already injected in request context or
use a credential explicitly supplied by the runtime. They must never serialize,
recover or decrypt a TMDB credential from repository/provider bytes.

This migration is intentionally idempotent and fails if an unexpected legacy
shape remains, so reconstruction cannot silently re-introduce the mechanism.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"


def replace_optional(text: str, old: str, new: str) -> tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = False

    old_doc = """TMDB API metadata is authoritative when available. The build may embed an\nobfuscated runtime-only TMDB v3 API key generated from the repository secret;\nthe plaintext key is never committed and is never passed into provider business\nlogic. Object-style requests can also carry trusted TMDB metadata directly.\n"""
    new_doc = """TMDB API metadata is authoritative when available. Core may consume metadata\nalready injected in the request context/cache or a TMDB credential explicitly\nsupplied by the host runtime. Provider bundles never embed, obfuscate, recover or\ndecrypt a TMDB credential. Object-style requests may carry trusted metadata.\n"""
    text, did = replace_optional(text, old_doc, new_doc)
    changed |= did

    text, did = replace_optional(
        text,
        'RUNTIME_KEY_PATH = ROOT / "runtime" / "tmdb-runtime-key.json"\n\n\n',
        '',
    )
    changed |= did

    start = text.find("def _runtime_key_payload() -> dict[str, Any]:\n")
    if start >= 0:
        end = text.find("\n\ndef _strip_existing", start)
        if end < 0:
            raise AssertionError("embedded TMDB payload helper end anchor drifted")
        text = text[:start] + text[end + 2 :]
        changed = True

    text, did = replace_optional(text, '        **_runtime_key_payload(),\n', '')
    changed |= did

    js_start = text.find('function embeddedKey(){\n')
    if js_start >= 0:
        js_end = text.find('function localKey(){\n', js_start)
        if js_end < 0:
            raise AssertionError("embeddedKey/localKey source anchor drifted")
        text = text[:js_start] + text[js_end:]
        changed = True

    old_local = '''function localKey(){\n  var key="";\n  try{key=normalizeKey(g&&g.TMDB_API_KEY);if(key)return key}catch(_){}\n  try{if(typeof TMDB_API_KEY!=="undefined"){key=normalizeKey(TMDB_API_KEY);if(key)return key}}catch(_){}\n  try{return normalizeKey(embeddedKey())}catch(_){return""}\n}\n'''
    new_local = '''function localKey(){\n  var key="";\n  try{key=normalizeKey(g&&g.TMDB_API_KEY);if(key)return key}catch(_){}\n  try{if(typeof TMDB_API_KEY!=="undefined"){key=normalizeKey(TMDB_API_KEY);if(key)return key}}catch(_){}\n  return"";\n}\n'''
    text, did = replace_optional(text, old_local, new_local)
    changed |= did

    forbidden = (
        "RUNTIME_KEY_PATH",
        "_runtime_key_payload",
        "tmdbKeyCipher",
        "tmdbKeySalt",
        "function embeddedKey",
        "normalizeKey(embeddedKey())",
        "NiakVIO/TMDB/v1",
    )
    leftovers = [needle for needle in forbidden if needle in text]
    if leftovers:
        raise AssertionError(f"embedded TMDB key mechanism still present: {leftovers}")

    if changed:
        TARGET.write_text(text, encoding="utf-8")
    print(f"TMDB_RUNTIME_KEY_EMBED_REMOVAL_OK changed={str(changed).lower()} owner=runtime_or_context")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
