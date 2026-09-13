#!/usr/bin/env python3
"""Skip release qualification traffic for activation-matrix-disabled providers.

The release gate is defined by enabled providers. Disabled providers remain
materializable/present in the 96-provider catalogue, but ordinary release
reconstruction must not spend current-run live qualification budget on them.

This migration is deliberately layout-tolerant: the sequential reconstructor gained
clean-zero/resample logic after the first version of this patch. We anchor on the
semantic candidate-proof region instead of one historical text rectangle.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCT = ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py"
MARKER = "PROVIDER_V3_DISABLED_FAST_ADVANCE_V1"


def patch() -> bool:
    text = RECONSTRUCT.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    live_attempt_anchor = "LIVE_PROBE_ATTEMPTS = _live_probe_attempts()\n"
    helper = '''LIVE_PROBE_ATTEMPTS = _live_probe_attempts()\n\n\n# PROVIDER_V3_DISABLED_FAST_ADVANCE_V1\ndef skip_disabled_live_qualification(provider: dict[str, Any]) -> bool:\n    """Return true when release reconstruction should fast-advance an OFF provider."""\n    if provider.get("enabled") is not False:\n        return False\n    audit = str(os.environ.get("PROVIDER_V3_AUDIT_DISABLED_LIVE") or "").strip().casefold()\n    return audit not in {"1", "true", "yes", "on"}\n'''
    if text.count(live_attempt_anchor) != 1:
        raise AssertionError("disabled fast advance helper anchor missing")
    text = text.replace(live_attempt_anchor, helper, 1)

    proof_start = "        _rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)\n"
    failure_start = "        if completion_state is None:\n            failure = {\n"
    start = text.find(proof_start)
    end = text.find(failure_start, start + 1) if start >= 0 else -1
    if start < 0 or end < 0 or end <= start:
        raise AssertionError("disabled fast advance semantic proof anchors missing")

    current_region = text[start:end]
    required_current = (
        "completion_state = \"declared-types-qualified\" if is_qualified(evaluation) else None",
        "terminal_state(",
        "provider.get(\"enabled\") is False",
        "FIELD_PROVIDER_DISABLED_UNQUALIFIED_ADVANCE",
    )
    missing = [needle for needle in required_current if needle not in current_region]
    if missing:
        raise AssertionError("disabled fast advance current proof region incomplete: " + ",".join(missing))

    has_resample = "resample_required_lanes(_rows, evaluation)" in current_region
    resample_block = '''\n            if completion_state is None and provider.get("enabled") is not False:\n                resample_lanes = resample_required_lanes(_rows, evaluation)\n                if resample_lanes:\n                    completion_state = "resample-required"\n                    print(\n                        "FIELD_PROVIDER_RESAMPLE_REQUIRED "\n                        f"provider={provider_id} lanes={','.join(resample_lanes)} "\n                        "reason=clean_zero_stream_catalogue_sample next_action=rotate_fixture",\n                        flush=True,\n                    )\n''' if has_resample else ""

    replacement = '''        disabled_fast_advance = skip_disabled_live_qualification(provider)\n        if disabled_fast_advance:\n            # OFF rows retain their durable Provider DATA. No live request is made\n            # and no historical proof is credited into the active release gate.\n            _rows: list[dict[str, Any]] = []\n            evaluation = credit_verified_playable_chains(\n                evaluate_provider(provider_id, model, [], minimum), []\n            )\n            evaluation["qualificationSkipped"] = True\n            evaluation["disabledByActivationMatrix"] = True\n            used_tasks: list[dict[str, Any]] = []\n            completion_state = "disabled-unqualified"\n            origin_evidence: list[dict[str, Any]] = []\n            print(\n                "FIELD_PROVIDER_DISABLED_FAST_ADVANCE "\n                f"provider={provider_id} network_qualification=false "\n                f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'}",\n                flush=True,\n            )\n        else:\n            _rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)\n            completion_state = "declared-types-qualified" if is_qualified(evaluation) else None\n            origin_evidence: list[dict[str, Any]] = []\n            if completion_state is None:\n                completion_state, origin_evidence = terminal_state(\n                    evaluation, model, patch, origin_timeout\n                )\n''' + resample_block + '''\n            if completion_state is None and provider.get("enabled") is False:\n                completion_state = "disabled-unqualified"\n                print(\n                    "FIELD_PROVIDER_DISABLED_UNQUALIFIED_ADVANCE "\n                    f"provider={provider_id} phase=candidate "\n                    f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'}",\n                    flush=True,\n                )\n\n'''
    text = text[:start] + replacement + text[end:]

    finalize_start = "        finalize_provider(\n            provider_id,\n            provider,\n            knowledge,\n            overrides,\n            evaluation,\n            completion_state,\n            origin_evidence,\n        )\n        write(knowledge_path, knowledge)\n        write(overrides_path, overrides)\n\n        materialized = materialize_one(provider_id)\n"
    guarded_finalize = '''        if disabled_fast_advance:\n            # Structural materialization remains real, but skipped OFF providers do\n            # not overwrite durable DATA with an empty current-run evaluation.\n            materialized = materialize_one(provider_id)\n        else:\n            finalize_provider(\n                provider_id,\n                provider,\n                knowledge,\n                overrides,\n                evaluation,\n                completion_state,\n                origin_evidence,\n            )\n            write(knowledge_path, knowledge)\n            write(overrides_path, overrides)\n            materialized = materialize_one(provider_id)\n'''
    if text.count(finalize_start) != 1:
        raise AssertionError("disabled fast advance finalization anchor missing")
    text = text.replace(finalize_start, guarded_finalize, 1)

    RECONSTRUCT.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else RECONSTRUCT.read_text(encoding="utf-8")
    required = (
        MARKER,
        "def skip_disabled_live_qualification(",
        "PROVIDER_V3_AUDIT_DISABLED_LIVE",
        "disabled_fast_advance = skip_disabled_live_qualification(provider)",
        'evaluation["qualificationSkipped"] = True',
        'evaluation["disabledByActivationMatrix"] = True',
        "FIELD_PROVIDER_DISABLED_FAST_ADVANCE",
        "if disabled_fast_advance:",
        "network_qualification=false",
    )
    missing = [needle for needle in required if needle not in value]
    if missing:
        raise AssertionError("disabled fast advance markers missing: " + ",".join(missing))
    fast_pos = value.index("disabled_fast_advance = skip_disabled_live_qualification(provider)")
    probe_pos = value.index("run_until_qualified(provider, model, minimum, timeout)", fast_pos)
    if fast_pos >= probe_pos:
        raise AssertionError("disabled fast advance must be decided before live qualification")
    finalize_pos = value.index("finalize_provider(", probe_pos)
    guard_pos = value.rfind("if disabled_fast_advance:", probe_pos, finalize_pos)
    if guard_pos < 0:
        raise AssertionError("durable finalization is not guarded for disabled fast advance")
    if "def resample_required_lanes(" in value:
        proof_region = value[fast_pos:finalize_pos]
        if "resample_required_lanes(_rows, evaluation)" not in proof_region:
            raise AssertionError("clean-zero resample policy was lost while adding disabled fast advance")


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_DISABLED_FAST_ADVANCE_V1_OK "
        f"changed={str(changed).lower()} active_gate_unchanged=1 "
        "disabled_network_qualification=0 durable_data_preserved=1 audit_opt_in=1 layout_tolerant=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
