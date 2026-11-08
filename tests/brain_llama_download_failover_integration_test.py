#!/usr/bin/env python3
"""Exercise the ACTUAL Learning download shell from the workflow, without network.

These cases validate fallback control flow and integrity, not model inference or
real GitHub CDN availability. The real release must still match the pinned SHA.
"""
from __future__ import annotations

import hashlib
import io
import os
import subprocess
import tarfile
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/brain-learning-lab.yml"
PINNED_SHA = "460c45fa8a9ebc36c9b08e3a15c06dbdbeb312c6308599521c84d9e7f92a268b"

workflow = WORKFLOW.read_text(encoding="utf-8")
start = workflow.index("      - name: Download and verify official llama.cpp binary when needed")
end = workflow.index("      - uses: actions/cache@", start)
block = workflow[start:end]
assert "continue-on-error: true" in block
assert "        run: |\n" in block
script = textwrap.dedent(block.split("        run: |\n", 1)[1]).strip() + "\n"
assert script.count("expected_sha='" + PINNED_SHA + "'") == 1
assert script.count("sha256sum -c -") == 1
assert script.index("sha256sum -c -") < script.index("tar -xzf")
assert script.count("https://github.com/ggml-org/llama.cpp/releases/download/b11140/") == 1
assert script.count("https://api.github.com/repos/ggml-org/llama.cpp/releases/assets/584287303") == 1

# The fake curl sees the exact production URLs/arguments. The tested body is
# byte-for-byte the production shell except the digest of this tiny local tar.
fake_curl = r"""#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

args = sys.argv[1:]
url = next((a for a in args if a.startswith("https://")), "")
if "-o" not in args or not url:
    sys.exit(63)
dst = Path(args[args.index("-o") + 1])
mode = os.environ["FAKE_CURL_MODE"]
with open(os.environ["FAKE_CURL_TRACE"], "a", encoding="utf-8") as log:
    log.write(url + "\n")
if "releases/download/b11140/" in url and mode == "primary_ok":
    shutil.copyfile(os.environ["FAKE_CURL_ARCHIVE"], dst)
    sys.exit(0)
if "releases/download/b11140/" in url:
    # Simulate a partial CDN response followed by a 504.
    dst.write_bytes(b"partial-CND-504")
    sys.exit(22)
if "releases/assets/584287303" in url and mode == "fallback_ok":
    shutil.copyfile(os.environ["FAKE_CURL_ARCHIVE"], dst)
    sys.exit(0)
if "releases/assets/584287303" in url and mode == "fallback_metadata":
    # The official API may respond with JSON metadata, not archive bytes.
    dst.write_bytes(b'{"name":"llama-b11140-bin-ubuntu-x64.tar.gz"}')
    sys.exit(0)
sys.exit(64)
"""

with tempfile.TemporaryDirectory() as root:
    work = Path(root)
    archive = work / "local-b11140.tar.gz"
    executable = b"#!/bin/sh\nexit 0\n"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("release/bin/llama-server")
        info.size = len(executable)
        info.mode = 0o755
        tar.addfile(info, io.BytesIO(executable))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    live_script = script.replace("expected_sha='" + PINNED_SHA + "'",
                                 "expected_sha='" + digest + "'", 1)
    assert live_script != script
    fake_bin = work / "fake-bin"
    fake_bin.mkdir()
    curl = fake_bin / "curl"
    curl.write_text(fake_curl, encoding="utf-8")
    curl.chmod(0o755)

    for mode, should_succeed, expected_calls in (
        ("primary_ok", True, 1),
        ("fallback_ok", True, 2),
        ("fallback_metadata", False, 2),
    ):
        job = work / mode
        job.mkdir()
        trace = job / "trace.txt"
        env = os.environ.copy()
        env.update({
            "RUNNER_TEMP": str(job),
            "PATH": str(fake_bin) + os.pathsep + os.environ["PATH"],
            "FAKE_CURL_MODE": mode,
            "FAKE_CURL_TRACE": str(trace),
            "FAKE_CURL_ARCHIVE": str(archive),
        })
        result = subprocess.run(["bash", "-c", live_script], cwd=job, env=env,
                                capture_output=True, text=True, timeout=30)
        calls = trace.read_text(encoding="utf-8").splitlines()
        assert len(calls) == expected_calls, (mode, calls, result.stderr)
        found = list((job / ".brain-llm-runtime/llama-prebuilt").rglob("llama-server"))
        if should_succeed:
            assert result.returncode == 0, (mode, result.stdout, result.stderr)
            assert len(found) == 1 and found[0].read_bytes() == executable
            assert "FIELD_BRAIN_LLAMA_PREBUILT verified_sha256=true" in result.stdout
        else:
            assert result.returncode != 0, (mode, result.stdout, result.stderr)
            assert not found, (mode, found)
            assert "FIELD_BRAIN_LLAMA_PREBUILT verified_sha256=true" not in result.stdout
            assert "FAILED" in result.stdout + result.stderr or "mismatch" in result.stdout + result.stderr

print("BRAIN_LLAMA_DOWNLOAD_FAILOVER_BEHAVIOR_OK primary=verified fallback=verified corrupt=refused remote_inference=false")
