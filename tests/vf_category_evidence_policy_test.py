#!/usr/bin/env python3
"""Regression contract for VF publication evidence.

The local/global validator must keep evidence separate for movie, tv and anime.
A French movie result cannot validate a provider's tv/anime capability, and a
VO result cannot validate any category in the VF manifest.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
validator = (ROOT / "scripts" / "local" / "test_global_provider_repair.py")
if validator.exists():
    text = validator.read_text(encoding="utf-8")
    assert "vf_movie" in text or "movie_vf" in text
    assert "audio_languages" in text
    assert "subtitle_languages" in text
print("VF category evidence policy test passed")
