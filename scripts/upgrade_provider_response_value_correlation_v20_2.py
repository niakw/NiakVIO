#!/usr/bin/env python3
"""V20.2: compose V20 response-value replay with the current V18.4 Base resolver.

V20.1 made proof/materialization structural. The remaining Base migration still
expected the pre-V18.4 identity block and pre-trace step guard. V20.2 keeps the
canonical V20 Base owner, but translates only those known shared-owner anchors:
- the two intentional recipe value maps;
- V18.4 JSON-text/HTML identity selection -> provider id+slug pair;
- V18.4 traced step shape guard -> {id}|{slug}.

No provider-specific host, route, selector, title or id is introduced.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import upgrade_provider_response_value_correlation_v20_1 as v201  # noqa: E402

legacy = v201.legacy

patch_worker = v201.patch_worker
patch_proof = v201.patch_proof
patch_recovery = v201.patch_recovery
patch_materializer = v201.patch_materializer
validate_worker = v201.validate_worker
validate_proof = v201.validate_proof
validate_recovery = v201.validate_recovery
validate_materializer = v201.validate_materializer
validate_base = v201.validate_base


def _replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one current-owner anchor, got {count}")
    return text.replace(old, new, 1)


def patch_base() -> bool:
    original_once = legacy.once

    def compatible_once(text: str, old: str, new: str, label: str) -> str:
        if label == "v20-base-recipe-url-slug":
            count = text.count(old)
            if count != 2:
                raise AssertionError(f"{label}: expected two intentional anchors, got {count}")
            return text.replace(old, new, 1)

        if label == "v20-base-provider-value-pair" and old not in text:
            current = r'''      /* NIAKVIO_PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4 */
      let providerId = "";
      if (typeof searchPayload.value === "string") {
        const rawSearchValue = _text(searchPayload.value).trim();
        if (rawSearchValue && rawSearchValue.length <= 4 * 1024 * 1024 && /^[\[{]/.test(rawSearchValue)) {
          try {
            providerId = _spv18ProviderIdFromJson(JSON.parse(rawSearchValue), meta);
          } catch (_) {}
        }
        if (!providerId) providerId = _spv18ProviderIdFromHtml(rawSearchValue, meta);
      } else {
        providerId = _spv18ProviderIdFromJson(searchPayload.value, meta);
      }
      _spv184Trace(providerId ? "identity_hit" : "identity_miss", mediaType, providerId, -1, searchRoute);
      if (!providerId) continue;
      const values = Object.assign({}, baseValues, { providerId });
'''
            replacement = r'''      /* NIAKVIO_PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4 */
      /* NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20_2 */
      let providerValues = { id: "", slug: "" };
      if (typeof searchPayload.value === "string") {
        const rawSearchValue = _text(searchPayload.value).trim();
        if (rawSearchValue && rawSearchValue.length <= 4 * 1024 * 1024 && /^[\[{]/.test(rawSearchValue)) {
          try {
            providerValues = _spv20ProviderValuesFromJson(JSON.parse(rawSearchValue), meta);
          } catch (_) {}
        }
        if (!providerValues || (!providerValues.id && !providerValues.slug)) {
          providerValues = _spv20ProviderValuesFromHtml(rawSearchValue, meta);
        }
      } else {
        providerValues = _spv20ProviderValuesFromJson(searchPayload.value, meta);
      }
      providerValues = providerValues || { id: "", slug: "" };
      const providerId = providerValues.id || providerValues.slug || "";
      _spv184Trace(providerId ? "identity_hit" : "identity_miss", mediaType, providerId, -1, searchRoute);
      if (!providerId) continue;
      const values = Object.assign({}, baseValues, {
        providerId,
        providerSlug: providerValues.slug || providerValues.id || providerId
      });
'''
            return _replace_exact(text, current, replacement, label)

        if label == "v20-base-provider-step-id-or-slug" and old not in text:
            current = r'''        if (!/^https?:\/\//i.test(stepBase) || !stepRoute || !/\{id\}/i.test(stepRoute)) {
'''
            replacement = r'''        if (!/^https?:\/\//i.test(stepBase) || !stepRoute || !/\{(?:id|slug)\}/i.test(stepRoute)) {
'''
            return _replace_exact(text, current, replacement, label)

        return original_once(text, old, new, label)

    legacy.once = compatible_once
    try:
        changed = legacy.patch_base()
    finally:
        legacy.once = original_once
    validate_base()
    return changed


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_recovery() | patch_materializer() | patch_base()
    validate_worker()
    validate_proof()
    validate_recovery()
    validate_materializer()
    validate_base()
    print(
        f"PROVIDER_RESPONSE_VALUE_CORRELATION_V20_2_OK changed={str(changed).lower()} "
        "v18_4_json_text_preserved=1 v18_4_trace_preserved=1 id_slug_pair=1 "
        "provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
