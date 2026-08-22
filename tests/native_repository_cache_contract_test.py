#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".native-repository-cache-contract"
MANIFEST = TMP / "manifest.json"
RESOLVER = ROOT / "scripts/resolve_native_repository.sh"


def resolve_cache_key() -> tuple[str, str]:
    script = f'''
set -euo pipefail
WORKSPACE="{TMP / 'workspace'}"
NIAKVIO="{ROOT}"
TARGET_MANIFEST="{MANIFEST.relative_to(ROOT).as_posix()}"
SOURCE_SHA="$(git -C "$NIAKVIO" rev-parse HEAD)"
SOURCE_REPOSITORY="niakw/NiakVIO"
source "{RESOLVER}"
resolve_native_repository desktop 127.0.0.1 18979
printf 'RESOLVED_URL=%s\n' "$NIAKVIO_RESOLVED_MANIFEST_URL"
printf 'RESOLVED_KEY=%s\n' "$NIAKVIO_LOCAL_REPOSITORY_KEY"
cleanup_native_repository
'''
    env = os.environ.copy()
    # A runner-level proxy must never intercept the loopback readiness probe.
    # This reproduces the failure mode seen on GitHub-hosted macOS runners.
    env.update(
        {
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "",
            "no_proxy": "",
        }
    )
    run = subprocess.run(
        ["bash", "-lc", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    url = re.search(r"^RESOLVED_URL=(.+)$", run.stdout, re.MULTILINE)
    key = re.search(r"^RESOLVED_KEY=([0-9a-f]{32})$", run.stdout, re.MULTILINE)
    assert url, run.stdout
    assert key, run.stdout
    assert f"/candidate-{key.group(1)}/manifest.json" in url.group(1)
    assert "mode=local_candidate" in run.stdout
    return url.group(1), key.group(1)


try:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True)
    source_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    source_rows = [row for row in source_manifest.get("scrapers", []) if isinstance(row, dict) and row.get("filename")]
    assert source_rows

    # One valid provider is enough to prove the cache-addressing contract. The
    # filename remains repository-relative, exactly as Nuvio resolves it.
    candidate = {
        "name": "NiakVIO cache contract A",
        "version": "1",
        "scrapers": [source_rows[0]],
    }
    MANIFEST.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    url_a1, key_a1 = resolve_cache_key()
    url_a2, key_a2 = resolve_cache_key()
    assert key_a1 == key_a2, "identical candidate must retain the same cache key"
    assert url_a1 == url_a2, "identical candidate must retain the same repository URL"

    # Changing only manifest bytes must invalidate the persistent provider cache.
    candidate["name"] = "NiakVIO cache contract B"
    MANIFEST.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    url_b, key_b = resolve_cache_key()
    assert key_b != key_a1, "changed candidate must get a new content-addressed cache key"
    assert url_b != url_a1, "changed candidate must get a new repository URL"

    resolver_text = RESOLVER.read_text(encoding="utf-8")
    for required in (
        "content-addressed",
        "candidate-${content_key}",
        "manifest + every provider",
        "NIAKVIO_LOCAL_REPOSITORY_KEY",
        'http.client.HTTPConnection("127.0.0.1", port, timeout=1.0)',
    ):
        assert required in resolver_text, required
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print("native repository cache contract tests passed")
