#!/usr/bin/env python3
"""One-shot migration: active native matrix passes only when every active provider is FULL."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/gate_native_declared_provider_matrix.py"
TEST = ROOT / "tests/native_declared_provider_matrix_test.py"
MARKER = "NATIVE_ACTIVE_FULL_CERTIFICATION_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def patch_gate() -> None:
    text = GATE.read_text(encoding="utf-8")
    if MARKER in text:
        return
    text = replace_once(
        text,
        '    parser.add_argument("--scope-matrix", type=Path, default=None)\n    parser.add_argument("logs", nargs="+", type=Path)\n',
        '    parser.add_argument("--scope-matrix", type=Path, default=None)\n'
        '    parser.add_argument("--allow-nonfull", action="store_true", help="diagnostic/repair mode only; do not certify active providers")\n'
        '    parser.add_argument("--json-output", type=Path, default=None, help="write structured provider/lane certification evidence")\n'
        '    parser.add_argument("logs", nargs="+", type=Path)\n',
        "gate args",
    )
    start = text.index('    counts = {kind: sum(1 for _, media_type in expected if media_type == kind) for kind in TYPES}\n')
    end = text.index('    for provider in missing_providers[:120]:\n', start)
    new_block = '''    # NATIVE_ACTIVE_FULL_CERTIFICATION_V1
    # Structural traversal is necessary but not sufficient. An enabled provider is
    # certified only when every declared semantic lane has positive stream output
    # after the suite's adaptive catalogue rotation has had a chance to replace
    # clean catalogue misses. PARTIAL/RESAMPLE/ZERO remain valuable Brain evidence,
    # but none of them is a valid published-active state.
    counts = {kind: sum(1 for _, media_type in expected if media_type == kind) for kind in TYPES}
    structural_state = "passed" if not missing_begin and not missing_end and not missing_providers and not unexpected else "failed"

    status_counts: Counter[str] = Counter()
    provider_rows: list[dict[str, object]] = []
    nonfull: list[str] = []
    for provider in sorted(provider_ids):
        lanes = sorted(media_type for p, media_type in expected if p == provider)
        outcomes = {media_type: lane_outcomes[(provider, media_type)] for media_type in lanes}
        status = provider_status(outcomes)
        status_counts[status] += 1
        if status != "FULL":
            nonfull.append(provider)
        provider_rows.append({
            "provider": display.get(provider, provider),
            "providerId": provider,
            "status": status,
            "lanes": outcomes,
        })
        lane_text = ",".join(f"{media_type}:{outcomes[media_type]}" for media_type in lanes)
        print(
            "FIELD_NATIVE_PROVIDER_STATUS "
            f"client={args.client} provider={display.get(provider, provider)} status={status} lanes={lane_text}"
        )

    health_state = "passed" if not nonfull else "failed"
    state = "passed" if structural_state == "passed" and (args.allow_nonfull or health_state == "passed") else "failed"
    print(
        "FIELD_NATIVE_DECLARED_MATRIX "
        f"state={state} structural={structural_state} health={health_state} client={args.client} "
        f"providers={len(provider_ids)} disabled={len(disabled_ids)} routes={len(expected)} "
        f"movie={counts['movie']} tv={counts['tv']} anime={counts['anime']} "
        f"begun={len(begun & expected)} completed={len(completed & expected)} "
        f"missing_providers={len(missing_providers)} missing_begin={len(missing_begin)} "
        f"missing_end={len(missing_end)} unexpected={len(unexpected)} observed_disabled={len(observed_disabled)} "
        f"nonfull={len(nonfull)} allow_nonfull={str(args.allow_nonfull).lower()}"
    )
    print(
        "FIELD_NATIVE_PROVIDER_STATUS_SUMMARY "
        f"client={args.client} total={len(provider_ids)} FULL={status_counts['FULL']} "
        f"PARTIAL={status_counts['PARTIAL']} RESAMPLE={status_counts['RESAMPLE']} ZERO={status_counts['ZERO']}"
    )
    for provider in nonfull[:240]:
        row = next(item for item in provider_rows if item["providerId"] == provider)
        lane_text = ",".join(f"{lane}:{outcome}" for lane, outcome in sorted(dict(row["lanes"]).items()))
        print(
            "FIELD_NATIVE_ACTIVE_UNCERTIFIED "
            f"client={args.client} provider={row['provider']} status={row['status']} lanes={lane_text}"
        )

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps({
            "schemaVersion": 1,
            "authority": "native-active-full-certification-v1",
            "client": args.client,
            "state": state,
            "structuralState": structural_state,
            "healthState": health_state,
            "allowNonFull": bool(args.allow_nonfull),
            "providerCount": len(provider_ids),
            "disabledCount": len(disabled_ids),
            "routeCount": len(expected),
            "statusCounts": dict(status_counts),
            "nonFullProviders": [display.get(provider, provider) for provider in nonfull],
            "providers": provider_rows,
        }, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")

'''
    text = text[:start] + new_block + text[end:]
    GATE.write_text(text, encoding="utf-8")


def patch_test() -> None:
    text = TEST.read_text(encoding="utf-8")
    text = text.replace('request_type={media_type} count=0\\n"\n', 'request_type={media_type} count=1\\n"\n')
    old = '''        # Deliberately omit FIELD_NATIVE_IOS_RESULT here: provider END must still
        # derive the lane from any adaptive fixture slug and count as a terminal.
        lines.append(
            f"FIELD_NATIVE_IOS_PROVIDER_END fixture={fixture} provider={provider} state=completed duration_ms=1\\n"
        )
'''
    new = '''        lines.append(
            "FIELD_NATIVE_IOS_RESULT " + json.dumps({
                "fixture": fixture,
                "provider": provider,
                "mediaType": media_type,
                "enabled": True,
                "count": 1,
                "durationMs": 1,
                "state": "completed",
            }) + "\\n"
        )
        lines.append(
            f"FIELD_NATIVE_IOS_PROVIDER_END fixture={fixture} provider={provider} state=completed duration_ms=1\\n"
        )
'''
    if new in text:
        # Already migrated by an earlier workflow run. Keep the one-shot upgrader
        # safe to invoke again while a temporary validation workflow is iterated.
        TEST.write_text(text, encoding="utf-8")
        return
    text = replace_once(text, old, new, "ios positive test")
    TEST.write_text(text, encoding="utf-8")


def main() -> int:
    patch_gate()
    patch_test()
    print("NATIVE_ACTIVE_FULL_CERTIFICATION_V1 applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
