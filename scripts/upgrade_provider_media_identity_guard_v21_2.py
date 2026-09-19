#!/usr/bin/env python3
"""V21.2: make the V21 media identity guard self-contained.

V21.1 correctly made provider identity media-aware, but its candidate scorer reused
_slug() and _spv4Titles() from the wider ProviderBase scope. Historical V20.5
contract tests deliberately execute the strict response-value resolver in
isolation, so that hidden dependency broke migration-chain compatibility.

V21.2 keeps the V21.1 policy unchanged and moves title normalization / alias
collection behind V21-owned helpers. No provider, host, fixture title, or
provider-specific rule is introduced.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_media_identity_guard_v21_1 as v211  # noqa: E402

BASE = v211.BASE
MARKER = "NIAKVIO_PROVIDER_MEDIA_IDENTITY_GUARD_V21_2"

patch_worker = v211.patch_worker
patch_proof = v211.patch_proof
patch_recovery = v211.patch_recovery
patch_materializer = v211.patch_materializer
validate_worker = v211.validate_worker
validate_proof = v211.validate_proof
validate_recovery = v211.validate_recovery
validate_materializer = v211.validate_materializer


def _once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    v211.patch_base()
    text = BASE.read_text(encoding="utf-8")
    if MARKER in text:
        validate_base(text)
        return False

    old = r'''function _spv211RegexEscape(value) {
  return _text(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function _spv211CandidateIdentityScore(title, href, meta, mediaType, season) {
  const actual = _slug(title);
  if (!actual) return 0;
  const expected = _spv4Titles(meta).map(_slug).filter(Boolean);
'''
    new = r'''function _spv211RegexEscape(value) {
  return _text(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
/* NIAKVIO_PROVIDER_MEDIA_IDENTITY_GUARD_V21_2 */
function _spv212Slug(value) {
  return _text(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
function _spv212Titles(meta) {
  const rows = [meta && meta.title, ...((meta && Array.isArray(meta.aliases)) ? meta.aliases : [])];
  const out = [];
  const seen = new Set();
  for (const row of rows.slice(0, 8)) {
    const value = _text(row).trim();
    const key = _spv212Slug(value);
    if (!value || !key || seen.has(key)) continue;
    seen.add(key);
    out.push(value);
  }
  return out.slice(0, 4);
}
function _spv211CandidateIdentityScore(title, href, meta, mediaType, season) {
  const actual = _spv212Slug(title);
  if (!actual) return 0;
  const expected = _spv212Titles(meta).map(_spv212Slug).filter(Boolean);
'''
    text = _once(text, old, new, "v21.2-self-contained-title-identity")
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    v211.validate_base(value)
    for needle in (
        MARKER,
        "function _spv212Slug(value)",
        "function _spv212Titles(meta)",
        "const actual = _spv212Slug(title);",
        "const expected = _spv212Titles(meta).map(_spv212Slug).filter(Boolean);",
    ):
        if needle not in value:
            raise AssertionError(f"V21.2 ProviderBase missing {needle}")
    scorer_start = value.index("function _spv211CandidateIdentityScore")
    scorer_end = value.index("function _spv211ProviderIdAllowed", scorer_start)
    scorer = value[scorer_start:scorer_end]
    for forbidden_dependency in ("_slug(", "_spv4Titles("):
        if forbidden_dependency in scorer:
            raise AssertionError(f"V21.2 scorer leaked legacy dependency {forbidden_dependency}")
    runtime = value[value.index(MARKER): value.index("async function _resolveSearchRequestPlan", value.index(MARKER))]
    lowered = runtime.casefold()
    for forbidden in ("jujutsu", "animesama", "animevostfr", "french-manga", "purstream"):
        if forbidden in lowered:
            raise AssertionError(f"V21.2 provider/fixture-specific token leaked: {forbidden}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_MEDIA_IDENTITY_GUARD_V21_2_OK changed={str(changed).lower()} "
        "self_contained_title_identity=1 legacy_v20_5_compatible=1 "
        "media_policy_unchanged=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
