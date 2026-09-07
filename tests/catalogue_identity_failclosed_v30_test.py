#!/usr/bin/env python3
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANIME = ROOT / "scripts" / "provider_patches" / "anime_sama_runtime_v1.py"
source = ANIME.read_text(encoding="utf-8")

assert "NIAKVIO_ANIME_SAMA_SEARCH_IDENTITY_V30" in source
assert "searchSlugIdentityOk(title,s)" in source
assert 'a===b||a.indexOf(b)>=0||b.indexOf(a)>=0' in source
assert 'if(s&&!out.includes(s))out.push(s)' not in source


def slug(value: str) -> str:
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value


def accepted(expected: str, candidate: str) -> bool:
    a, b = slug(expected), slug(candidate)
    return bool(a and b and (a == b or a in b or b in a))

assert not accepted("Children of Men", "LAG")
assert not accepted("Children of Men", "Les Mikails")
assert accepted("Children of Men", "Children of Men")
assert accepted("Les Fils de l'homme", "Les Fils de l'homme")
assert accepted("Children of Men", "Children of Men Extended")

print("catalogue identity fail-closed v30 Anime-Sama regression passed")
