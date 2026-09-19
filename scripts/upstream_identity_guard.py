#!/usr/bin/env python3
"""Conservative route-identity guard for upstream parity evidence.

This is an audit guard, not Core identity policy. It only rejects strong route
contradictions that can be proven from the upstream's own content URL. In
particular, a one-significant-token requested title must not silently resolve to
a different title/franchise page. Multi-word aliases remain UNKNOWN unless a
stronger identity source proves a contradiction elsewhere.
"""
from __future__ import annotations

import re
import unicodedata
import urllib.parse
from typing import Any

_ROUTE_MARKERS = {
    "anime", "animes", "series", "serie", "tvshows", "tvshow",
    "movie", "movies", "film", "films",
}
_STOP = {
    "a", "an", "the", "of", "and", "or", "de", "du", "des", "la", "le", "les",
    "un", "une", "et", "no", "to", "in", "on",
}
_SUFFIX = {
    "vf", "vostfr", "vo", "vost", "fr", "french", "dub", "dubbed", "sub", "subbed",
    "hd", "fhd", "uhd", "4k", "film", "movie",
}
_SEASON_RE = re.compile(r"^(?:s|season|saison)\d+$", re.I)
_EPISODE_RE = re.compile(r"^(?:e|ep|episode)\d+$", re.I)
_YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _tokens(value: object) -> list[str]:
    return [token for token in _norm(value).split() if token and token not in _STOP]


def _clean_slug_tokens(slug: str) -> list[str]:
    tokens = _tokens(urllib.parse.unquote(slug).removesuffix(".html"))
    while tokens and (tokens[-1] in _SUFFIX or _YEAR_RE.match(tokens[-1]) or _SEASON_RE.match(tokens[-1]) or _EPISODE_RE.match(tokens[-1])):
        tokens.pop()
    # Common trailing season pair: "saison 3" / "season 3".
    if len(tokens) >= 2 and tokens[-2] in {"season", "saison"} and tokens[-1].isdigit():
        tokens = tokens[:-2]
    return tokens


def _route_candidates(raw: dict[str, Any]) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []
    for row in raw.get("network_observations") or []:
        if not isinstance(row, dict):
            continue
        stage = str(row.get("stage") or "").casefold()
        if stage not in {"content_lookup", "episode", "search"}:
            continue
        proof = str(row.get("proof_url") or "").strip()
        if not proof.startswith(("http://", "https://")):
            continue
        try:
            parts = [part for part in urllib.parse.urlsplit(proof).path.split("/") if part]
        except Exception:
            continue
        for index, part in enumerate(parts[:-1]):
            if part.casefold() not in _ROUTE_MARKERS:
                continue
            candidate = _clean_slug_tokens(parts[index + 1])
            if candidate:
                item = (proof, candidate)
                if item not in out:
                    out.append(item)
            break
    return out


def classify_route_identity(raw: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any]:
    """Return MATCH/CONTRADICTION/UNKNOWN without broad alias guessing.

    Only one-significant-token requested titles are auto-rejected from route
    slugs. This catches the demonstrated false positives while avoiding false
    negatives for translated/Japanese aliases such as Nanatsu no Taizai.
    """
    expected = _tokens(fixture.get("title") or fixture.get("name") or "")
    if len(expected) != 1:
        return {"status": "UNKNOWN", "reason": "non_single_token_title"}
    token = expected[0]
    candidates = _route_candidates(raw)
    if not candidates:
        return {"status": "UNKNOWN", "reason": "no_content_route_slug"}

    exact = []
    contradictions = []
    for proof, candidate in candidates:
        if candidate == [token]:
            exact.append(proof)
            continue
        # A route with the expected token plus another significant title token
        # is still a different identity (Joker Game, Garden of Sinners,
        # Interstellar Documentary). Language/year/quality suffixes were removed.
        contradictions.append({"route": proof, "tokens": candidate[:12]})

    if exact:
        return {"status": "MATCH", "reason": "exact_content_route", "route_count": len(exact)}
    if contradictions:
        return {
            "status": "CONTRADICTION",
            "reason": "single_token_title_routed_to_different_content_slug",
            "expected": token,
            "observed": [row["tokens"] for row in contradictions[:4]],
        }
    return {"status": "UNKNOWN", "reason": "no_decisive_route"}
