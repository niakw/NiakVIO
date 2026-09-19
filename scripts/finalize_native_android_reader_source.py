#!/usr/bin/env python3
"""Finalize NiakVIO-owned Android reader test source before request augmentation.

This never edits Nuvio production sources. It only fixes two harness contracts in the
generated ephemeral instrumentation test:

* the generic production-player entry marker is FIELD_NATIVE_PLAYER_ENTRY; the later
  request-contract augmenter owns the sole enriched FIELD_NATIVE_PLAYER_BEGIN marker;
* NuvioMobile's reader probe resolves the installed launcher component through
  PackageManager. Kotlin namespace and instrumentation context are not authoritative
  for the installed applicationId.
"""
from __future__ import annotations

GENERIC_BEGIN = "FIELD_NATIVE_PLAYER_BEGIN client="
GENERIC_ENTRY = "FIELD_NATIVE_PLAYER_ENTRY client="
ENTRY_SUFFIX = " entry=nuvio-production-player"
MOBILE_CONTEXT_LAUNCH = "context.packageManager.getLaunchIntentForPackage(context.packageName)"
MOBILE_EXPLICIT_SET_CLASS = "Intent().setClassName("
MOBILE_EXPLICIT_CONTEXT_PACKAGE = "context.packageName,"
MOBILE_EXPLICIT_TARGET_PACKAGE = "MainActivity::class.java.packageName,"
MOBILE_EXPLICIT_MAIN_ACTIVITY = "MainActivity::class.java.name"
MOBILE_LAUNCHER_QUERY = "val launcherQuery = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)"
MOBILE_QUERY_ACTIVITIES = "context.packageManager.queryIntentActivities(launcherQuery, 0)"
MOBILE_INSTALLED_PACKAGE = "launchActivity.activityInfo.packageName,"
MOBILE_INSTALLED_ACTIVITY = "launchActivity.activityInfo.name,"
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
        # The installed launcher component is authoritative. Kotlin namespace,
        # instrumentation package and applicationId are allowed to differ.
        explicit_set_class_count = source.count(MOBILE_EXPLICIT_SET_CLASS)
        launcher_query_count = source.count(MOBILE_LAUNCHER_QUERY)
        query_count = source.count(MOBILE_QUERY_ACTIVITIES)
        installed_package_count = source.count(MOBILE_INSTALLED_PACKAGE)
        installed_activity_count = source.count(MOBILE_INSTALLED_ACTIVITY)
        if (
            explicit_set_class_count != 1
            or launcher_query_count != 1
            or query_count < 1
            or installed_package_count != 1
            or installed_activity_count != 1
        ):
            raise ValueError(
                "expected one generated applicationId-safe Mobile launcher probe, "
                f"setClassName={explicit_set_class_count} launcherQuery={launcher_query_count} "
                f"queries={query_count} package={installed_package_count} activity={installed_activity_count}"
            )
        for obsolete in (
            MOBILE_CONTEXT_LAUNCH,
            MOBILE_EXPLICIT_CONTEXT_PACKAGE,
            MOBILE_EXPLICIT_TARGET_PACKAGE,
            MOBILE_LEGACY_EXPLICIT_LAUNCH,
        ):
            if obsolete in source:
                raise ValueError("obsolete namespace/package-based Mobile launcher survived code generation")

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
        or MOBILE_LAUNCHER_QUERY not in source
        or MOBILE_QUERY_ACTIVITIES not in source
        or MOBILE_INSTALLED_PACKAGE not in source
        or MOBILE_INSTALLED_ACTIVITY not in source
        or MOBILE_EXPLICIT_CONTEXT_PACKAGE in source
        or MOBILE_EXPLICIT_TARGET_PACKAGE in source
        or MOBILE_LEGACY_EXPLICIT_LAUNCH in source
    ):
        raise ValueError("applicationId-safe NuvioMobile launcher resolution was not materialized")
    return source
