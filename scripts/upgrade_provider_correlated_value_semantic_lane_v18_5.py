#!/usr/bin/env python3
"""Provider Value Plan V18.5: align proof-plan lanes with semantic capability.

Provider v3 stores ``NIAKVIO_PROVIDER_MODEL.supportedTypes`` from
``canonicalSupportedTypes``. Nuvio/Core may execute a canonical anime provider on
the TV transport lane. Structured proof plans must therefore accept ``tv`` as a
transport alias for an ``anime`` plan only when the provider itself is
canonically anime-capable.

This is deliberately not a generic TV<->anime equivalence: a movie/tv provider
without canonical anime capability must never consume anime proof. The same
bounded helper is used by correlated provider-value and other structured proof
plan lane gates so they cannot drift apart.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_CORRELATED_VALUE_SEMANTIC_LANE_V18_5"


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
        "NIAKVIO_PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4",
        "NIAKVIO_PROVIDER_VALUE_TRACE_V18_4",
    ):
        if required not in text:
            raise AssertionError(f"V18.5 requires {required}")

    anchor = "function _spv184Trace(stage, mediaType, providerId, stepIndex, route) {\n"
    helper = r'''/* NIAKVIO_PROVIDER_CORRELATED_VALUE_SEMANTIC_LANE_V18_5 */
function _spv185PlanLaneAllowed(lanes, mediaType) {
  if (!Array.isArray(lanes) || !lanes.length) return true;
  const type = _text(mediaType).trim().toLowerCase();
  if (lanes.includes(type)) return true;
  const semantic = Array.isArray(NIAKVIO_PROVIDER_MODEL.supportedTypes)
    ? NIAKVIO_PROVIDER_MODEL.supportedTypes.map(value => _text(value).trim().toLowerCase())
    : [];
  if (!semantic.includes("anime")) return false;
  return (type === "tv" && lanes.includes("anime")) ||
    (type === "anime" && lanes.includes("tv"));
}
'''
    text = once(text, anchor, helper + anchor, "v18.5-semantic-lane-helper")

    traced_old = '''    const lanes = Array.isArray(plan && plan.semanticTypes) ? plan.semanticTypes : [];
    if (lanes.length && !lanes.includes(mediaType) && !(mediaType === "anime" && lanes.includes("tv"))) {
      _spv184Trace("lane_skip", mediaType, "", -1, "");
      continue;
    }
    _spv184Trace("plan_selected", mediaType, "", -1, _text(plan && plan.searchRoute));
'''
    traced_new = '''    const lanes = Array.isArray(plan && plan.semanticTypes) ? plan.semanticTypes : [];
    if (!_spv185PlanLaneAllowed(lanes, mediaType)) {
      _spv184Trace("lane_skip", mediaType, "", -1, "");
      continue;
    }
    _spv184Trace("plan_selected", mediaType, "", -1, _text(plan && plan.searchRoute));
'''
    text = once(text, traced_old, traced_new, "v18.5-provider-value-lane")

    # Other structured proof resolvers were created before V18 and used the
    # older one-way anime->tv condition. Keep all proof-plan lane gates on the
    # same semantic capability rule. This replacement is intentionally bounded
    # to the exact legacy condition.
    plain_old = '''    if (lanes.length && !lanes.includes(mediaType) && !(mediaType === "anime" && lanes.includes("tv"))) continue;
'''
    plain_count = text.count(plain_old)
    if plain_count < 1 or plain_count > 8:
        raise AssertionError(f"v18.5 structured lane anchors={plain_count}")
    text = text.replace(
        plain_old,
        '''    if (!_spv185PlanLaneAllowed(lanes, mediaType)) continue;\n''',
    )

    BASE.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"V18.5 marker count={value.count(MARKER)}")
    for needle in (
        "function _spv185PlanLaneAllowed(lanes, mediaType)",
        'if (lanes.includes(type)) return true;',
        'if (!semantic.includes("anime")) return false;',
        '(type === "tv" && lanes.includes("anime"))',
        '(type === "anime" && lanes.includes("tv"))',
        'if (!_spv185PlanLaneAllowed(lanes, mediaType)) {',
        'if (!_spv185PlanLaneAllowed(lanes, mediaType)) continue;',
    ):
        if needle not in value:
            raise AssertionError(f"V18.5 missing {needle}")
    forbidden = 'lanes.length && !lanes.includes(mediaType) && !(mediaType === "anime" && lanes.includes("tv"))'
    if forbidden in value:
        raise AssertionError("V18.5 left legacy one-way structured lane gate")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_CORRELATED_VALUE_SEMANTIC_LANE_V18_5_OK changed={str(changed).lower()} "
        "canonical_anime_tv_transport=1 generic_tv_to_anime=0 shared_plan_gate=1 provider_specific_rules=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
