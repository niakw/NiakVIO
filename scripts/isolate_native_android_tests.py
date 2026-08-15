#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def isolate(root: Path, keep: Path) -> None:
    if not root.is_dir():
        raise SystemExit(f"native Android test root missing: {root}")
    keep = keep.resolve()
    removed: list[Path] = []
    kept = False
    for pattern in ("*.kt", "*.java"):
        for source in sorted(root.rglob(pattern)):
            resolved = source.resolve()
            if resolved == keep:
                kept = True
                continue
            source.unlink()
            removed.append(source)
    if not kept or not keep.is_file():
        raise SystemExit(f"injected NiakVIO test missing after isolation: {keep}")
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass
    print(f"FIELD_NATIVE_TEST_ISOLATION root={root} removed={len(removed)} kept={keep}")
    for source in removed:
        print(f"FIELD_NATIVE_TEST_REMOVED path={source}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("mobile", "tv"))
    parser.add_argument("repo")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if args.target == "mobile":
        root = repo / "composeApp/src/androidDeviceTest"
        keep = root / "kotlin/com/nuvio/app/features/plugins/NiakvioFinalNativeMobileTest.kt"
    else:
        root = repo / "app/src/androidTest"
        keep = root / "java/com/nuvio/tv/core/plugin/NiakvioFinalNativeTvTest.kt"

    isolate(root, keep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
