#!/usr/bin/env python3
"""V21.10: require semantic movie-title equivalence before catalogue selection.

A partial title overlap is useful for ranking search candidates but is not enough to
prove movie identity.  In particular, a result such as "The Science of Interstellar"
must never be accepted for "Interstellar" merely because the expected title is a
substring.  This upgrade remains provider-agnostic: it allows only exact TMDB title
or alias identity plus bounded presentation noise (year, quality, language, generic
watch/streaming labels).  Extra semantic words fail closed before a provider id/slug
can become executable.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_MOVIE_CATALOGUE_IDENTITY_V21_10"

HELPER = r'''/* NIAKVIO_PROVIDER_MOVIE_CATALOGUE_IDENTITY_V21_10 */
function _spv211MovieCatalogueEquivalent(actual, expected, meta) {
  const wantedYear = Number(meta && (meta.year || meta.releaseYear || meta.release_year));
  const noise = new Set([
    "stream", "streaming", "watch", "regarder", "online", "gratuit", "free",
    "vf", "vff", "vfq", "vostfr", "vo", "multi", "french", "francais",
    "hd", "fhd", "fullhd", "uhd", "4k", "2160p", "1440p", "1080p", "720p"
  ]);
  function presentationOnly(value) {
    const parts = _text(value).split("-").filter(Boolean);
    if (!parts.length) return false;
    return parts.every(part => {
      if (noise.has(part)) return true;
      if (/^(?:19|20)\d{2}$/.test(part)) {
        return Number.isFinite(wantedYear) && wantedYear > 1800 && Number(part) === wantedYear;
      }
      return false;
    });
  }
  for (const wanted of expected) {
    if (!wanted) continue;
    if (actual === wanted) return true;
    if (actual.startsWith(wanted + "-") && presentationOnly(actual.slice(wanted.length + 1))) return true;
    if (actual.endsWith("-" + wanted) && presentationOnly(actual.slice(0, -(wanted.length + 1)))) return true;
  }
  return false;
}
'''


def patch() -> bool:
    text = BASE.read_text(encoding="utf-8")
    changed = False

    if MARKER not in text:
        anchor = "function _spv211CandidateIdentityScore(title, href, meta, mediaType, season) {\n"
        if text.count(anchor) != 1:
            raise AssertionError(f"movie identity scorer anchor count={text.count(anchor)}")
        text = text.replace(anchor, HELPER + anchor, 1)
        changed = True

    guard = '  if (lane === "movie") {\n'
    strict_guard = (
        '  if (lane === "movie") {\n'
        '    if (!exact && !_spv211MovieCatalogueEquivalent(actual, expected, meta)) return -10000;\n'
    )
    if strict_guard not in text:
        if text.count(guard) != 1:
            raise AssertionError(f"movie lane anchor count={text.count(guard)}")
        text = text.replace(guard, strict_guard, 1)
        changed = True

    if changed:
        BASE.write_text(text, encoding="utf-8")
    validate(text)
    return changed


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    required = (
        MARKER,
        "function _spv211MovieCatalogueEquivalent(actual, expected, meta)",
        "if (!exact && !_spv211MovieCatalogueEquivalent(actual, expected, meta)) return -10000;",
        'actual.startsWith(wanted + "-")',
        'actual.endsWith("-" + wanted)',
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"movie catalogue identity missing {needle}")
    window = value[value.index(MARKER):value.index("function _spv211ProviderIdAllowed", value.index(MARKER))]
    lowered = window.casefold()
    for forbidden in ("streamzo", "interstellar", "papadustream", "vidrock", "mugiwara"):
        if forbidden in lowered:
            raise AssertionError(f"provider/fixture-specific token leaked into generic movie identity: {forbidden}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_MOVIE_CATALOGUE_IDENTITY_V21_10_OK "
        f"changed={str(changed).lower()} exact_or_presentation_noise_only=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
