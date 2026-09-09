#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path: Path, old: str, new: str, label: str, *, all_occurrences: bool = False) -> bool:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return False
    if old not in text:
        raise SystemExit(f"{label}: source anchor missing in {path.relative_to(ROOT)}")
    text = text.replace(old, new) if all_occurrences else text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    changed = []

    v1 = ROOT / "scripts" / "build_provider_history_matrix.py"
    if patch(
        v1,
        "baseline = lanes_from_rows(by36.get(pid) or qrows)",
        "baseline = lanes_from_rows(by36.get(pid) or [])",
        "historical V1 cross-version fallback",
    ):
        changed.append(str(v1.relative_to(ROOT)))

    repair = ROOT / "scripts" / "run_provider_repair_pipeline_v6.py"
    if patch(
        repair,
        '        "tests/global_media_type_resolution_test.py",',
        '        "tests/global_media_type_pre_network_gate_test.py",\n        "tests/global_media_type_resolution_test.py",',
        "repair V6 media fast gate",
    ):
        changed.append(str(repair.relative_to(ROOT)))

    sync = ROOT / ".github" / "workflows" / "sync.yml"
    if patch(
        sync,
        "          python tests/global_media_type_resolution_test.py",
        "          python tests/global_media_type_pre_network_gate_test.py\n          python tests/global_media_type_resolution_test.py",
        "CORE Quick media fast gate",
        all_occurrences=True,
    ):
        changed.append(str(sync.relative_to(ROOT)))

    print("NON_REGRESSION_OWNERSHIP_MIGRATION changed=" + (",".join(changed) if changed else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
