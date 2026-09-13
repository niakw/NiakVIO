#!/usr/bin/env python3
"""Make Provider v3 minimization an explicit final-stage operation.

Workspace/provider-repair materialization must preserve readable Lego bytes. The
embedded minimizer may only run in release/main context when explicitly requested
with NIAKVIO_PROVIDER_V3_FINAL_MINIMIZE=1.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL = ROOT / "scripts" / "materialize_provider_v3_all.py"
ONE = ROOT / "scripts" / "materialize_provider_v3_one.py"
MARKER = "PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"{label}: anchor not found")
    if text.count(old) != 1:
        raise SystemExit(f"{label}: anchor count={text.count(old)}")
    return text.replace(old, new, 1)


def patch_all(text: str) -> str:
    helper_anchor = "EXPECTED_PROVIDER_COUNT = 96\n"
    helper = '''EXPECTED_PROVIDER_COUNT = 96\n\n# PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1\nFINAL_MINIMIZER_ENV = "NIAKVIO_PROVIDER_V3_FINAL_MINIMIZE"\n\ndef materialization_context() -> str:\n    context = str(os.environ.get("NUVIO_PROVIDER_V3_CONTEXT") or "workspace").strip().casefold()\n    if context not in {"workspace", "release", "main"}:\n        raise ValueError(f"invalid NUVIO_PROVIDER_V3_CONTEXT: {context}")\n    return context\n\ndef final_minimizer_enabled(context: str | None = None) -> bool:\n    current = str(context or materialization_context()).strip().casefold()\n    raw = str(os.environ.get(FINAL_MINIMIZER_ENV) or "").strip().casefold()\n    false_values = {"", "0", "false", "no", "off"}\n    true_values = {"1", "true", "yes", "on"}\n    if raw not in false_values | true_values:\n        raise ValueError(f"invalid {FINAL_MINIMIZER_ENV}: {raw}")\n    requested = raw in true_values\n    if requested and current not in {"release", "main"}:\n        raise ValueError(\n            f"{FINAL_MINIMIZER_ENV}=1 is forbidden in {current} context; "\n            "minimization is final-stage only"\n        )\n    return requested and current in {"release", "main"}\n'''
    text = once(text, helper_anchor, helper, "all-helper")

    context_anchor = '''    if not isinstance(patches, dict) or not isinstance(capabilities, dict):\n        raise ValueError("provider override maps required")\n\n    rows = [\n'''
    context_new = '''    if not isinstance(patches, dict) or not isinstance(capabilities, dict):\n        raise ValueError("provider override maps required")\n\n    context = materialization_context()\n    minimize_enabled = final_minimizer_enabled(context)\n\n    rows = [\n'''
    text = once(text, context_anchor, context_new, "all-context")

    old_min = '''        minimized = minimize_text(text)\n        validate_transform(text, minimized.text)\n        text = minimized.text\n        bundle = text.encode("utf-8")\n\n        # Prove minimization kept Lego ownership and envelope byte-addressable.\n        minimized_fix_ids = validate_managed_fixes(text)\n        if minimized_fix_ids != fix_ids:\n            raise ValueError(f"{provider_id}: minimizer changed managed Lego ownership")\n        if text.count("/* BEGIN NIAKVIO_PROVIDER */") != 1 or text.count("/* END NIAKVIO_PROVIDER */") != 1:\n            raise ValueError(f"{provider_id}: minimizer changed Provider v3 envelope")\n        if text.count(boundary) != 1:\n            raise ValueError(f"{provider_id}: minimizer changed Core boundary")\n\n'''
    new_min = '''        minimizer_report = {\n            "enabled": False,\n            "savedBytes": 0,\n            "transformedLines": 0,\n            "skippedReason": "final-stage-only",\n        }\n        if minimize_enabled:\n            minimized = minimize_text(text)\n            validate_transform(text, minimized.text)\n            text = minimized.text\n            minimizer_report = {\n                "enabled": True,\n                "savedBytes": minimized.saved_bytes,\n                "transformedLines": minimized.transformed_lines,\n                "skippedReason": minimized.skipped_reason,\n            }\n\n            # Prove final-stage minimization kept Lego ownership and envelope byte-addressable.\n            minimized_fix_ids = validate_managed_fixes(text)\n            if minimized_fix_ids != fix_ids:\n                raise ValueError(f"{provider_id}: minimizer changed managed Lego ownership")\n            if text.count("/* BEGIN NIAKVIO_PROVIDER */") != 1 or text.count("/* END NIAKVIO_PROVIDER */") != 1:\n                raise ValueError(f"{provider_id}: minimizer changed Provider v3 envelope")\n            if text.count(boundary) != 1:\n                raise ValueError(f"{provider_id}: minimizer changed Core boundary")\n        bundle = text.encode("utf-8")\n\n'''
    text = once(text, old_min, new_min, "all-minimizer")

    old_report = '''            "minimizer": {\n                "enabled": True,\n                "savedBytes": minimized.saved_bytes,\n                "transformedLines": minimized.transformed_lines,\n                "skippedReason": minimized.skipped_reason,\n            },\n'''
    new_report = '''            "minimizer": minimizer_report,\n'''
    text = once(text, old_report, new_report, "all-report")

    duplicate_context = '''    context = str(os.environ.get("NUVIO_PROVIDER_V3_CONTEXT") or "workspace").strip().casefold()\n    if context not in {"workspace", "release", "main"}:\n        raise ValueError(f"invalid NUVIO_PROVIDER_V3_CONTEXT: {context}")\n    report = {\n'''
    text = once(text, duplicate_context, '''    report = {\n''', "all-duplicate-context")
    return text


def patch_one(text: str) -> str:
    old_min = '''    minimized = allmat.minimize_text(text)\n    allmat.validate_transform(text, minimized.text)\n    text = minimized.text\n    bundle = text.encode("utf-8")\n    if allmat.validate_managed_fixes(text) != fix_ids:\n        raise ValueError(f"{provider_id}: minimizer changed managed Lego ownership")\n    if text.count(boundary) != 1:\n        raise ValueError(f"{provider_id}: minimizer changed Core boundary")\n\n'''
    new_min = '''    # PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1\n    context = allmat.materialization_context()\n    minimize_enabled = allmat.final_minimizer_enabled(context)\n    minimizer_report = {\n        "enabled": False,\n        "savedBytes": 0,\n        "transformedLines": 0,\n        "skippedReason": "final-stage-only",\n    }\n    if minimize_enabled:\n        minimized = allmat.minimize_text(text)\n        allmat.validate_transform(text, minimized.text)\n        text = minimized.text\n        minimizer_report = {\n            "enabled": True,\n            "savedBytes": minimized.saved_bytes,\n            "transformedLines": minimized.transformed_lines,\n            "skippedReason": minimized.skipped_reason,\n        }\n        if allmat.validate_managed_fixes(text) != fix_ids:\n            raise ValueError(f"{provider_id}: minimizer changed managed Lego ownership")\n        if text.count(boundary) != 1:\n            raise ValueError(f"{provider_id}: minimizer changed Core boundary")\n    bundle = text.encode("utf-8")\n\n'''
    text = once(text, old_min, new_min, "one-minimizer")

    old_report = '''        "minimizer": {\n            "enabled": True,\n            "savedBytes": minimized.saved_bytes,\n            "transformedLines": minimized.transformed_lines,\n            "skippedReason": minimized.skipped_reason,\n        },\n'''
    text = once(text, old_report, '''        "minimizer": minimizer_report,\n''', "one-report")
    return text


def main() -> int:
    all_before = ALL.read_text(encoding="utf-8")
    one_before = ONE.read_text(encoding="utf-8")
    all_after = patch_all(all_before)
    one_after = patch_one(one_before)
    ALL.write_text(all_after, encoding="utf-8")
    ONE.write_text(one_after, encoding="utf-8")
    print(
        "PROVIDER_V3_FINAL_STAGE_MINIMIZER_GATE_V1_OK "
        f"all_changed={all_after != all_before} one_changed={one_after != one_before}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
