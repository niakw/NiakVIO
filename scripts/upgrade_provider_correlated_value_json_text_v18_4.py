#!/usr/bin/env python3
"""Provider Value Plan V18.4: parse JSON carried as textual HTTP payloads.

The generic request layer may return a response body as a string even when the
remote endpoint is application/json. V18 previously selected the identity parser
only from the JavaScript runtime type, which sent such structured search results
to the HTML parser and silently lost provider ids/slugs.

V18.4 first attempts bounded JSON decoding for string payloads, reuses the strict
V18.1 JSON identity scorer, then falls back to HTML identity extraction. This is a
response-shape capability: no provider id, host, route or fixture is encoded.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4"


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
        "NIAKVIO_PROVIDER_BASE_CORRELATED_VALUE_PLAN_V18",
        "NIAKVIO_PROVIDER_CORRELATED_VALUE_PLAN_V18_1",
        "NIAKVIO_PROVIDER_CORRELATED_VALUE_AUTHORITY_V18_2",
    ):
        if required not in text:
            raise AssertionError(f"V18.4 requires {required}")

    old = '''      const providerId = typeof searchPayload.value === "string"
        ? _spv18ProviderIdFromHtml(searchPayload.value, meta)
        : _spv18ProviderIdFromJson(searchPayload.value, meta);
      if (!providerId) continue;
'''
    new = '''      /* NIAKVIO_PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4 */
      let providerId = "";
      if (typeof searchPayload.value === "string") {
        const rawSearchValue = _text(searchPayload.value).trim();
        if (rawSearchValue && rawSearchValue.length <= 4 * 1024 * 1024 && /^[\\[{]/.test(rawSearchValue)) {
          try {
            providerId = _spv18ProviderIdFromJson(JSON.parse(rawSearchValue), meta);
          } catch (_) {}
        }
        if (!providerId) providerId = _spv18ProviderIdFromHtml(rawSearchValue, meta);
      } else {
        providerId = _spv18ProviderIdFromJson(searchPayload.value, meta);
      }
      if (!providerId) continue;
'''
    text = once(text, old, new, "v18.4-json-text-identity-bridge")
    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.4 marker count={value.count(MARKER)}")
    for needle in (
        "const rawSearchValue = _text(searchPayload.value).trim();",
        "rawSearchValue.length <= 4 * 1024 * 1024",
        "_spv18ProviderIdFromJson(JSON.parse(rawSearchValue), meta)",
        "if (!providerId) providerId = _spv18ProviderIdFromHtml(rawSearchValue, meta);",
        "providerId = _spv18ProviderIdFromJson(searchPayload.value, meta);",
    ):
        if needle not in value:
            raise AssertionError(f"V18.4 missing {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4_OK changed={str(changed).lower()} "
        "json_text_first=1 strict_v18_identity_reused=1 html_fallback=1 bounded_payload=1 "
        "provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
