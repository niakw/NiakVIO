#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / "scripts/prepare_native_reader_acceptance.py"
spec = importlib.util.spec_from_file_location("prepare_native_reader_acceptance", module_path)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def source(client: str) -> str:
    return f'''package example\n\nimport android.util.Log\nimport androidx.test.platform.app.InstrumentationRegistry\nimport org.junit.Test\n\nclass Sample {{\n    private fun b64(v: Any?) = ""\n    private fun hostOnly(v: String) = ""\n    private fun probeTransport(url: String, headers: Map<String,String>?) = TODO()\n\n    @Test\n    fun run() {{\n        val fixtureSlug = "sinners-2025"\n        val provider = object {{ val id = "MOVIESDRIVE" }}\n        val rows = emptyList<dynamic>()\n                rows.take(3).forEachIndexed {{ index, row ->\n                    emit("FIELD_NATIVE_ROW client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} index=$index")\n                }}\n                rows.firstOrNull()?.let {{ row ->\n                    val probe = probeTransport(row.url, row.headers)\n                    emit("FIELD_NATIVE_TRANSPORT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=${{probe.state}} kind=${{probe.kind}} status=${{probe.status}} content_type64=${{b64(probe.contentType)}} extm3u=${{probe.extm3u}} duration_seconds=${{probe.durationSeconds ?: 0.0}} host64=${{b64(probe.host)}} media_hint64=${{b64(probe.mediaHint)}}")\n                }}\n    }}\n    private fun emit(v: String) {{}}\n}}\n'''


out = mod.reader_source(source("tv"), "tv", 137, "all")
assert "rows.take(" not in out
assert out.count("rows.forEachIndexed") >= 2
assert "PlayerPlaybackNetworking.createDataSourceFactory(context, headers)" in out
assert out.index("val reader = probeNativePlayer") < out.index("val transport = probeTransport")

sampled = mod.reader_source(source("tv"), "tv", 137, 2)
assert "rows.take(2).forEachIndexed" in sampled
assert "rows.take(3).forEachIndexed" in sampled

# Curated fixture scope remains available for a manual/targeted diagnosis. Its
# ordering is deliberate: the PR-bounded lab consumes the first canaries exactly
# in this order, while deep acceptance below still traverses the whole manifest.
selected_fixture = mod.select_providers("manifest.json", "sinners-2025", "fixture")
fixture_ids = [str(row["id"]).casefold() for row in selected_fixture]
assert fixture_ids == [
    "cineby",
    "movieshunt",
    "videasy",
    "vixsrc",
    "moviesdrive",
    "moviesmod",
    "4khdhub",
], fixture_ids
assert "4khdhubnew" not in fixture_ids

# Acceptance scope is intentionally exhaustive and includes inactive providers.
selected_all = mod.select_providers("manifest.json", "sinners-2025", "all")
manifest_all = mod.client_prepare.manifest_providers("manifest.json")
all_ids = [str(row["id"]).casefold() for row in selected_all]
assert len(selected_all) == len(manifest_all) >= 90, (len(selected_all), len(manifest_all))
assert len(set(all_ids)) == len(all_ids)
assert any(not bool(row.get("enabled")) for row in selected_all), "inactive providers must stay in reader lab scope"
assert any(bool(row.get("enabled")) for row in selected_all), "active providers must stay in reader lab scope"

config = json.loads((ROOT / ".github/triggers/nuvio-client-lab.json").read_text(encoding="utf-8"))
acceptance = config["native_reader_acceptance"]
assert acceptance["provider_scope"] == "all"
assert acceptance["include_disabled"] is True
assert acceptance["publication_requires_fresh_reader_proof"] is True
for suite in ("scripts/run_native_corpus_tv_suite.sh", "scripts/run_native_corpus_mobile_suite.sh"):
    text = (ROOT / suite).read_text(encoding="utf-8")
    assert "CONFIGURED_ACCEPTANCE_PROVIDER_SCOPE" in text
    assert 'if [[ -z "$PROVIDER_SCOPE" || "$PROVIDER_SCOPE" = "all" ]]; then PROVIDER_SCOPE="fixture"; fi' not in text

b64 = lambda value: __import__("base64").urlsafe_b64encode(value.encode()).decode().rstrip("=")
with tempfile.TemporaryDirectory() as tmp:
    log = Path(tmp) / "reader.log"
    lines = [
        "FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=sinners-2025 title64=x providers=1",
        f"FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64={b64('MOVIESDRIVE')} enabled=true duration_ms=1 count=9",
    ]
    for index in range(3):
        lines.append(f"FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64={b64('MOVIESDRIVE')} index={index} state=error")
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    failed = subprocess.run(
        ["node", str(ROOT / "scripts/gate_native_reader_coverage.cjs"), "--streams", "all", str(log)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert "returned=9" in failed.stdout and "played=3" in failed.stdout
    assert "ci_mode=deep" in failed.stdout

    # PR acceptance has exactly one canonical coverage floor: at least one real
    # native read for every route that returned media. The generator may choose a
    # larger bounded sample; the gate must not independently re-invent that count.
    pr_env = dict(os.environ, GITHUB_EVENT_NAME="pull_request")
    pr_bounded = subprocess.run(
        ["node", str(ROOT / "scripts/gate_native_reader_coverage.cjs"), "--streams", "all", str(log)],
        cwd=ROOT, text=True, capture_output=True, env=pr_env,
    )
    assert pr_bounded.returncode == 0, pr_bounded.stdout + pr_bounded.stderr
    assert "ci_mode=pr-bounded" in pr_bounded.stdout
    assert "expected_played=1 played=3" in pr_bounded.stdout

    sampled_pass = subprocess.run(
        ["node", str(ROOT / "scripts/gate_native_reader_coverage.cjs"), "--streams", "3", str(log)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert sampled_pass.returncode == 0, sampled_pass.stdout + sampled_pass.stderr
    assert "expected_played=3 played=3" in sampled_pass.stdout

    for index in range(3, 9):
        lines.append(f"FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64={b64('MOVIESDRIVE')} index={index} state=error")
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    passed = subprocess.run(
        ["node", str(ROOT / "scripts/gate_native_reader_coverage.cjs"), "--streams", "all", str(log)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert "expected_played=9 played=9" in passed.stdout

print("sampled/exhaustive native reader acceptance tests passed: pr_floor=1 deep=all")
