#!/usr/bin/env python3
"""Finalize NiakVIO-owned Android reader test source before request augmentation.

This never edits Nuvio production sources. It only fixes two harness contracts in the
generated ephemeral instrumentation test:

* the generic production-player entry marker is FIELD_NATIVE_PLAYER_ENTRY; the later
  request-contract augmenter owns the sole enriched FIELD_NATIVE_PLAYER_BEGIN marker;
* NuvioMobile's reader probe targets the separately installed official androidApp
  debug APK instead of the composeApp instrumentation target package.
"""
from __future__ import annotations

MOBILE_DEBUG_PACKAGE = "com.nuviodebug.com"
GENERIC_BEGIN = "FIELD_NATIVE_PLAYER_BEGIN client="
GENERIC_ENTRY = "FIELD_NATIVE_PLAYER_ENTRY client="
ENTRY_SUFFIX = " entry=nuvio-production-player"
MOBILE_CONTEXT_LAUNCH = "context.packageManager.getLaunchIntentForPackage(context.packageName)"
MOBILE_DEBUG_LAUNCH = (
    'context.packageManager.getLaunchIntentForPackage("' + MOBILE_DEBUG_PACKAGE + '")'
)


def finalize_source(source: str, client: str) -> str:
    if client not in {"mobile", "tv"}:
        raise ValueError(f"unsupported Android client: {client}")

    generic_lines = [
        line for line in source.splitlines()
        if GENERIC_BEGIN in line and ENTRY_SUFFIX in line
    ]
    if len(generic_lines) != 1:
        raise ValueError(
            f"expected exactly one generic player entry marker for {client}, found {len(generic_lines)}"
        )
    source = source.replace(GENERIC_BEGIN, GENERIC_ENTRY, 1)

    if client == "mobile":
        count = source.count(MOBILE_CONTEXT_LAUNCH)
        if count != 1:
            raise ValueError(
                f"expected exactly one mobile context-package launch probe, found {count}"
            )
        source = source.replace(MOBILE_CONTEXT_LAUNCH, MOBILE_DEBUG_LAUNCH, 1)

    if any(
        GENERIC_BEGIN in line and ENTRY_SUFFIX in line
        for line in source.splitlines()
    ):
        raise ValueError("generic FIELD_NATIVE_PLAYER_BEGIN survived finalization")
    if not any(
        GENERIC_ENTRY in line and ENTRY_SUFFIX in line
        for line in source.splitlines()
    ):
        raise ValueError("FIELD_NATIVE_PLAYER_ENTRY was not materialized")
    if client == "mobile" and MOBILE_DEBUG_LAUNCH not in source:
        raise ValueError("official NuvioMobile debug launch package was not materialized")
    return source
