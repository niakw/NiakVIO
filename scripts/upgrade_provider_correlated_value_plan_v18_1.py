#!/usr/bin/env python3
"""Provider Value Plan V18.1: accept provider-native slug identities.

Some structured search APIs identify the matched catalogue row with a slug rather
than a numeric id. Route recovery already normalizes the later request to {id};
V18.1 completes the runtime identity bridge by accepting slug-shaped fields only
after the same strict title score and bounded safe-character validation as ids.

This is a data-shape capability, not a provider or host exception.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_CORRELATED_VALUE_PLAN_V18_1"


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
    if "NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18" not in text:
        raise AssertionError("V18.1 requires V18")

    old_keys = 'for (const key of ["id","ID","_id","media_id","post_id","anime_id","movie_id","series_id","show_id"]) {'
    new_keys = '/* NIAKVIO_PROVIDER_CORRELATED_VALUE_PLAN_V18_1 */\n    for (const key of ["id","ID","_id","media_id","post_id","anime_id","movie_id","series_id","show_id","slug","provider_slug","seo_slug"]) {'
    text = once(text, old_keys, new_keys, "v18.1-json-provider-slug")

    old_attr = r'/\bdata-(?:id|post-id|media-id|anime-id|movie-id|series-id|show-id)\s*=\s*["\']?([A-Za-z0-9._~-]{1,160})/i'
    new_attr = r'/\bdata-(?:id|post-id|media-id|anime-id|movie-id|series-id|show-id|slug|provider-slug|seo-slug)\s*=\s*["\']?([A-Za-z0-9._~-]{1,160})/i'
    if text.count(old_attr) != 2:
        raise AssertionError(f"v18.1-html-provider-slug expected two anchors, got {text.count(old_attr)}")
    text = text.replace(old_attr, new_attr)

    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.1 marker count={value.count(MARKER)}")
    for needle in (
        '"slug","provider_slug","seo_slug"',
        "provider-slug|seo-slug",
        ".filter(item => item.score >= 90)",
        "/^[A-Za-z0-9._~-]+$/.test(value)",
    ):
        if needle not in value:
            raise AssertionError(f"V18.1 missing {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_CORRELATED_VALUE_PLAN_V18_1_OK changed={str(changed).lower()} "
        "scored_slug_identity=1 bounded_charset=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
