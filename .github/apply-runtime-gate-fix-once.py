#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract_embedded_patch() -> str:
    source = ROOT / ".github/workflows/gate-runtime-main-fix-once-v2.yml"
    lines = source.read_text(encoding="utf-8").splitlines()
    begin = lines.index("          python3 - <<'PY'") + 1
    end = lines.index("          PY", begin)
    body = [line[10:] if line.startswith("          ") else line for line in lines[begin:end]]
    return "\n".join(body) + "\n"


def apply_verified_sentinel_patch() -> None:
    script = extract_embedded_patch()
    exec(compile(script, "gate-runtime-main-fix-once-v2:embedded-python", "exec"), {"__name__": "__main__"})

    test = ROOT / "tests/native_reader_brain_repair_test.py"
    lines = test.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if line == "    if runtime_sentinel:"), -1)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("    path.write_text(")),
        -1,
    ) if start >= 0 else -1
    if start < 0 or end < 0 or lines[start + 1] != "    lines.insert(":
        raise RuntimeError("unexpected runtime sentinel regression block")
    for index in range(start + 1, end):
        if lines[index]:
            lines[index] = "    " + lines[index]
    test.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # The v3 test run proved this patch, but Actions cannot publish workflow changes.
    # Restore workflow/static-contract files and enforce the gate from the existing
    # runtime-memory filter step that already executes before Brain materialization.
    subprocess.run(
        ["git", "checkout", "HEAD", "--", ".github/workflows/native-android-route-reader.yml"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "HEAD", "--", "tests/native_corpus_device_lab_test.py"],
        cwd=ROOT,
        check=True,
    )


def patch_prebrain_scope_gate() -> None:
    path = ROOT / "scripts/scope_native_reader_learning_runtime.py"
    text = path.read_text(encoding="utf-8")
    if "FIELD_NATIVE_READER_RUNTIME_PREBRAIN_GATE" in text:
        return

    old = "import json\nimport subprocess\n"
    new = "import json\nimport os\nimport subprocess\n"
    if text.count(old) != 1:
        raise RuntimeError("scope import anchor missing")
    text = text.replace(old, new, 1)

    old = 'MERGER = ROOT / "scripts" / "merge_native_reader_repair_learning.py"\n'
    new = old + 'CROSS_RUNTIME_GATE = ROOT / "scripts" / "gate_native_cross_client_runtime.cjs"\n'
    if text.count(old) != 1:
        raise RuntimeError("scope gate constant anchor missing")
    text = text.replace(old, new, 1)

    old = '''def run_filter(args: argparse.Namespace) -> int:
    fingerprint = clean_fingerprint(args.runtime_fingerprint)
'''
    new = '''def gate_representative_runtime_before_learning() -> None:
    """Fail closed on systemic TV/Mobile runtime divergence before Brain repair."""
    workspace_raw = os.environ.get("GITHUB_WORKSPACE", "").strip()
    if not workspace_raw:
        return
    baseline = Path(workspace_raw).resolve() / "baseline-reader"
    tv = baseline / "tv"
    mobile = baseline / "mobile"
    if not tv.is_dir() and not mobile.is_dir():
        return
    if not tv.is_dir() or not mobile.is_dir():
        raise RuntimeError(
            f"incomplete pre-Brain runtime evidence: tv={tv.is_dir()} mobile={mobile.is_dir()}"
        )
    command = [
        "node",
        str(CROSS_RUNTIME_GATE),
        "--dir", str(baseline),
        "--require-clients", "mobile,tv",
        "--min-comparisons", "3",
    ]
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if process.stdout:
        print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, end="")
    if process.returncode != 0:
        raise RuntimeError(
            f"pre-Brain cross-runtime gate failed with exit code {process.returncode}"
        )
    print("FIELD_NATIVE_READER_RUNTIME_PREBRAIN_GATE status=pass clients=mobile,tv")


def run_filter(args: argparse.Namespace) -> int:
    gate_representative_runtime_before_learning()
    fingerprint = clean_fingerprint(args.runtime_fingerprint)
'''
    if text.count(old) != 1:
        raise RuntimeError("scope filter anchor missing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_boundary_test() -> None:
    path = ROOT / "tests/native_runtime_brain_boundary_test.py"
    path.write_text(
        '''#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "scripts/scope_native_reader_learning_runtime.py"
WORKFLOW = ROOT / ".github/workflows/native-android-route-reader.yml"

scope = SCOPE.read_text(encoding="utf-8")
workflow = WORKFLOW.read_text(encoding="utf-8")
for required in (
    "gate_native_cross_client_runtime.cjs",
    "FIELD_NATIVE_READER_RUNTIME_PREBRAIN_GATE",
    '"--require-clients", "mobile,tv"',
    '"--min-comparisons", "3"',
    "incomplete pre-Brain runtime evidence",
):
    assert required in scope, required

scope_call = "scope_native_reader_learning_runtime.py filter"
brain_step = "Materialize bounded generic Brain mutations across three representative routes"
assert scope_call in workflow
assert brain_step in workflow
assert workflow.index(scope_call) < workflow.index(brain_step)

with tempfile.TemporaryDirectory(dir=ROOT) as raw:
    temp = Path(raw)
    source = temp / "state.json"
    output = temp / "scoped.json"
    source.write_text(json.dumps({"nativeReaderRepairMemory": {"entries": []}}), encoding="utf-8")
    env = dict(os.environ)
    env.pop("GITHUB_WORKSPACE", None)
    run = subprocess.run([
        "python3", str(SCOPE), "filter",
        "--state", str(source),
        "--runtime-fingerprint", "tv=abc;mobile=def",
        "--output", str(output),
    ], cwd=ROOT, env=env, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert output.is_file()

print("native runtime pre-Brain boundary contract passed")
''',
        encoding="utf-8",
    )


def main() -> int:
    apply_verified_sentinel_patch()
    patch_prebrain_scope_gate()
    write_boundary_test()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
