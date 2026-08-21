#!/usr/bin/env python3
"""Enable NuvioTV Android instrumentation tests without version-specific anchors."""
from __future__ import annotations

from pathlib import Path

RUNNER = 'testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"'
EXT_JUNIT = 'androidTestImplementation("androidx.test.ext:junit:1.3.0")'
TEST_RUNNER = 'androidTestImplementation("androidx.test:runner:1.7.0")'


def enable_tv_tests(repo: Path) -> None:
    """Patch the official NuvioTV Gradle file structurally and idempotently.

    Client version bumps must never break the Lab.  The Android ``defaultConfig``
    block is the stable contract; ``versionName`` is deliberately not an anchor.
    """
    build = Path(repo) / "app/build.gradle.kts"
    text = build.read_text(encoding="utf-8")

    release_signing = '        debug {\n            signingConfig = signingConfigs.getByName("release")'
    debug_signing = '        debug {\n            signingConfig = signingConfigs.getByName("debug")'
    if release_signing in text:
        text = text.replace(release_signing, debug_signing, 1)
    elif debug_signing not in text:
        raise SystemExit("NuvioTV debug signing contract missing")

    if RUNNER not in text:
        default_config = "    defaultConfig {\n"
        if text.count(default_config) != 1:
            raise SystemExit(
                f"NuvioTV defaultConfig structural anchor count={text.count(default_config)}"
            )
        text = text.replace(
            default_config,
            default_config + f"        {RUNNER}\n",
            1,
        )

    missing_dependencies = [
        dependency
        for dependency in (EXT_JUNIT, TEST_RUNNER)
        if dependency not in text
    ]
    if missing_dependencies:
        text = text.rstrip() + "\n\n\ndependencies {\n"
        text += "\n".join(f"    {dependency}" for dependency in missing_dependencies)
        text += "\n}\n"

    build.write_text(text, encoding="utf-8")
