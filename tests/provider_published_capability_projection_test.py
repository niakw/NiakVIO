#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from materialize_provider_v3_all import project_published_semantic_types, normalize_anime_transport_compatibility

movie={"supportedTypes":["movie","tv"]}
assert project_published_semantic_types(movie,{"published_types":["movie"]}) is True
normalize_anime_transport_compatibility(movie)
assert movie["canonicalSupportedTypes"]==["movie"], movie
assert movie["supportedTypes"]==["movie"], movie

anime={"supportedTypes":["anime","movie"]}
assert project_published_semantic_types(anime,{"published_types":["anime"]}) is True
normalize_anime_transport_compatibility(anime)
assert anime["canonicalSupportedTypes"]==["anime"], anime
assert anime["supportedTypes"]==["anime","tv"], anime
assert "movie" not in anime["supportedTypes"], anime

unchanged={"supportedTypes":["movie","tv"]}
assert project_published_semantic_types(unchanged,{}) is False
assert unchanged["supportedTypes"]==["movie","tv"]

print("provider published capability projection passed")
