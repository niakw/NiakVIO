#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load_module("prepare_native_corpus_client_tested", SCRIPTS / "prepare_native_corpus_client.py")
restage = load_module("restage_native_corpus_client_tested", SCRIPTS / "restage_native_corpus_client.py")

DESKTOP_OLD = '        assertTrue(errors.isEmpty(), "native provider runtime errors: " + errors.take(12).joinToString(" | "))\n'
ANDROID_OLD = '        assertTrue("native provider runtime errors: " + errors.take(12).joinToString(" | "), errors.isEmpty())\n'
DESKTOP_NEW = '        assertTrue(providers.isNotEmpty(), "native corpus provider list must not be empty")\n'
ANDROID_NEW = '        assertTrue("native corpus provider list must not be empty", providers.isNotEmpty())\n'


class NativeCorpusCollectorAssertionTest(unittest.TestCase):
    def test_desktop_prepare_and_restage_keep_kotlin_assertion_order(self):
        source = "before\n" + DESKTOP_OLD + "after\n"
        prepared = prepare._collector_test(source, "desktop")
        restaged = restage.collector_test(source, "desktop")
        self.assertEqual(prepared, restaged)
        self.assertIn(DESKTOP_NEW, prepared)
        self.assertNotIn(ANDROID_NEW, prepared)
        self.assertNotIn(DESKTOP_OLD, prepared)

    def test_mobile_prepare_and_restage_keep_junit_assertion_order(self):
        source = "before\n" + ANDROID_OLD + "after\n"
        prepared = prepare._collector_test(source, "mobile")
        restaged = restage.collector_test(source, "mobile")
        self.assertEqual(prepared, restaged)
        self.assertIn(ANDROID_NEW, prepared)
        self.assertNotIn(DESKTOP_NEW, prepared)
        self.assertNotIn(ANDROID_OLD, prepared)

    def test_tv_uses_same_android_junit_contract(self):
        source = "before\n" + ANDROID_OLD + "after\n"
        self.assertEqual(
            prepare._collector_test(source, "tv"),
            restage.collector_test(source, "tv"),
        )


if __name__ == "__main__":
    unittest.main()
