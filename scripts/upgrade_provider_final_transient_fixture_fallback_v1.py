#!/usr/bin/env python3
"""Add a strict alternate-fixture fallback for transient final-bundle re-probes.

A provider may prove a semantic lane in the candidate bundle and then hit only
transient gateway/network failures while the immediately rematerialized final
bundle is re-probed. That is not contradictory evidence about the final DATA.
Before failing the provider, try unselected fixtures for the still-missing type.
Wrong-content/runtime/deterministic failures never unlock this fallback.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECONSTRUCT = ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py"
MARKER = "PROVIDER_V3_FINAL_TRANSIENT_FIXTURE_FALLBACK_V1"

OLD_TRANSIENT = "TRANSIENT_LIVE_HTTP_STATUSES = {0, 408, 425, 429, 500, 502, 503, 504, 522, 524}"
NEW_TRANSIENT = "TRANSIENT_LIVE_HTTP_STATUSES = {0, 408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526}"

ANCHOR = '''    required_types = {str(v or "").strip().casefold() for v in evaluation.get("requiredTypes") or []}\n    playable_types = {\n'''

BLOCK = '''    # PROVIDER_V3_FINAL_TRANSIENT_FIXTURE_FALLBACK_V1\n    # The candidate already proved every declared type. If the selected final\n    # fixture exhausted its bounded retries with transport-only failures, probe\n    # alternate fixtures for that same semantic type before declaring DATA\n    # regression. Deterministic/wrong-content selected failures never enter here.\n    selected_slugs = {\n        str(task.get("fixture_slug") or "")\n        for task in used_tasks\n        if isinstance(task, dict) and str(task.get("fixture_slug") or "")\n    }\n    required_before_fallback = {\n        str(v or "").strip().casefold()\n        for v in evaluation.get("requiredTypes") or []\n        if str(v or "").strip()\n    }\n    validated_before_fallback = {\n        str(v or "").strip().casefold()\n        for v in evaluation.get("validatedTypes") or []\n        if str(v or "").strip()\n    }\n    for missing_type in sorted(required_before_fallback - validated_before_fallback):\n        selected_type_rows = [\n            row for row in rows\n            if str(row.get("semantic_type") or "").strip().casefold() == missing_type\n        ]\n        if not selected_type_rows or not all(should_retry_live_probe(row) for row in selected_type_rows):\n            continue\n        fallback_verified = False\n        fallback_step = 0\n        for raw_fallback_task in provider.get("tasks") or []:\n            if not isinstance(raw_fallback_task, dict):\n                continue\n            if str(raw_fallback_task.get("semantic_type") or "").strip().casefold() != missing_type:\n                continue\n            fallback_slug = str(raw_fallback_task.get("fixture_slug") or "")\n            if not fallback_slug or fallback_slug in selected_slugs:\n                continue\n            fallback_step += 1\n            fallback_task = copy.deepcopy(raw_fallback_task)\n            fallback_task["filename"] = final_filename\n            for attempt in range(1, LIVE_PROBE_ATTEMPTS + 1):\n                result = run_task(fallback_task, timeout)\n                result["fixture_slug"] = fallback_task.get("fixture_slug")\n                result["fixture"] = copy.deepcopy(fallback_task.get("fixture") or {})\n                result["probe_attempt"] = attempt\n                result["final_transient_fallback"] = True\n                rows.append(result)\n                evaluation = credit_verified_playable_chains(\n                    evaluate_provider(provider["provider_id"], live_model, rows, minimum), rows\n                )\n                http_counts = Counter(int(fetch.get("status") or 0) for fetch in result.get("fetches") or [])\n                http_summary = ",".join(\n                    f"{status}:{count}" for status, count in sorted(http_counts.items())\n                ) or "none"\n                print(\n                    "FIELD_PROVIDER_FINAL_TRANSIENT_FALLBACK "\n                    f"provider={provider['provider_id']} type={missing_type} "\n                    f"fixture={fallback_task.get('fixture_slug')} fallback_step={fallback_step} "\n                    f"attempt={attempt}/{LIVE_PROBE_ATTEMPTS} task_status={result.get('status')} "\n                    f"http_statuses={http_summary} "\n                    f"validated_types={','.join(evaluation.get('validatedTypes') or []) or 'none'} "\n                    f"missing_types={','.join(evaluation.get('missingTypes') or []) or 'none'}",\n                    flush=True,\n                )\n                validated_now = {\n                    str(value or "").strip().casefold()\n                    for value in evaluation.get("validatedTypes") or []\n                }\n                bad_status = result.get("status") in {\n                    "wrong_content", "runtime_error", "invalid_probe_output", "probe_error"\n                }\n                if missing_type in validated_now and not bad_status:\n                    fallback_verified = True\n                    break\n                if attempt < LIVE_PROBE_ATTEMPTS and not should_retry_live_probe(result):\n                    break\n            if fallback_verified:\n                break\n\n'''


def patch() -> bool:
    text = RECONSTRUCT.read_text(encoding="utf-8")
    changed = False
    if OLD_TRANSIENT in text:
        text = text.replace(OLD_TRANSIENT, NEW_TRANSIENT, 1)
        changed = True
    elif NEW_TRANSIENT not in text:
        raise AssertionError("adaptive transient status set not found")

    if MARKER not in text:
        if text.count(ANCHOR) != 1:
            raise AssertionError("final transient fallback anchor missing or ambiguous")
        text = text.replace(ANCHOR, BLOCK + ANCHOR, 1)
        changed = True

    if changed:
        RECONSTRUCT.write_text(text, encoding="utf-8")
    validate(text)
    return changed


def validate(text: str | None = None) -> None:
    value = text if text is not None else RECONSTRUCT.read_text(encoding="utf-8")
    required = (
        MARKER,
        NEW_TRANSIENT,
        "FIELD_PROVIDER_FINAL_TRANSIENT_FALLBACK",
        "all(should_retry_live_probe(row) for row in selected_type_rows)",
        "fallback_task[\"filename\"] = final_filename",
        "result[\"final_transient_fallback\"] = True",
    )
    missing = [needle for needle in required if needle not in value]
    if missing:
        raise AssertionError("final transient fallback markers missing: " + ",".join(missing))


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_FINAL_TRANSIENT_FIXTURE_FALLBACK_V1_OK "
        f"changed={str(changed).lower()} selected_fixture_gate=strict "
        "transient_only=1 alternate_fixture_required=1 contradictory_evidence=fail_closed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
