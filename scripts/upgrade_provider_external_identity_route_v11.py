#!/usr/bin/env python3
"""External identity route V11: prove and replay IMDb-derived provider paths.

Some providers obtain an IMDb identity from TMDB/metadata and then address their
catalogue by `/series/tt...`. Prior route proof treated those literals as static
path text, so reconstruction could freeze one fixture's IMDb into DATA.

V11 is fail-closed and provider-agnostic:
- the proof worker exposes only IMDb-shaped values under explicit imdb keys;
- Python keeps external identity hints separate from provider-internal IDs;
- an observed tt... segment is reusable only when a prior response proved it,
  becoming `{imdbId}`; otherwise the route is rejected as fixture residue;
- ProviderBase recognizes/expands `{imdbId}` and source-plan detail discovery can
  execute an IMDb-addressed detail route directly from Core TMDB metadata.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "provider_worker.cjs"
PROOF = ROOT / "scripts" / "provider_route_proof.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_EXTERNAL_IDENTITY_ROUTE_V11"
WORKER_MARKER = "NUVIO_PROVIDER_WORKER_EXTERNAL_IDENTITY_HINT_V11"
PROOF_MARKER = "PROVIDER_ROUTE_PROOF_EXTERNAL_IDENTITY_V11"
BASE_MARKER = "NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_worker() -> bool:
    text = WORKER.read_text(encoding="utf-8")
    if WORKER_MARKER in text:
        validate_worker(text)
        return False
    if "NUVIO_PROVIDER_WORKER_ROUTE_PROOF_V1" not in text:
        raise AssertionError("external identity V11 requires route-proof worker first")
    old = '''  'movie_id', 'movieid', 'series_id', 'seriesid', 'show_id', 'showid', 'slug',
]);'''
    new = '''  'movie_id', 'movieid', 'series_id', 'seriesid', 'show_id', 'showid', 'slug',
  // NUVIO_PROVIDER_WORKER_EXTERNAL_IDENTITY_HINT_V11
  'imdb', 'imdb_id', 'imdbid',
]);'''
    text = once(text, old, new, "worker-imdb-hint-keys")
    WORKER.write_text(text, encoding="utf-8")
    validate_worker(text)
    return True


def patch_proof() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if PROOF_MARKER in text:
        validate_proof(text)
        return False

    text = once(
        text,
        '''CONTENT_IDENTITY_QUERY_KEYS = {
    "imdb", "imdbid", "imdb_id", "year", "releaseyear", "release_year",
''',
        '''# PROVIDER_ROUTE_PROOF_EXTERNAL_IDENTITY_V11
EXTERNAL_IDENTITY_HINT_KEYS = {"imdb", "imdbid", "imdb_id"}
CONTENT_IDENTITY_QUERY_KEYS = {
    "imdb", "imdbid", "imdb_id", "year", "releaseyear", "release_year",
''',
        "proof-external-id-keys",
    )

    anchor = "def response_value_hints(fetch: dict[str, Any]) -> list[dict[str, str]]:\n"
    helper = '''def _external_identity_hint_values(\n    prior_value_hints: Iterable[dict[str, Any]] | None,\n) -> set[str]:\n    out: set[str] = set()\n    for row in prior_value_hints or []:\n        if not isinstance(row, dict):\n            continue\n        key = canonical(row.get("key"))\n        value = str(row.get("value") or "").strip()\n        if key not in EXTERNAL_IDENTITY_HINT_KEYS:\n            continue\n        if re.fullmatch(r"tt\\d{7,10}", value, re.I):\n            out.add(value)\n    return out\n\n\n'''
    text = once(text, anchor, helper + anchor, "proof-external-hint-helper")
    text = once(
        text,
        '''        if key in PROVIDER_VALUE_KEYS and value and len(value) <= 160:
            out.append({"key": key, "value": value})
''',
        '''        if (key in PROVIDER_VALUE_KEYS or key in EXTERNAL_IDENTITY_HINT_KEYS) and value and len(value) <= 160:
            if key in EXTERNAL_IDENTITY_HINT_KEYS and not re.fullmatch(r"tt\\d{7,10}", value, re.I):
                continue
            out.append({"key": key, "value": value})
''',
        "proof-retain-external-hints",
    )

    text = once(
        text,
        '''    provider_values = _provider_hint_values(prior_value_hints)

    tmdb = str(fixture.get("tmdbId") or "").strip()
''',
        '''    provider_values = _provider_hint_values(prior_value_hints)
    imdb_values = _external_identity_hint_values(prior_value_hints)

    tmdb = str(fixture.get("tmdbId") or "").strip()
''',
        "proof-load-imdb-values",
    )
    text = once(
        text,
        '''        if tmdb and decoded == tmdb:
            placeholder = "{tmdbId}"
        elif decoded in provider_values:
            placeholder = "{id}"
''',
        '''        if tmdb and decoded == tmdb:
            placeholder = "{tmdbId}"
        elif decoded in imdb_values:
            placeholder = "{imdbId}"
        elif decoded in provider_values:
            placeholder = "{id}"
''',
        "proof-imdb-path-placeholder",
    )
    text = once(
        text,
        '''        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:
            placeholder = "{id}"
''',
        '''        elif value in imdb_values and key_l in EXTERNAL_IDENTITY_HINT_KEYS:
            placeholder = "{imdbId}"
        elif value in provider_values and key_l in PROVIDER_VALUE_KEYS:
            placeholder = "{id}"
''',
        "proof-imdb-query-placeholder",
    )
    text = once(
        text,
        '''    opaque = [segment for segment in unresolved_segments if re.fullmatch(r"\\d{2,}|[A-Fa-f0-9]{12,}|[A-Za-z0-9_-]{18,}", segment)]
''',
        '''    opaque = [segment for segment in unresolved_segments if re.fullmatch(r"\\d{2,}|tt\\d{7,10}|[A-Fa-f0-9]{12,}|[A-Za-z0-9_-]{18,}", segment, re.I)]
''',
        "proof-imdb-literal-fail-closed",
    )
    text = once(
        text,
        '''        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),
        "reusable": reusable,
''',
        '''        "providerValueCorrelation": bool(provider_values and any(row.get("placeholder") == "{id}" for row in substitutions)),
        "externalIdentityCorrelation": bool(imdb_values and any(row.get("placeholder") == "{imdbId}" for row in substitutions)),
        "reusable": reusable,
''',
        "proof-external-correlation",
    )
    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_BASE_SOURCE_PLAN_V4" not in text:
        raise AssertionError("external identity V11 requires Source Plan V4")

    text = once(
        text,
        '''    if any(token in route for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}")):
''',
        '''    if any(token in route for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}", "{imdbid}", "{imdb_id}")):
''',
        "base-runtime-route-imdb-authority",
    )
    text = once(
        text,
        '''  const id = _text(meta && meta.tmdbId);
  const title = _text(meta && meta.title);
''',
        '''  const id = _text(meta && meta.tmdbId);
  const imdbId = _text(meta && meta.imdbId);
  const title = _text(meta && meta.title);
''',
        "base-learned-imdb-value",
    )
    text = once(
        text,
        '''  route = route.replace(/\\{tmdb_?id\\}/gi, encodeURIComponent(id));
  // {id} has no universal meaning across providers.
''',
        '''  route = route.replace(/\\{tmdb_?id\\}/gi, encodeURIComponent(id));
  route = route.replace(/\\{imdb_?id\\}/gi, encodeURIComponent(imdbId));
  // {id} has no universal meaning across providers.
''',
        "base-expand-imdb-learned-route",
    )
    text = once(
        text,
        '''  if (/\\{(?:tmdb_?id|id|slug|title)\\}/i.test(value) || /\\/(?:title|movie|film|series|tv|show|watch|media)(?:[/?#]|$)/i.test(value)) return "detail";
''',
        '''  if (/\\{(?:tmdb_?id|imdb_?id|id|slug|title)\\}/i.test(value) || /\\/(?:title|movie|film|series|tv|show|watch|media)(?:[/?#]|$)/i.test(value)) return "detail";
''',
        "base-route-kind-imdb",
    )

    # Source-plan detail discovery can execute an explicit external-ID route even
    # when the provider has no title search endpoint.
    anchor = '''  // Slug-driven catalogues (Sekai and similar) do not expose a search endpoint.
  // Generate only deterministic title slugs from Core metadata.
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
'''
    replacement = '''  // NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11
  // External-ID catalogues may have no title search endpoint. Core already owns
  // TMDB -> IMDb metadata resolution, so execute only routes whose `{imdbId}`
  // placeholder was proof-derived from a prior response.
  const detailRoutes = _spv4Routes().filter(route => _spv4IsDetailRoute(route, family));
  if (meta && meta.imdbId) {
    for (const route of detailRoutes) {
      if (!/\\{imdb_?id\\}/i.test(route)) continue;
      out.push(..._spv4Expand(route, meta, {}, mediaType, season, episode));
    }
  }
  // Slug-driven catalogues (Sekai and similar) do not expose a search endpoint.
  // Generate only deterministic title slugs from Core metadata.
'''
    text = once(text, anchor, replacement, "base-external-id-detail-plan")
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_worker(text: str | None = None) -> None:
    value = text if text is not None else WORKER.read_text(encoding="utf-8")
    for needle in (WORKER_MARKER, "'imdb', 'imdb_id', 'imdbid'"):
        if needle not in value:
            raise AssertionError(f"V11 worker missing: {needle}")


def validate_proof(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        PROOF_MARKER,
        "EXTERNAL_IDENTITY_HINT_KEYS",
        "def _external_identity_hint_values",
        'placeholder = "{imdbId}"',
        '"externalIdentityCorrelation"',
        'tt\\d{7,10}',
    ):
        if needle not in value:
            raise AssertionError(f"V11 proof missing: {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        'const imdbId = _text(meta && meta.imdbId)',
        "imdb_?id",
        "meta && meta.imdbId",
        "External-ID catalogues may have no title search endpoint",
    ):
        if needle not in value:
            raise AssertionError(f"V11 ProviderBase missing: {needle}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_base()
    validate_worker()
    validate_proof()
    validate_base()
    print(
        f"PROVIDER_EXTERNAL_IDENTITY_ROUTE_V11_OK changed={str(changed).lower()} "
        "imdb_hint=1 provider_id_separation=1 literal_imdb_fail_closed=1 "
        "imdb_placeholder=1 source_plan_external_id=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
