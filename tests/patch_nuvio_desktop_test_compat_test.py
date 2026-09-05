#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "patch_nuvio_desktop_test_compat.py"
spec = importlib.util.spec_from_file_location("patch_nuvio_desktop_test_compat", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp)
        interface = checkout / module.INTERFACE
        test = checkout / module.TEST
        interface.parent.mkdir(parents=True)
        test.parent.mkdir(parents=True)

        interface.write_text(
            "interface PlayerEngineController {\n"
            "    fun applyAudioLanguagePreferences(languages: List<String>)\n"
            "}\n",
            encoding="utf-8",
        )
        test.write_text(
            "val controller = object : PlayerEngineController {\n"
            + module.ANCHOR
            + "\n}\n",
            encoding="utf-8",
        )

        assert module.patch(checkout) == "applied"
        updated = test.read_text(encoding="utf-8")
        assert updated.count(module.OVERRIDE) == 1
        assert module.patch(checkout) == "already_compatible"
        assert test.read_text(encoding="utf-8") == updated

        test.write_text("structure changed\n", encoding="utf-8")
        try:
            module.patch(checkout)
        except ValueError as exc:
            assert "structure changed" in str(exc)
        else:
            raise AssertionError("changed upstream structure must fail closed")

    print("NuvioDesktop test compatibility patch tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
