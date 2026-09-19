#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checkpoint = load_module("native_tv_route_checkpoint", ROOT / "scripts/native_tv_route_checkpoint.py")
retest = load_module("build_native_reader_retest_manifest", ROOT / "scripts/build_native_reader_retest_manifest.py")

with tempfile.TemporaryDirectory() as tmp_raw:
    tmp = Path(tmp_raw)
    client = tmp / "nuvio-tv"
    client.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=client, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=client, check=True)
    subprocess.run(["git", "config", "user.name", "NiakVIO Test"], cwd=client, check=True)
    (client / "README").write_text("client-v1\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=client, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "v1"], cwd=client, check=True)

    manifest = tmp / "manifest.json"
    manifest.write_text('{"scrapers":[]}\n', encoding="utf-8")
    log = tmp / "route.log"
    log.write_text("FIELD_NATIVE_CORPUS_END fixture=test\n", encoding="utf-8")
    checkpoint_path = tmp / "checkpoint.json"

    base = dict(
        checkpoint=checkpoint_path,
        log=log,
        fixture="test-fixture",
        manifest=manifest,
        client_root=client,
        provider_scope="all",
        stream_scope="all",
    )
    record_args = argparse.Namespace(
        **base,
        runtime_status=0,
        collection_status=0,
        coverage_status=0,
        reader_status=0,
    )
    assert checkpoint.record(record_args) == 0
    assert checkpoint.verify(argparse.Namespace(**base)) == 0
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert payload["complete"] is True
    assert len(payload["manifestSha256"]) == 64
    assert len(payload["clientSha"]) == 40
    assert len(payload["logSha256"]) == 64

    log.write_text("tampered\n", encoding="utf-8")
    assert checkpoint.verify(argparse.Namespace(**base)) == 1
    log.write_text("FIELD_NATIVE_CORPUS_END fixture=test\n", encoding="utf-8")
    assert checkpoint.verify(argparse.Namespace(**base)) == 0

    manifest.write_text('{"scrapers":[],"version":"changed"}\n', encoding="utf-8")
    assert checkpoint.verify(argparse.Namespace(**base)) == 1
    manifest.write_text('{"scrapers":[]}\n', encoding="utf-8")
    assert checkpoint.verify(argparse.Namespace(**base)) == 0

    (client / "README").write_text("client-v2\n", encoding="utf-8")
    subprocess.run(["git", "add", "README"], cwd=client, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "v2"], cwd=client, check=True)
    assert checkpoint.verify(argparse.Namespace(**base)) == 1

    failure_args = argparse.Namespace(
        **base,
        runtime_status=124,
        collection_status=1,
        coverage_status=1,
        reader_status=1,
    )
    assert checkpoint.record(failure_args) == 0
    assert checkpoint.verify(argparse.Namespace(**base)) == 1

manifest_payload = {
    "name": "test",
    "scrapers": [
        {"id": "mut-a", "enabled": True, "supportedTypes": ["movie"], "filename": "providers/a.js"},
        {"id": "mut-b", "enabled": False, "supportedTypes": ["tv"], "filename": "providers/b.js"},
        {"id": "alpha", "enabled": True, "supportedTypes": ["movie", "tv"], "filename": "providers/c.js"},
        {"id": "beta", "enabled": True, "supportedTypes": ["anime"], "filename": "providers/d.js"},
        {"id": "gamma", "enabled": True, "supportedTypes": ["tv"], "filename": "providers/e.js"},
        {"id": "disabled-sentinel", "enabled": False, "supportedTypes": ["anime"], "filename": "providers/f.js"},
    ],
}
repair_report = {"providers": ["mut-a", "MUT-B"], "proposalCount": 2}
bounded_manifest, scope = retest.build_scope(manifest_payload, repair_report)
selected = {str(row["id"]).casefold() for row in bounded_manifest["scrapers"]}
assert {"mut-a", "mut-b"} <= selected
assert scope["mutationCount"] == 2
assert scope["fullCatalogueRetest"] is False
assert scope["policy"]["providerSpecificExceptions"] is False
assert scope["sentinelTypes"]
assert len(scope["sentinelProviders"]) <= 3
assert scope["selectedCount"] <= scope["mutationCount"] + 3
assert "disabled-sentinel" not in scope["sentinelProviders"]
for media_type in retest.MEDIA_TYPES:
    assert any(media_type in values for values in scope["sentinelTypes"].values()), media_type

try:
    retest.build_scope(manifest_payload, {"providers": []})
except ValueError as exc:
    assert "no mutated providers" in str(exc)
else:
    raise AssertionError("empty repair scope must fail closed")

print("Native TV route checkpoint and bounded Brain retest tests passed")
