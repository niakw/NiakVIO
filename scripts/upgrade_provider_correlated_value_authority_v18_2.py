#!/usr/bin/env python3
"""Provider Value Authority V18.2.

V18 projected proven search -> provider-value -> correlated-route plans and wired
them into the generic getStreams path. V16, however, owns the canonical proof
execution path used by the final ProviderBase wrapper and may call _spv4GetStreams
directly. That made a correctly materialized providerValuePlan unreachable.

V18.2 gives the correlated plan the same proof-owned authority in _spv4GetStreams:
1. proven provider-value correlated plan,
2. proven API recipe,
3. proven structured search request plan,
4. source-family traversal and existing fallbacks.

No provider ids, hostnames, fixtures or route literals are encoded here.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_CORRELATED_VALUE_AUTHORITY_V18_2"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    for required in (
        "NIAKVIO_PROVIDER_EXECUTION_AUTHORITY_V16",
        "NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18",
        "async function _resolveProviderValuePlan",
    ):
        if required not in text:
            raise AssertionError(f"V18.2 requires {required}")

    old_flags = '''const hasProofRecipe = !!NIAKVIO_PROVIDER_MODEL.apiRecipe;
const hasProofSearch = Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length > 0;
let proofMeta = null;
if (hasProofRecipe || hasProofSearch) proofMeta = await _tmdb(tmdbId, type);
'''
    new_flags = '''/* NIAKVIO_PROVIDER_CORRELATED_VALUE_AUTHORITY_V18_2 */
const hasProofValue = Array.isArray(NIAKVIO_PROVIDER_MODEL.providerValuePlan) && NIAKVIO_PROVIDER_MODEL.providerValuePlan.length > 0;
const hasProofRecipe = !!NIAKVIO_PROVIDER_MODEL.apiRecipe;
const hasProofSearch = Array.isArray(NIAKVIO_PROVIDER_MODEL.searchRequestPlan) && NIAKVIO_PROVIDER_MODEL.searchRequestPlan.length > 0;
let proofMeta = null;
if (hasProofValue || hasProofRecipe || hasProofSearch) proofMeta = await _tmdb(tmdbId, type);
if (hasProofValue && proofMeta && proofMeta.title) {
  const valuePrimary = await _resolveProviderValuePlan(proofMeta, type, season, episode);
  if (Array.isArray(valuePrimary) && valuePrimary.length) return valuePrimary;
}
'''
    text = once(text, old_flags, new_flags, "v18.2-proof-value-authority")

    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.2 marker count={value.count(MARKER)}")
    for needle in (
        "const hasProofValue = Array.isArray(NIAKVIO_PROVIDER_MODEL.providerValuePlan)",
        "if (hasProofValue || hasProofRecipe || hasProofSearch) proofMeta = await _tmdb(tmdbId, type);",
        "const valuePrimary = await _resolveProviderValuePlan(proofMeta, type, season, episode);",
        "if (Array.isArray(valuePrimary) && valuePrimary.length) return valuePrimary;",
    ):
        if needle not in value:
            raise AssertionError(f"V18.2 missing {needle}")

    start = value.index(MARKER)
    end = value.find('if (family === "stremio-json")', start)
    if end < 0:
        raise AssertionError("V18.2 cannot locate source-family boundary")
    prefix = value[start:end]
    value_pos = prefix.find("_resolveProviderValuePlan")
    recipe_pos = prefix.find("_resolveApiRecipe")
    search_pos = prefix.find("_resolveSearchRequestPlan")
    if min(value_pos, recipe_pos, search_pos) < 0:
        raise AssertionError("V18.2 proof authority functions are incomplete")
    if not (value_pos < recipe_pos < search_pos):
        raise AssertionError("V18.2 proof order must be provider-value -> recipe -> search")

    lower = value.lower()
    for token in ("animekai", "movies4u", "frenchstream", "mugiwara"):
        if token in lower:
            raise AssertionError(f"V18.2 introduced provider-specific token: {token}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_CORRELATED_VALUE_AUTHORITY_V18_2_OK changed={str(changed).lower()} "
        "provider_value_first=1 recipe_second=1 search_third=1 family_after=1 "
        "provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
