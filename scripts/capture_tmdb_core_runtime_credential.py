#!/usr/bin/env python3
"""Capture runtime TMDB credentials once inside the Core closure.

The host may expose a credential during provider module initialization (CI/server
mode). Core captures it into closure-local variables and all later getTmdbData()
requests use those values. ProviderBase/presentation receive metadata only.
Native clients may continue to use the authenticated native fetch bridge without
exposing any JavaScript credential at all.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = False

    capture = 'var coreCredentialKey=localKey(),coreCredentialToken=localToken();\n'
    anchor = '''function localToken(){
  try{if(g&&s(g.TMDB_ACCESS_TOKEN))return s(g.TMDB_ACCESS_TOKEN)}catch(_){}
  try{if(typeof TMDB_ACCESS_TOKEN!=="undefined"&&s(TMDB_ACCESS_TOKEN))return s(TMDB_ACCESS_TOKEN)}catch(_){}
  return "";
}
'''
    if capture not in text:
        if text.count(anchor) != 1:
            raise AssertionError("Core credential capture anchor drifted")
        text = text.replace(anchor, anchor + capture, 1)
        changed = True

    old_api = '  var key=localKey(),token=localToken(),nativeBridge=nativeFetchBridge();\n'
    new_api = '  var key=coreCredentialKey,token=coreCredentialToken,nativeBridge=nativeFetchBridge();\n'
    if new_api not in text:
        if text.count(old_api) != 1:
            raise AssertionError("Core apiJson credential ownership anchor drifted")
        text = text.replace(old_api, new_api, 1)
        changed = True

    required = (
        'var coreCredentialKey=localKey(),coreCredentialToken=localToken();',
        'var key=coreCredentialKey,token=coreCredentialToken,nativeBridge=nativeFetchBridge();',
        'g.__nuvioCoreGetTmdbDataV1=coreGetTmdbData',
    )
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise AssertionError(f"Core TMDB credential closure missing: {missing}")

    # getTmdbData/apiJson must no longer re-read the host globals after init.
    api_start = text.find('async function apiJson(url){')
    api_end = text.find('\nasync function findTmdb(', api_start)
    if api_start < 0 or api_end < 0:
        raise AssertionError("Core apiJson bounds missing")
    api_body = text[api_start:api_end]
    if 'localKey()' in api_body or 'localToken()' in api_body:
        raise AssertionError("Core TMDB request path still re-reads runtime credential")

    if changed:
        TARGET.write_text(text, encoding="utf-8")
    print(f"TMDB_CORE_CREDENTIAL_CLOSURE_OK changed={str(changed).lower()} credential_returned=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
