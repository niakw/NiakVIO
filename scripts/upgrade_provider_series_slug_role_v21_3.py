#!/usr/bin/env python3
"""V21.3: preserve semantic series-slug role across response-value replay.

A series detail response may expose episode URLs whose last path segment also
looks title-related. V20.5 correctly learns response values, but blindly replacing
providerSlug can turn a stable series slug into an episode slug and then expand a
later route such as ``/episode/{slug}-{season}-episode-{episode}/`` twice.

This migration keeps response learning, but preserves a non-episodic series slug
when an episodic candidate would be consumed by a later route that explicitly
adds season/episode coordinates. It is media/route-shape driven and contains no
provider names, hosts or fixture-specific values.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_media_identity_guard_v21_2 as v212  # noqa: E402

BASE = v212.BASE
MARKER = "NIAKVIO_PROVIDER_SERIES_SLUG_ROLE_V21_3"

patch_worker = v212.patch_worker
patch_proof = v212.patch_proof
patch_recovery = v212.patch_recovery
patch_materializer = v212.patch_materializer
validate_worker = v212.validate_worker
validate_proof = v212.validate_proof
validate_recovery = v212.validate_recovery
validate_materializer = v212.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    v212.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    helper_anchor = "function _spv211ProviderIdAllowed(key, rawValue) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_SERIES_SLUG_ROLE_V21_3 */
function _spv213SlugCarriesEpisodeIdentity(value) {
  const slug = _text(value).toLowerCase();
  if (!slug) return false;
  return /(?:^|[-_.])(?:s\d{1,3}[-_.]?e\d{1,4}|(?:season|saison)[-_.]?\d{1,3}|(?:episode|ep)[-_.]?\d{1,4}|\d{1,3}[-_.]episode[-_.]\d{1,4})(?:$|[-_.])/i.test(slug);
}
function _spv213StableSeriesSlug(currentSlug, candidateSlug, mediaType, valueSteps, completedSteps, currentStepIndex) {
  const current = _text(currentSlug).trim();
  const candidate = _text(candidateSlug).trim();
  if (!candidate || !current || candidate === current) return candidate || current;
  const lane = _text(mediaType).trim().toLowerCase();
  if (lane !== "tv" && lane !== "anime") return candidate;
  if (_spv213SlugCarriesEpisodeIdentity(current) || !_spv213SlugCarriesEpisodeIdentity(candidate)) return candidate;

  const steps = Array.isArray(valueSteps) ? valueSteps : [];
  const done = completedSteps && typeof completedSteps.has === "function" ? completedSteps : null;
  let laterNeedsSeriesCoordinates = false;
  for (let index = 0; index < steps.length; index += 1) {
    if (index === Number(currentStepIndex) || (done && done.has(index))) continue;
    const route = _text(steps[index] && steps[index].route);
    if (!/\{slug\}/i.test(route)) continue;
    if (/\{(?:season|episode)\}/i.test(route)) {
      laterNeedsSeriesCoordinates = true;
      break;
    }
  }
  return laterNeedsSeriesCoordinates ? current : candidate;
}
'''
    text = _once(text, helper_anchor, helper + helper_anchor, "v21.3-series-slug-helper")

    old_response = '''          const nextProviderValues = _spv205StrictProviderValues(
            payload.value,
            payload.base || stepUrl,
            meta,
            season,
            mediaType
          ) || { id: "", slug: "" };
          if (nextProviderValues.id || nextProviderValues.slug) {
'''
    new_response = '''          const nextProviderValues = _spv205StrictProviderValues(
            payload.value,
            payload.base || stepUrl,
            meta,
            season,
            mediaType
          ) || { id: "", slug: "" };
          if (nextProviderValues.slug) {
            nextProviderValues.slug = _spv213StableSeriesSlug(
              values.providerSlug,
              nextProviderValues.slug,
              mediaType,
              valueSteps,
              completedSteps,
              stepIndex
            );
          }
          if (nextProviderValues.id || nextProviderValues.slug) {
'''
    text = _once(text, old_response, new_response, "v21.3-response-slug-role")

    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v212.validate_base(value)
    for needle in (
        MARKER,
        "function _spv213SlugCarriesEpisodeIdentity(value)",
        "function _spv213StableSeriesSlug(currentSlug, candidateSlug, mediaType, valueSteps, completedSteps, currentStepIndex)",
        "nextProviderValues.slug = _spv213StableSeriesSlug(",
        "providerSlug: nextProviderValues.slug || values.providerSlug",
    ):
        if needle not in value:
            raise AssertionError(f"V21.3 ProviderBase missing {needle}")
    runtime = value[value.index(MARKER): value.index("async function _resolveSearchRequestPlan", value.index(MARKER))]
    lowered = runtime.casefold()
    for forbidden in ("jujutsu", "animesama", "animevostfr", "french-manga", "purstream"):
        if forbidden in lowered:
            raise AssertionError(f"V21.3 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_SERIES_SLUG_ROLE_V21_3_OK changed={str(changed).lower()} "
        "series_slug_role_preserved=1 episode_slug_handoff_still_allowed=1 "
        "route_shape_driven=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
