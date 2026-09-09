#!/usr/bin/env python3
"""V21.8: safely replay deterministic composite search-body identity values.

Live provider traces can carry fixture-owned identity in one structured scalar,
for example a dotted title plus movie year or SxxExx. Proof V1 only abstracts
whole-value fields, so those deterministic values were rejected as fixture
residue and the exact live POST could not become executable DATA.

V21.8 adds only shared, exact decomposition rules:
- title words separated by dots + `.YEAR`;
- title words separated by dots + `.SxxExx`;
- dotted title alone.
Anything that does not exactly reconstruct from the fixture remains fail-closed.
Redacted/session/token fields remain residue and are never promoted.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_player_fallback_v21_7 as v217  # noqa: E402

PROOF = ROOT / "scripts" / "provider_route_proof.py"
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_COMPOSITE_REQUEST_TEMPLATE_V21_8"
PROOF_MARKER = "PROVIDER_ROUTE_PROOF_COMPOSITE_REQUEST_TEMPLATE_V21_8"
RECOVERY_MARKER = "ROUTE_RECOVERY_COMPOSITE_SEARCH_TEMPLATE_V21_8"
BASE_MARKER = "NIAKVIO_PROVIDER_BASE_COMPOSITE_REQUEST_TEMPLATE_V21_8"

patch_worker = v217.patch_worker
patch_materializer = v217.patch_materializer
validate_worker = v217.validate_worker
validate_materializer = v217.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def _function_section(text: str, start_marker: str, next_marker: str) -> tuple[int, int, str]:
    start = text.index(start_marker)
    end = text.index(next_marker, start)
    return start, end, text[start:end]


def patch_proof() -> bool:
    v217.patch_proof()
    text = PROOF.read_text(encoding="utf-8")
    if PROOF_MARKER in text:
        validate_proof(text)
        return False

    anchor = "def _request_scalar_placeholder(\n"
    helper = r'''# PROVIDER_ROUTE_PROOF_COMPOSITE_REQUEST_TEMPLATE_V21_8
def _request_dotted_title(raw: object) -> str:
    return re.sub(r"\s+", ".", str(raw or "").strip())


def _request_compact_identity(raw: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", canonical(raw))


def _request_composite_placeholder(
    key: object,
    raw_value: object,
    fixture: dict[str, Any],
) -> str | None:
    """Abstract only exact fixture-owned composite search scalars."""
    if canonical(key) not in BODY_TITLE_KEYS:
        return None
    value = str(raw_value if raw_value is not None else "").strip()
    title = str(fixture.get("title") or "").strip()
    if not value or not title:
        return None
    dotted = _request_dotted_title(title)
    year = str(fixture.get("year") or "").strip()
    season = str(fixture.get("season") or "").strip()
    episode = str(fixture.get("episode") or "").strip()

    if year and canonical(value) == canonical(f"{dotted}.{year}"):
        return "{queryDots}.{year}"
    if season and episode:
        try:
            episodic = f"{dotted}.S{int(season):02d}E{int(episode):02d}"
        except (TypeError, ValueError):
            episodic = ""
        if episodic and canonical(value) == canonical(episodic):
            return "{queryDots}.S{season2}E{episode2}"
    if dotted != title and canonical(value) == canonical(dotted):
        return "{queryDots}"
    return None


def _request_composite_related_to_fixture(
    key: object,
    raw_value: object,
    fixture: dict[str, Any],
) -> bool:
    """Fail closed on near-miss composite identity instead of freezing it."""
    if canonical(key) not in BODY_TITLE_KEYS:
        return False
    title = _request_compact_identity(fixture.get("title"))
    value = _request_compact_identity(raw_value)
    return bool(len(title) >= 4 and title in value)


'''
    text = _once(text, anchor, helper + anchor, "v21.8-proof-helper")

    # Patch only the canonical structured-body owner. Earlier V16/V20 migrations
    # can legitimately add lines around this assignment, so do not couple V21.8
    # to their exact surrounding block.
    start, end, section = _function_section(text, "def derive_request_spec(\n", "def derive_observed_route(\n")
    scalar = "        placeholder = _request_scalar_placeholder(key, raw, fixture, provider_values)\n"
    if section.count(scalar) != 1:
        raise AssertionError(f"v21.8-structured-scalar-anchor count={section.count(scalar)}")
    section = section.replace(
        scalar,
        scalar
        + "        if not placeholder:\n"
        + "            placeholder = _request_composite_placeholder(key, raw, fixture)\n",
        1,
    )
    residue_anchor = "        if any(token and str(token) in value for token in fixture_tokens):\n"
    if section.count(residue_anchor) != 1:
        raise AssertionError(f"v21.8-structured-residue-anchor count={section.count(residue_anchor)}")
    section = section.replace(
        residue_anchor,
        "        if _request_composite_related_to_fixture(key, raw, fixture):\n"
        "            residue.append({\"location\": f\"body:{key}\", \"value\": value[:160]})\n"
        "            continue\n"
        + residue_anchor,
        1,
    )
    text = text[:start] + section + text[end:]

    # V20.3 owns a second URL-encoded text-body path. Extend it too when present,
    # while preserving all of V20.4's existing title+season logic.
    if "def _urlencoded_text_body_spec(\n" in text:
        start, end, section = _function_section(text, "def _urlencoded_text_body_spec(\n", "def derive_request_spec(\n")
        scalar_text = "        placeholder = _request_scalar_placeholder(key, value, fixture, provider_values)\n"
        if section.count(scalar_text) == 1:
            insert_after = scalar_text
            if "            placeholder = _urlencoded_search_query_template(key, value, fixture)\n" in section:
                insert_after += (
                    "        if not placeholder:\n"
                    "            placeholder = _urlencoded_search_query_template(key, value, fixture)\n"
                )
            if section.count(insert_after) != 1:
                raise AssertionError("v21.8-urlencoded-composite predecessor ambiguous")
            section = section.replace(
                insert_after,
                insert_after
                + "        if not placeholder:\n"
                + "            placeholder = _request_composite_placeholder(key, value, fixture)\n",
                1,
            )
            text = text[:start] + section + text[end:]

    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def patch_recovery() -> bool:
    v217.patch_recovery()
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False

    start = text.index("def _record_has_search_query(row: dict[str, Any]) -> bool:\n")
    next_def = text.index("\ndef ", start + 5)
    section = text[start:next_def]
    old_route = '''    if "{query}" in str(row.get("route") or ""):
        return True
'''
    new_route = '''    route = str(row.get("route") or "")
    if any(marker in route for marker in ("{query}", "{queryDots}", "{query_dots}")):
        return True
'''
    section = _once(section, old_route, new_route, "v21.8-recovery-route-query")
    old_return = '''    return "{query}" in json.dumps(spec, ensure_ascii=False, sort_keys=True)
'''
    new_return = '''    serialized = json.dumps(spec, ensure_ascii=False, sort_keys=True)
    return any(marker in serialized for marker in ("{query}", "{queryDots}", "{query_dots}"))
'''
    section = _once(section, old_return, new_return, "v21.8-recovery-spec-query")
    section = "# ROUTE_RECOVERY_COMPOSITE_SEARCH_TEMPLATE_V21_8\n" + section
    text = text[:start] + section + text[next_def:]
    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_base() -> bool:
    v217.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False

    old_replacements = '''    query: values.query,
    title: values.query,
    id: values.providerId,
'''
    new_replacements = '''    query: values.query,
    title: values.query,
    queryDots: _text(values.query).trim().replace(/\\s+/g, "."),
    query_dots: _text(values.query).trim().replace(/\\s+/g, "."),
    year: values.year,
    season2: String(values.season == null ? "" : values.season).padStart(2, "0"),
    episode2: String(values.episode == null ? "" : values.episode).padStart(2, "0"),
    id: values.providerId,
'''
    text = _once(text, old_replacements, new_replacements, "v21.8-base-placeholder-expansion")

    # Structured search plans are the primary consumer. Keep year local to the
    # TMDB metadata already fetched for this exact request.
    start = text.index("async function _resolveSearchRequestPlan(meta, mediaType, season, episode) {")
    end = text.index("async function _resolveExternalIdentityPlan", start)
    section = text[start:end]
    section = _once(
        section,
        '''    imdbId: _text(meta.imdbId),
    media,
    season,
''',
        '''    imdbId: _text(meta.imdbId),
    media,
    year: _text(meta.year),
    season,
''',
        "v21.8-search-plan-year",
    )
    text = text[:start] + section + text[end:]

    marker_anchor = "function _recipeExpandScalar(value, values) {\n"
    text = _once(text, marker_anchor, f"/* {BASE_MARKER} */\n" + marker_anchor, "v21.8-base-marker")
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_proof(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        PROOF_MARKER,
        "def _request_composite_placeholder",
        "def _request_composite_related_to_fixture",
        'return "{queryDots}.{year}"',
        'return "{queryDots}.S{season2}E{episode2}"',
        "_request_composite_related_to_fixture(key, raw, fixture)",
        "_request_composite_placeholder(key, raw, fixture)",
    ):
        if needle not in value:
            raise AssertionError(f"V21.8 proof missing {needle}")


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        '"{queryDots}"',
        "return any(marker in serialized",
    ):
        if needle not in value:
            raise AssertionError(f"V21.8 recovery missing {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        'queryDots: _text(values.query).trim().replace(/\\s+/g, ".")',
        "year: values.year",
        'season2: String(values.season == null ? "" : values.season).padStart(2, "0")',
        'episode2: String(values.episode == null ? "" : values.episode).padStart(2, "0")',
    ):
        if needle not in value:
            raise AssertionError(f"V21.8 base missing {needle}")
    start = value.index("async function _resolveSearchRequestPlan(meta, mediaType, season, episode) {")
    end = value.index("async function _resolveExternalIdentityPlan", start)
    if "year: _text(meta.year)" not in value[start:end]:
        raise AssertionError("V21.8 search request plan does not carry TMDB year")

    # This migration must stay shared; fixture/provider literals are forbidden.
    section = value.split(f"/* {BASE_MARKER} */", 1)[1].split("function _recipeExpandObject", 1)[0].casefold()
    for token in ("animezey", "interstellar", "breaking bad", "movieblast", "cineby"):
        if token in section:
            raise AssertionError(f"V21.8 provider/fixture-specific token leaked: {token}")


def main() -> int:
    patch_worker()
    proof_changed = patch_proof()
    recovery_changed = patch_recovery()
    patch_materializer()
    base_changed = patch_base()
    validate_worker(); validate_proof(); validate_recovery(); validate_materializer(); validate_base()
    changed = proof_changed or recovery_changed or base_changed
    print(
        f"PROVIDER_COMPOSITE_REQUEST_TEMPLATE_V21_8_OK changed={str(changed).lower()} "
        "dotted_title=1 movie_year=1 episodic_sxxexx=1 near_miss_fail_closed=1 "
        "redacted_fields_fail_closed=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
