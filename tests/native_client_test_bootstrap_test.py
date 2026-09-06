#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from native_client_test_bootstrap import enable_mobile_device_tests  # noqa: E402

BASE_SOURCE_SETS = '''
    sourceSets {
        commonMain.dependencies {
            implementation("example:dependency:1")
        }
    }
'''

HOST_TEST_VARIANTS = (
    "        withHostTest {}\n\n        compilerOptions {\n            jvmTarget.set(JvmTarget.JVM_11)\n        }",
    "        withHostTest { isIncludeAndroidResources = true }\n\n        compilerOptions {\n            jvmTarget.set(JvmTarget.JVM_11)\n        }",
)

for host_test in HOST_TEST_VARIANTS:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        build = repo / "composeApp/build.gradle.kts"
        build.parent.mkdir(parents=True)
        build.write_text(
            "kotlin {\n    android {\n" + host_test + "\n    }\n" + BASE_SOURCE_SETS + "}\n",
            encoding="utf-8",
        )

        enable_mobile_device_tests(repo)
        once = build.read_text(encoding="utf-8")
        assert once.count("withDeviceTest {") == 1
        assert once.count('instrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"') == 1
        assert once.count('execution = "HOST"') == 1
        assert once.count("val androidDeviceTest by getting {") == 1
        assert once.count('pickFirsts.add("lib/*/libc++_shared.so")') == 1
        assert "withHostTest {" in once

        # The bootstrap is deliberately idempotent so a fixture restage cannot
        # accumulate test-only Gradle mutations.
        enable_mobile_device_tests(repo)
        twice = build.read_text(encoding="utf-8")
        assert twice == once

print("native client test bootstrap upstream-DSL compatibility passed")
