#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
MODULE_PATH = SCRIPTS / "apply_provider_overrides.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

CLEANUP_LINE = "    text, removed_guards = _strip_legacy_global_stream_guards(text)"


def load_module():
    spec = importlib.util.spec_from_file_location("apply_provider_overrides_order_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lines = source.splitlines()
    assert lines.count(CLEANUP_LINE) == 1, (
        "legacy guard cleanup assignment must exist exactly once as an executable Python line"
    )
    assert "structural\\n" not in source, "literal \\n leaked into transaction-order comment"

    apply_start = source.index("def apply_overrides(")
    cleanup = source.index(CLEANUP_LINE, apply_start)
    profiles = source.index('profiles = config.get("patch_profiles") or {}', apply_start)
    per_provider = source.index("for patch_script in patch_scripts if phase == \"discovery\" else []:", apply_start)
    global_integrity = source.index("if phase == \"discovery\":", per_provider)
    assert cleanup < profiles < per_provider < global_integrity, (
        cleanup,
        profiles,
        per_provider,
        global_integrity,
    )

    module = load_module()
    clean = "native-provider-code\n\n"
    untouched, count = module._strip_legacy_global_stream_guards(clean)
    assert count == 0
    assert untouched == clean, "clean bundles must not be whitespace-normalized by legacy cleanup"

    legacy = (
        "native-provider-code\n"
        "/* NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V3 */\n"
        "legacy-terminal-wrapper\n"
        "/* CURRENT_HOOK_THAT_MUST_BE_REBUILT */\n"
        "current-hook\n"
    )
    cleaned, count = module._strip_legacy_global_stream_guards(legacy)
    assert count == 1
    assert cleaned == "native-provider-code\n"

    print("override transaction ordering and no-op cleanup tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
