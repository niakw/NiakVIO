#!/usr/bin/env python3
"""Instrument the NuvioDesktop plugin runtime using its shared Compose fetch bridge."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "scripts/instrument_native_client_evidence.py"


def load_base():
    spec = importlib.util.spec_from_file_location("niakvio_native_evidence", BASE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {BASE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    base = load_base()

    # Desktop and Mobile share PluginRuntime/FetchBridge in fullCommonMain at the
    # accepted NuvioDesktop revision. Reuse the exact fail-closed patch, then relabel
    # only NiakVIO's passive evidence client marker; runtime semantics stay untouched.
    base.instrument_mobile(repo)
    bridge = repo / "composeApp/src/fullCommonMain/kotlin/com/nuvio/app/features/plugins/runtime/network/FetchBridge.kt"
    text = bridge.read_text(encoding="utf-8")
    count = text.count("client=mobile")
    if count < 3:
        raise SystemExit(f"desktop evidence relabel expected >=3 mobile markers, got {count}")
    bridge.write_text(text.replace("client=mobile", "client=desktop"), encoding="utf-8")
    print(f"FIELD_NATIVE_EVIDENCE_INSTRUMENTED client=desktop bridge={bridge}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
