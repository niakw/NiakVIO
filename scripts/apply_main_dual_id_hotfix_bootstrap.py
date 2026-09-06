#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / "scripts" / "apply_main_dual_id_hotfix.py"
DUAL_ID_TEST = ROOT / "tests" / "native_dual_id_identity_test.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one repair anchor, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = PATCHER.read_text(encoding="utf-8")

    # The temporary patcher intentionally embeds generated Python/Kotlin/JS source.
    # Two outer raw single-quoted literals accidentally collided with inner r''' / f'''
    # literals. Switch only those outer delimiters to triple double-quotes.
    text = replace_once(
        text,
        "        fn = r'''\ndef inject_app_path_diagnostics(path: Path, client: str) -> None:\n",
        '        fn = r"""\ndef inject_app_path_diagnostics(path: Path, client: str) -> None:\n',
        "app-path outer literal open",
    )
    text = replace_once(
        text,
        "    print(f\"FIELD_NATIVE_PROVIDER_APP_PATH client={client} injected=true already=false\")\n'''\n        text = one(text, anchor, \"\\n\" + fn + anchor, \"app path diagnostics insertion\")\n",
        '    print(f"FIELD_NATIVE_PROVIDER_APP_PATH client={client} injected=true already=false")\n"""\n        text = one(text, anchor, "\\n" + fn + anchor, "app path diagnostics insertion")\n',
        "app-path outer literal close",
    )
    text = replace_once(
        text,
        "    p.write_text(r'''#!/usr/bin/env python3\nfrom __future__ import annotations\n",
        '    p.write_text(r"""#!/usr/bin/env python3\nfrom __future__ import annotations\n',
        "dual-id test outer literal open",
    )
    text = replace_once(
        text,
        "print(\"native dual IMDb/TMDB identity tests passed\")\n''',encoding=\"utf-8\")\n",
        'print("native dual IMDb/TMDB identity tests passed")\n""",encoding="utf-8")\n',
        "dual-id test outer literal close",
    )

    compile(text, str(PATCHER), "exec")
    PATCHER.write_text(text, encoding="utf-8")
    print("MAIN_DUAL_ID_PATCHER_SYNTAX_OK")
    subprocess.run([sys.executable, str(PATCHER)], cwd=ROOT, check=True)

    # The generated regression test deliberately stores JS snippets inside Python
    # triple-quoted strings. They must be ordinary strings so \n escapes become real
    # line breaks before Node executes them; raw strings would write literal backslash-n.
    test = DUAL_ID_TEST.read_text(encoding="utf-8")
    test = replace_once(test, "BASE=r'''", "BASE='''", "dual-id provider fixture raw prefix")
    run_count = test.count("run(r'''")
    if run_count != 2:
        raise SystemExit(f"dual-id runner fixture raw prefixes: expected 2, got {run_count}")
    test = test.replace("run(r'''", "run('''")
    compile(test, str(DUAL_ID_TEST), "exec")
    DUAL_ID_TEST.write_text(test, encoding="utf-8")
    print("MAIN_DUAL_ID_NODE_FIXTURE_SYNTAX_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
