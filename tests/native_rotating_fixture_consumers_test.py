#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rotating_corpus  # noqa: E402

for slug in ("parasite-2019", "squid-game-s01e01", "failure-frame-s01e01"):
    row = rotating_corpus.fixture_by_slug(slug)
    assert row["slug"] == slug, row

reader_source = (ROOT / "scripts/prepare_native_reader_acceptance.py").read_text(encoding="utf-8")
augment_source = (ROOT / "scripts/augment_native_corpus_request_contract.py").read_text(encoding="utf-8")
assert "rotating_fixture_by_slug" in reader_source
assert "rotating_fixture_by_slug" in augment_source

reader_spec = importlib.util.spec_from_file_location(
    "prepare_native_reader_acceptance",
    ROOT / "scripts/prepare_native_reader_acceptance.py",
)
assert reader_spec and reader_spec.loader
reader = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader)
for slug in ("parasite-2019", "squid-game-s01e01", "failure-frame-s01e01"):
    row = reader.fixture_row(slug)
    assert row["slug"] == slug
    assert row["fixture"]["tmdbId"]

augment_spec = importlib.util.spec_from_file_location(
    "augment_native_corpus_request_contract",
    ROOT / "scripts/augment_native_corpus_request_contract.py",
)
assert augment_spec and augment_spec.loader
augment = importlib.util.module_from_spec(augment_spec)
augment_spec.loader.exec_module(augment)
for slug in ("parasite-2019", "squid-game-s01e01", "failure-frame-s01e01"):
    fixture = augment.fixture(slug)
    assert fixture["tmdbId"]

# Cross-platform CLI contract: the source explicitly forces LF so Git Bash on
# Windows cannot preserve a CR in a slug/log filename.
rotation_source = (ROOT / "scripts/rotating_corpus.py").read_text(encoding="utf-8")
assert 'sys.stdout.reconfigure(newline="\\n")' in rotation_source

print("native rotating fixture consumer tests passed")
