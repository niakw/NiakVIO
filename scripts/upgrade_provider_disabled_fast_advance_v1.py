#!/usr/bin/env python3
"""Skip release qualification traffic for activation-matrix-disabled providers.

The release gate is defined by enabled providers. Disabled providers must remain
materializable and present in the 96-provider corpus, but they must not consume the
same current-run live qualification/retry budget as enabled providers and they must
never count toward active qualification.

A dedicated audit can opt back into the historical deep behavior with
PROVIDER_V3_AUDIT_DISABLED_LIVE=1.
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

    old_probe = '''        _rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)\n        completion_state = "declared-types-qualified" if is_qualified(evaluation) else None\n        origin_evidence: list[dict[str, Any]] = []\n        if completion_state is None:\n            completion_state, origin_evidence = terminal_state(\n                evaluation, model, patch, origin_timeout\n            )\n\n        if completion_state is None and provider.get("enabled") is False:\n            completion_state = "disabled-unqualified"\n            print(\n                "FIELD_PROVIDER_DISABLED_UNQUALIFIED_ADVANCE "\n                f"provider={provider_id} phase=candidate "\n                f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'}",\n                flush=True,\n            )\n'''
    new_probe = '''        disabled_fast_advance = skip_disabled_live_qualification(provider)\n        if disabled_fast_advance:\n            # OFF providers stay present/materializable, but current-run release\n            # qualification is intentionally not executed and no historical proof\n            # is credited into the active gate. Preserve their durable DATA as-is.\n            evaluation = credit_verified_playable_chains(\n                evaluate_provider(provider_id, model, [], minimum), []\n            )\n            evaluation["qualificationSkipped"] = True\n            evaluation["disabledByActivationMatrix"] = True\n            used_tasks: list[dict[str, Any]] = []\n            completion_state = "disabled-unqualified"\n            origin_evidence: list[dict[str, Any]] = []\n            print(\n                "FIELD_PROVIDER_DISABLED_FAST_ADVANCE "\n                f"provider={provider_id} network_qualification=false "\n                f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'}",\n                flush=True,\n            )\n        else:\n            _rows, evaluation, used_tasks = run_until_qualified(provider, model, minimum, timeout)\n            completion_state = "declared-types-qualified" if is_qualified(evaluation) else None\n            origin_evidence = []\n            if completion_state is None:\n                completion_state, origin_evidence = terminal_state(\n                    evaluation, model, patch, origin_timeout\n                )\n\n            if completion_state is None and provider.get("enabled") is False:\n                completion_state = "disabled-unqualified"\n                print(\n                    "FIELD_PROVIDER_DISABLED_UNQUALIFIED_ADVANCE "\n                    f"provider={provider_id} phase=candidate "\n                    f"missing={','.join(evaluation.get('missingTypes') or []) or 'none'}",\n                    flush=True,\n                )\n'''
    if text.count(old_probe) != 1:
        raise AssertionError("disabled fast advance probe anchor missing")
    text = text.replace(old_probe, new_probe, 1)

    old_finalize = '''        finalize_provider(\n            provider_id,\n            provider,\n            knowledge,\n            overrides,\n            evaluation,\n            completion_state,\n            origin_evidence,\n        )\n        write(knowledge_path, knowledge)\n        write(overrides_path, overrides)\n\n        materialized = materialize_one(provider_id)\n'''
    new_finalize = '''        if disabled_fast_advance:\n            # Do not overwrite durable/historical Provider DATA or claim that its\n            # JavaScript was executed in this run. Candidate and final bundle are\n            # still materialized, so structural 96/96 reconstruction remains real.\n            materialized = materialize_one(provider_id)\n        else:\n            finalize_provider(\n                provider_id,\n                provider,\n                knowledge,\n                overrides,\n                evaluation,\n                completion_state,\n                origin_evidence,\n            )\n            write(knowledge_path, knowledge)\n            write(overrides_path, overrides)\n            materialized = materialize_one(provider_id)\n'''
    if text.count(old_finalize) != 1:
        raise AssertionError("disabled fast advance finalization anchor missing")
    text = text.replace(old_finalize, new_finalize, 1)

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


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_DISABLED_FAST_ADVANCE_V1_OK "
        f"changed={str(changed).lower()} active_gate_unchanged=1 "
        "disabled_network_qualification=0 durable_data_preserved=1 audit_opt_in=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
