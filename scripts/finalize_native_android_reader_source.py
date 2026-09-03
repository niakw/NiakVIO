#!/usr/bin/env python3
"""Finalize NiakVIO-owned Android reader test source before request augmentation.

This never edits Nuvio production sources. It only fixes two harness contracts in the
generated ephemeral instrumentation test:

* the generic production-player entry marker is FIELD_NATIVE_PLAYER_ENTRY; the later
  request-contract augmenter owns the sole enriched FIELD_NATIVE_PLAYER_BEGIN marker;
* NuvioMobile's reader probe starts the production MainActivity class explicitly.
  This avoids launcher-alias/package-resolution drift while still exercising the
  separately installed official androidApp debug APK.
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
MOBILE_EXPLICIT_MAIN_ACTIVITY = "Intent(context, MainActivity::class.java)"


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
        # The current reader generator launches NuvioMobile's real MainActivity
        # explicitly. Older harnesses used packageManager launcher resolution and
        # then rewrote that package; keeping that rewrite here made the Lab fail
        # before a single provider executed after NuvioMobile adopted icon aliases.
        explicit_count = source.count(MOBILE_EXPLICIT_MAIN_ACTIVITY)
        if explicit_count != 1:
            raise ValueError(
                f"expected exactly one explicit mobile MainActivity launch probe, found {explicit_count}"
            )
        if MOBILE_CONTEXT_LAUNCH in source or MOBILE_DEBUG_LAUNCH in source:
            raise ValueError("obsolete mobile package-launch probe survived code generation")

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
    if client == "mobile" and MOBILE_EXPLICIT_MAIN_ACTIVITY not in source:
        raise ValueError("official NuvioMobile MainActivity launch was not materialized")
    return source
