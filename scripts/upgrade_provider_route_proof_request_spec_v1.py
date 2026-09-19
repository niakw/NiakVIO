#!/usr/bin/env python3
"""Extend provider_route_proof with request-spec dataflow abstraction."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_route_proof.py"
MARKER = "PROVIDER_ROUTE_PROOF_REQUEST_SPEC_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    anchor = '''def derive_observed_route(
    fetch: dict[str, Any],
    task: dict[str, Any],
    prior_value_hints: Iterable[dict[str, Any]] | None = None,
) -> tuple[str | None, dict[str, Any]]:
'''
    helpers = r'''# PROVIDER_ROUTE_PROOF_REQUEST_SPEC_V1
BODY_TITLE_KEYS = {"q", "query", "search", "title", "keyword", "story", "name"}
BODY_SEASON_KEYS = {"s", "season", "season_number", "seasonid", "season_id"}
BODY_EPISODE_KEYS = {"e", "ep", "episode", "episode_number", "episodeid", "episode_id"}
BODY_MEDIA_KEYS = {"type", "mediatype", "media_type", "media", "category", "kind"}
BODY_TMDB_KEYS = {"id", "tmdb", "tmdbid", "tmdb_id", "movie", "tv"}
BODY_YEAR_KEYS = {"year", "releaseyear", "release_year"}


def _request_scalar_placeholder(
    key: object,
    raw_value: object,
    fixture: dict[str, Any],
    provider_values: set[str],
) -> str | None:
    value = str(raw_value if raw_value is not None else "").strip()
    key_l = canonical(key)
    if not value:
        return None
    tmdb = str(fixture.get("tmdbId") or "").strip()
    season = str(fixture.get("season") or "").strip()
    episode = str(fixture.get("episode") or "").strip()
    year = str(fixture.get("year") or "").strip()
    titles = {canonical(fixture.get("title"))}
    titles.update(canonical(v) for v in fixture.get("aliases") or [])
    titles.discard("")
    media = canonical(fixture.get("mediaType") or fixture.get("type") or fixture.get("category"))

    if tmdb and value == tmdb and key_l in BODY_TMDB_KEYS:
        return "{tmdbId}"
    if season and value == season and key_l in BODY_SEASON_KEYS:
        return "{season}"
    if episode and value == episode and key_l in BODY_EPISODE_KEYS:
        return "{episode}"
    if canonical(value) in titles and key_l in BODY_TITLE_KEYS:
        return "{query}"
    if value in provider_values and key_l in PROVIDER_VALUE_KEYS:
        return "{id}"
    if media in SEMANTIC_TYPES and canonical(value) in {media, "series" if media == "tv" else media} and key_l in BODY_MEDIA_KEYS:
        return "{media}"
    if year and value == year and key_l in BODY_YEAR_KEYS:
        return "{year}"
    return None


def derive_request_spec(
    fetch: dict[str, Any],
    task: dict[str, Any],
    prior_value_hints: Iterable[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    fixture = task.get("fixture") if isinstance(task.get("fixture"), dict) else {}
    provider_values = _provider_hint_values(prior_value_hints)
    method = str(fetch.get("method") or "GET").upper()
    body_kind = canonical(fetch.get("body_kind") or "none")
    raw_body = fetch.get("body_values") if isinstance(fetch.get("body_values"), dict) else {}
    raw_headers = fetch.get("proof_headers") if isinstance(fetch.get("proof_headers"), dict) else {}
    body: dict[str, Any] = {}
    headers: dict[str, str] = {}
    residue: list[dict[str, str]] = []
    substitutions: list[dict[str, str]] = []

    sensitive_marker = "<redacted>"
    fixture_tokens = unique([
        fixture.get("tmdbId"), fixture.get("title"), fixture.get("year"),
        fixture.get("season"), fixture.get("episode"), *provider_values,
    ], 32)

    for key, raw in raw_body.items():
        value = str(raw if raw is not None else "")
        if value == sensitive_marker:
            residue.append({"location": f"body:{key}", "value": sensitive_marker})
            continue
        placeholder = _request_scalar_placeholder(key, raw, fixture, provider_values)
        if placeholder:
            body[str(key)] = placeholder
            substitutions.append({"location": f"body:{key}", "value": value, "placeholder": placeholder})
            continue
        if any(token and str(token) in value for token in fixture_tokens):
            residue.append({"location": f"body:{key}", "value": value[:160]})
            continue
        body[str(key)] = raw

    for key, raw in raw_headers.items():
        value = str(raw or "")
        if value == sensitive_marker:
            residue.append({"location": f"header:{key}", "value": sensitive_marker})
            continue
        replaced = value
        for body_key, raw_fixture in (
            ("tmdbId", fixture.get("tmdbId")),
            ("query", fixture.get("title")),
            ("season", fixture.get("season")),
            ("episode", fixture.get("episode")),
            ("year", fixture.get("year")),
        ):
            token = str(raw_fixture or "")
            if token and token in replaced:
                replaced = replaced.replace(token, "{" + body_key + "}")
        for provider_value in provider_values:
            if provider_value and provider_value in replaced:
                replaced = replaced.replace(provider_value, "{id}")
        if any(token and str(token) in replaced for token in fixture_tokens):
            residue.append({"location": f"header:{key}", "value": value[:160]})
            continue
        headers[str(key)] = replaced

    reusable = not residue
    spec: dict[str, Any] = {"method": method}
    if headers:
        spec["headers"] = headers
    if body_kind in {"json", "form"}:
        if raw_body and not body:
            reusable = False
        spec["bodyKind"] = body_kind
        spec["body"] = body
    elif body_kind not in {"none", "empty", ""}:
        reusable = False

    return (spec if reusable else None), {
        "requestSpecReusable": reusable,
        "requestSpecSubstitutions": substitutions,
        "requestSpecResidue": residue[:20],
    }


'''
    text = once(text, anchor, helpers + anchor, "insert-request-spec-helpers")

    old_meta = '''    meta = {
        "origin": f"{parsed.scheme}://{parsed.netloc}",
        "observedUrl": raw,
        "substitutions": substitutions,
        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),
        "reusable": reusable,
        "fixtureSpecificValues": unique(fixture_specific, 12),
        "dynamicQueryResidue": dynamic_query_residue[:12],
        "unresolvedOpaqueSegments": opaque[:12],
    }
    return (route if reusable else None), meta
'''
    new_meta = '''    request_spec, request_meta = derive_request_spec(fetch, task, prior_value_hints)
    meta = {
        "origin": f"{parsed.scheme}://{parsed.netloc}",
        "observedUrl": raw,
        "substitutions": substitutions,
        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),
        "reusable": reusable,
        "fixtureSpecificValues": unique(fixture_specific, 12),
        "dynamicQueryResidue": dynamic_query_residue[:12],
        "unresolvedOpaqueSegments": opaque[:12],
        "requestSpec": request_spec,
        **request_meta,
    }
    return (route if reusable else None), meta
'''
    text = once(text, old_meta, new_meta, "attach-request-spec-proof")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"request spec proof marker count={value.count(MARKER)}")
    for needle in (
        "def derive_request_spec(",
        '"requestSpec": request_spec',
        '"requestSpecReusable": reusable',
        'return "{id}"',
        'return "{query}"',
        'return "{season}"',
        'return "{episode}"',
    ):
        if needle not in value:
            raise AssertionError(f"request spec proof missing: {needle}")


def main() -> int:
    changed = patch()
    print(f"PROVIDER_ROUTE_PROOF_REQUEST_SPEC_V1_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
