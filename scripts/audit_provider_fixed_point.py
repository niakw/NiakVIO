#!/usr/bin/env python3
"""Audit provider publication fixed-point convergence with actionable provider IDs.

This disposable diagnostic mirrors authoritative Core preparation and reports not
only moving content-addressed references but also whether each moving provider
recovers the same provider-derived prefix before Core hooks are rebuilt.  That
makes a plateau actionable without mutating generated provider bundles by hand.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

AUDIT_REVISION = "plateau-root-v3"
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, check=check)


def refs() -> dict[str, str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        str(row.get("id") or "").strip().casefold(): str(row.get("filename") or "")
        for row in data.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }


def short_ref(value: str) -> str:
    name = Path(value).name
    stem = name[:-3] if name.endswith(".js") else name
    return stem.rsplit("--", 1)[-1][:16] if "--" in stem else stem[-16:]


def _read_ref(value: str) -> str:
    path = ROOT / value
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _first_diff(left: str, right: str) -> tuple[int, int]:
    prefix = 0
    limit = min(len(left), len(right))
    while prefix < limit and left[prefix] == right[prefix]:
        prefix += 1
    suffix = 0
    remaining = limit - prefix
    while suffix < remaining and left[len(left) - 1 - suffix] == right[len(right) - 1 - suffix]:
        suffix += 1
    return prefix, suffix


def diagnose_transition(provider_id: str, before_ref: str, after_ref: str, pass_no: int) -> None:
    # Import only after durable normalizers have rewritten the owning module.
    sys.path.insert(0, str(ROOT / "scripts"))
    from apply_provider_overrides import _provider_export_floor, _strip_generated_core_tail  # noqa: E402

    before = _read_ref(before_ref)
    after = _read_ref(after_ref)
    before_base, before_stripped = _strip_generated_core_tail(before)
    after_base, after_stripped = _strip_generated_core_tail(after)
    prefix, suffix = _first_diff(before, after)
    markers = (
        "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
        "NUVIO_HLS_RUNTIME_INTEGRITY_V1",
        "NUVIO_GLOBAL_STREAM_FACTS_V1",
        "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
        "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",
        "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
    )
    marker_state = ";".join(
        f"{marker.replace('NUVIO_', '')}:{before.find(marker)}>{after.find(marker)}"
        for marker in markers
    )
    print(
        "FIELD_PROVIDER_FIXED_POINT_ROOT "
        f"pass={pass_no} provider={provider_id} "
        f"refs={short_ref(before_ref)}>{short_ref(after_ref)} "
        f"len={len(before)}>{len(after)} first_diff={prefix} common_suffix={suffix} "
        f"floor={_provider_export_floor(before)}>{_provider_export_floor(after)} "
        f"stripped={str(before_stripped).lower()}>{str(after_stripped).lower()} "
        f"base_len={len(before_base)}>{len(after_base)} "
        f"base_sha={_digest(before_base)}>{_digest(after_base)} "
        f"base_equal={str(before_base == after_base).lower()} markers={marker_state}",
        flush=True,
    )
    if before_base != after_base:
        base_prefix, base_suffix = _first_diff(before_base, after_base)
        left = before_base[max(0, base_prefix - 80): base_prefix + 160]
        right = after_base[max(0, base_prefix - 80): base_prefix + 160]
        print(
            "FIELD_PROVIDER_FIXED_POINT_BASE_DIFF "
            f"pass={pass_no} provider={provider_id} first_diff={base_prefix} common_suffix={base_suffix} "
            f"before={json.dumps(left, ensure_ascii=True)} after={json.dumps(right, ensure_ascii=True)}",
            flush=True,
        )


def main() -> int:
    print(f"FIELD_PROVIDER_FIXED_POINT_AUDIT revision={AUDIT_REVISION}", flush=True)
    run("scripts/normalize_provider_rebuild_safety.py", "--apply")
    run("scripts/normalize_core_fixed_point_contract.py", "--apply")
    run("scripts/normalize_provider_branding_pipeline.py", "--apply")
    run("scripts/normalize_core_media_policy.py", "--apply")
    run("scripts/apply_runtime_capability_upgrade_v4.py")
    run("scripts/build_provider_runtime_profiles.py")

    previous_changed: tuple[str, ...] | None = None
    for pass_no in range(1, 7):
        before = refs()
        run(str(REAPPLY))
        after = refs()
        changed = tuple(sorted(pid for pid in set(before) | set(after) if before.get(pid) != after.get(pid)))
        transitions = ",".join(
            f"{pid}:{short_ref(before.get(pid, ''))}>{short_ref(after.get(pid, ''))}" for pid in changed
        ) or "-"
        print(
            "FIELD_PROVIDER_FIXED_POINT_PASS "
            f"pass={pass_no} changed_count={len(changed)} ids={','.join(changed) or '-'}",
            flush=True,
        )
        print(f"FIELD_PROVIDER_FIXED_POINT_TRANSITIONS pass={pass_no} values={transitions}", flush=True)

        if pass_no >= 3 and len(changed) <= 20:
            for provider_id in changed:
                diagnose_transition(provider_id, before.get(provider_id, ""), after.get(provider_id, ""), pass_no)

        if not changed:
            checked = run(str(REAPPLY), "--check", check=False)
            if checked.returncode == 0:
                print(f"FIELD_PROVIDER_FIXED_POINT_RESULT status=converged pass={pass_no}", flush=True)
                return 0
            print(f"FIELD_PROVIDER_FIXED_POINT_RESULT status=metadata_stale pass={pass_no}", flush=True)
            return 5

        if previous_changed is not None and changed == previous_changed:
            print(
                "FIELD_PROVIDER_FIXED_POINT_RESULT status=stagnant "
                f"pass={pass_no} changed_count={len(changed)} ids={','.join(changed)}",
                flush=True,
            )
            return 3
        previous_changed = changed

    print(
        "FIELD_PROVIDER_FIXED_POINT_RESULT status=nonconvergent "
        f"changed_count={len(previous_changed or ())} ids={','.join(previous_changed or ())}",
        flush=True,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
