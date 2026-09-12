#!/usr/bin/env python3
"""Finalize NiakVIO-owned Android reader test source before request augmentation.

This never edits Nuvio production sources. It only fixes two harness contracts in the
generated ephemeral instrumentation test:

* the generic production-player entry marker is FIELD_NATIVE_PLAYER_ENTRY; the later
  request-contract augmenter owns the sole enriched FIELD_NATIVE_PLAYER_BEGIN marker;
* NuvioMobile's reader probe starts the production MainActivity class explicitly in
  the exact application package under instrumentation. This avoids launcher-alias
  drift without hard-coding an applicationId that can change between client builds.
"""
from __future__ import annotations

GENERIC_BEGIN = "FIELD_NATIVE_PLAYER_BEGIN client="
GENERIC_ENTRY = "FIELD_NATIVE_PLAYER_ENTRY client="
ENTRY_SUFFIX = " entry=nuvio-production-player"
MOBILE_CONTEXT_LAUNCH = "context.packageManager.getLaunchIntentForPackage(context.packageName)"
MOBILE_EXPLICIT_SET_CLASS = "Intent().setClassName("
MOBILE_EXPLICIT_CONTEXT_PACKAGE = "context.packageName,"
MOBILE_EXPLICIT_MAIN_ACTIVITY = "MainActivity::class.java.name"
MOBILE_LEGACY_EXPLICIT_LAUNCH = '''Intent().setClassName(
                "com.nuviodebug.com",
                MainActivity::class.java.name,
            )'''


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
        # The reader must launch NuvioMobile's real MainActivity explicitly while
        # staying inside the exact package installed for instrumentation. A fixed
        # package literal made the Lab drift from the client it had actually built.
        explicit_set_class_count = source.count(MOBILE_EXPLICIT_SET_CLASS)
        explicit_context_count = source.count(MOBILE_EXPLICIT_CONTEXT_PACKAGE)
        explicit_main_count = source.count(MOBILE_EXPLICIT_MAIN_ACTIVITY)
        if explicit_set_class_count != 1 or explicit_context_count < 1 or explicit_main_count != 1:
            raise ValueError(
                "expected exactly one explicit mobile MainActivity setClassName launch probe, "
                f"found setClassName={explicit_set_class_count} contextPackage={explicit_context_count} "
                f"mainActivity={explicit_main_count}"
            )
        if MOBILE_CONTEXT_LAUNCH in source:
            raise ValueError("obsolete mobile package-launch probe survived code generation")
        if MOBILE_LEGACY_EXPLICIT_LAUNCH in source:
            raise ValueError("hard-coded mobile debug package survived code generation")

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
    if client == "mobile" and (
        MOBILE_EXPLICIT_SET_CLASS not in source
        or MOBILE_EXPLICIT_CONTEXT_PACKAGE not in source
        or MOBILE_EXPLICIT_MAIN_ACTIVITY not in source
        or MOBILE_LEGACY_EXPLICIT_LAUNCH in source
    ):
        raise ValueError("instrumented-package NuvioMobile MainActivity setClassName launch was not materialized")
    return source
