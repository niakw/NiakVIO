#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch_augment() -> None:
    path = ROOT / "scripts/augment_native_corpus_request_contract.py"
    text = path.read_text(encoding="utf-8")
    if "from rotating_corpus import fixture_by_slug as rotating_fixture_by_slug" not in text:
        anchor = "from native_media_type_contract import canonical_media_type, fixture_media_type  # noqa: E402\n"
        replacement = anchor + "from rotating_corpus import fixture_by_slug as rotating_fixture_by_slug  # noqa: E402\n"
        if text.count(anchor) != 1:
            raise SystemExit("augment rotating import anchor missing")
        text = text.replace(anchor, replacement, 1)
    pattern = re.compile(r"def fixture\(slug: str\) -> dict:\n.*?\n\ndef manifest_types", re.S)
    replacement = '''def fixture(slug: str) -> dict:
    try:
        row = rotating_fixture_by_slug(slug)
    except KeyError as error:
        raise SystemExit(str(error)) from error
    return {key: value for key, value in row.items() if key not in {"slug", "lane"}}


def manifest_types'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"augment fixture resolver patch count={count}")
    path.write_text(text, encoding="utf-8")


def patch_reader_acceptance() -> None:
    path = ROOT / "scripts/prepare_native_reader_acceptance.py"
    text = path.read_text(encoding="utf-8")
    if "from rotating_corpus import fixture_by_slug as rotating_fixture_by_slug" not in text:
        anchor = "from native_client_test_bootstrap import (  # noqa: E402\n"
        import_line = "from rotating_corpus import fixture_by_slug as rotating_fixture_by_slug  # noqa: E402\n"
        if text.count(anchor) != 1:
            raise SystemExit("reader rotating import anchor missing")
        text = text.replace(anchor, import_line + anchor, 1)
    pattern = re.compile(r"def fixture_row\(slug: str\) -> dict:\n.*?\n\ndef select_providers", re.S)
    replacement = '''def fixture_row(slug: str) -> dict:
    try:
        fixture = rotating_fixture_by_slug(slug)
    except KeyError as error:
        raise SystemExit(str(error)) from error
    clean = {key: value for key, value in fixture.items() if key not in {"lane"}}
    return {"slug": slug, "fixture": clean, "providers": []}


def select_providers'''
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(f"reader fixture resolver patch count={count}")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    patch_augment()
    patch_reader_acceptance()
    print("rotating fixture consumers patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
