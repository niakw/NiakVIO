#!/usr/bin/env python3
"""Provider Value Plan V18.1: select provider-native JSON identities deterministically.

A positive structured search response can expose several labels plus one provider
id/slug. Selection must score every known label, require a strong identity match,
and then keep the highest-scoring row that also carries a bounded safe identity.

The implementation intentionally avoids spread-call/first-label shortcuts so the
same deterministic loop works across the supported JavaScript runtimes. No
provider ids, hosts, routes or fixture titles are encoded.
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

    old = r'''function _spv18ProviderIdFromJson(value, meta) {
  const rows = _spv4JsonRows(value, [])
    .map(row => ({
      row,
      score: _spv4TitleScore(
        _spv4Scalar(row.title) || _spv4Scalar(row.name) ||
        _spv4Scalar(row.original_title) || _spv4Scalar(row.post_title) ||
        _spv4Scalar(row.label) || "",
        meta
      )
    }))
    .filter(item => item.score >= 90)
    .sort((a, b) => b.score - a.score)
    .slice(0, 12);
  for (const item of rows) {
    const row = item.row || {};
    for (const key of ["id","ID","_id","media_id","post_id","anime_id","movie_id","series_id","show_id"]) {
      const value = _spv4Scalar(row[key]);
      if (value && value.length <= 160 && /^[A-Za-z0-9._~-]+$/.test(value)) return value;
    }
  }
  return "";
}
'''
    new = r'''function _spv18ProviderIdFromJson(value, meta) {
  /* NIAKVIO_PROVIDER_CORRELATED_VALUE_PLAN_V18_1 */
  const labelKeys = [
    "title","name","original_title","post_title","label","anime",
    "movie","series","show","matched","display_name","displayName"
  ];
  const identityKeys = [
    "id","ID","_id","media_id","post_id","anime_id","movie_id",
    "series_id","show_id","slug","provider_slug","seo_slug"
  ];
  let bestScore = -1;
  let bestIdentity = "";
  const rows = _spv4JsonRows(value, []).slice(0, 300);
  for (const row of rows) {
    if (!row || typeof row !== "object") continue;
    let rowScore = 0;
    for (const key of labelKeys) {
      const label = _spv4Scalar(row[key]);
      if (!label) continue;
      rowScore = Math.max(rowScore, _spv4TitleScore(label, meta));
    }
    if (rowScore < 90) continue;
    let identity = "";
    for (const key of identityKeys) {
      const candidate = _spv4Scalar(row[key]);
      if (candidate && candidate.length <= 160 && /^[A-Za-z0-9._~-]+$/.test(candidate)) {
        identity = candidate;
        break;
      }
    }
    if (!identity) continue;
    if (rowScore > bestScore) {
      bestScore = rowScore;
      bestIdentity = identity;
    }
  }
  return bestIdentity;
}
'''
    text = once(text, old, new, "v18.1-json-provider-identity-selector")
    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.1 marker count={value.count(MARKER)}")
    for needle in (
        '"anime",',
        '"matched",',
        '"slug","provider_slug","seo_slug"',
        "const rows = _spv4JsonRows(value, []).slice(0, 300);",
        "rowScore = Math.max(rowScore, _spv4TitleScore(label, meta));",
        "if (rowScore < 90) continue;",
        "/^[A-Za-z0-9._~-]+$/.test(candidate)",
        "return bestIdentity;",
    ):
        if needle not in value:
            raise AssertionError(f"V18.1 missing {needle}")
    function_start = value.index("function _spv18ProviderIdFromJson")
    function_end = value.index("function _spv18ProviderIdFromHtml", function_start)
    function = value[function_start:function_end]
    if "..." in function:
        raise AssertionError("V18.1 identity selector must not use spread syntax")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_CORRELATED_VALUE_PLAN_V18_1_OK changed={str(changed).lower()} "
        "scored_json_slug_identity=1 deterministic_best_row=1 bounded_charset=1 "
        "spread_calls=0 html_slug_inference=0 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
