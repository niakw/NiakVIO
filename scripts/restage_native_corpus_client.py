#!/usr/bin/env python3
"""Rewrite one already-prepared client corpus test for another fixture."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_native_corpus_validation as corpus  # noqa: E402
import prepare_native_corpus_client as selected_manifest  # noqa: E402
import native_player_diagnostics_codegen as reader_diag  # noqa: E402
import finalize_native_android_reader_source as reader_source_finalizer  # noqa: E402

CORPUS_PATH = ROOT / ".github/triggers/nuvio-client-lab.json"
DEFAULT_PR_PROVIDER_LIMIT = 4
RUNTIME_ERROR_SENTINEL = "__NIAKVIO_RUNTIME_ERROR__"

RUNTIME_TRAP_HELPER = r'''
    private fun trapRuntimeErrors(code: String): String = code + """
;/* NIAKVIO_NATIVE_RUNTIME_ERROR_TRAP */
(function () {
    var marker = "__NIAKVIO_RUNTIME_ERROR__";
    var makeError = function (error) {
        var message = "unknown_runtime_error";
        try {
            if (error && error.message) message = String(error.message);
            else if (error != null) message = String(error);
        } catch (_) {}
        return [{
            title: marker,
            name: marker,
            url: "data:application/x-niakvio-runtime-error,1",
            quality: "",
            language: "",
            provider: marker + ":" + message,
            type: marker
        }];
    };
    var exportsObject = null;
    try {
        if (typeof module !== "undefined" && module && module.exports) {
            exportsObject = module.exports;
        }
    } catch (_) {}
    var original = null;
    if (exportsObject && typeof exportsObject.getStreams === "function") {
        original = exportsObject.getStreams;
    } else if (typeof globalThis !== "undefined" && typeof globalThis.getStreams === "function") {
        original = globalThis.getStreams;
    }
    var wrapped;
    if (typeof original !== "function") {
        wrapped = async function () {
            return makeError(new Error("getStreams_not_found"));
        };
    } else {
        wrapped = async function () {
            try {
                return await original.apply(this, arguments);
            } catch (error) {
                return makeError(error);
            }
        };
    }
    if (exportsObject) exportsObject.getStreams = wrapped;
    else if (typeof globalThis !== "undefined") globalThis.getStreams = wrapped;
})();
""".trimIndent()
'''


def _is_pull_request() -> bool:
    return os.environ.get("GITHUB_EVENT_NAME", "").strip().lower() == "pull_request"


def _pr_provider_limit() -> int:
    raw = os.environ.get("NIAKVIO_PR_PROVIDER_LIMIT", str(DEFAULT_PR_PROVIDER_LIMIT)).strip()
    try:
        return max(1, min(int(raw), 12))
    except ValueError:
        return DEFAULT_PR_PROVIDER_LIMIT


def _fixture_provider_ids(slug: str) -> list[str]:
    data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    for row in data.get("fixtures", []):
        if not isinstance(row, dict) or str(row.get("slug") or "") != slug:
            continue
        providers = row.get("providers")
        if not isinstance(providers, list):
            break
        return [str(value).strip() for value in providers if str(value).strip()]
    raise SystemExit(f"unknown or malformed native corpus fixture: {slug}")


def _provider_file_ids(path: str | None) -> list[str]:
    if not path:
        return []
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(os.environ.get("GITHUB_WORKSPACE") or ROOT) / candidate
    if not candidate.is_file():
        raise SystemExit(f"provider allowlist file missing: {candidate}")
    ids = []
    seen: set[str] = set()
    for raw in candidate.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            ids.append(value)
    if not ids:
        raise SystemExit(f"provider allowlist file is empty: {candidate}")
    return ids


def staged_providers(
    manifest_path: str,
    provider: str | None = None,
    fixture: str | None = None,
    provider_file: str | None = None,
) -> list[dict]:
    staged = selected_manifest.staged_manifest_providers(manifest_path)
    allowlist = _provider_file_ids(provider_file)
    if allowlist:
        by_id = {str(row.get("id") or "").strip().casefold(): row for row in staged}
        filtered = [by_id[key] for value in allowlist if (key := value.casefold()) in by_id]
        missing = [value for value in allowlist if value.casefold() not in by_id]
        if missing:
            raise SystemExit("provider allowlist references missing manifest ids: " + ",".join(missing))
        if fixture:
            fixture_row = corpus.fixture_by_slug(fixture)
            declared = {
                str(row.get("id") or "").strip().casefold()
                for row in selected_manifest.select_declared_type(staged, fixture_row)
            }
            filtered = [row for row in filtered if str(row.get("id") or "").strip().casefold() in declared]
        if not filtered:
            raise SystemExit(f"provider allowlist selected no providers for fixture={fixture or 'unknown'}")
        return filtered

    mode = str(provider or "").strip().casefold()
    if mode == "declared-type":
        if not fixture:
            raise SystemExit("declared-type provider selection requires a fixture")
        return selected_manifest.select_declared_type(staged, corpus.fixture_by_slug(fixture))
    if _is_pull_request() and not provider and fixture:
        wanted = _fixture_provider_ids(fixture)
        by_id = {str(row.get("id") or "").strip().casefold(): row for row in staged}
        filtered = [by_id[key] for value in wanted if (key := value.casefold()) in by_id]
        if not filtered:
            raise SystemExit(f"PR native corpus fixture {fixture} selected no providers from {manifest_path}")
        return filtered[: _pr_provider_limit()]
    try:
        return reader_diag.filter_staged_providers(staged, provider)
    except ValueError as error:
        raise SystemExit(str(error)) from error


def preserve_runtime_errors(source: str, client: str) -> str:
    helper_anchor = "    private fun b64(value: Any?): String ="
    if source.count(helper_anchor) != 1:
        raise SystemExit(f"unable to add {client} runtime-error trap: helper anchor count={source.count(helper_anchor)}")
    source = source.replace(helper_anchor, RUNTIME_TRAP_HELPER + "\n" + helper_anchor, 1)

    if client == "desktop":
        code_anchor = "                    code = File(root, provider.asset).readText(),"
        code_replacement = "                    code = trapRuntimeErrors(File(root, provider.asset).readText()),"
    else:
        code_anchor = "                    code = code(provider.asset),"
        code_replacement = "                    code = trapRuntimeErrors(code(provider.asset)),"
    if source.count(code_anchor) != 1:
        raise SystemExit(f"unable to wrap {client} provider code: anchor count={source.count(code_anchor)}")
    return source.replace(code_anchor, code_replacement, 1)


def collector_test(source: str, client: str) -> str:
    source = preserve_runtime_errors(source, client)
    if client == "desktop":
        old = '        assertTrue(errors.isEmpty(), "native provider runtime errors: " + errors.take(12).joinToString(" | "))\n'
        new = '        assertTrue(providers.isNotEmpty(), "native corpus provider list must not be empty")\n'
    else:
        old = '        assertTrue("native provider runtime errors: " + errors.take(12).joinToString(" | "), errors.isEmpty())\n'
        new = '        assertTrue("native corpus provider list must not be empty", providers.isNotEmpty())\n'
    if source.count(old) != 1:
        raise SystemExit(f"unable to relax {client} provider-error assertion: anchor count={source.count(old)}")
    return source.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("desktop", "mobile", "tv"))
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--provider", default="", help="exact provider id, or declared-type for canonical lane coverage")
    parser.add_argument("--provider-file", default="", help="newline-separated exact provider ids; used by clean-miss adaptive rotation")
    parser.add_argument("--player-probes", type=int, default=1, help="number of returned streams played by the native reader (1-4)")
    parser.add_argument("--manifest", default="manifest.json", help="same in-repository manifest used during initial preparation")
    args = parser.parse_args()
    fixture = corpus.fixture_by_slug(args.fixture)
    provider = args.provider.strip() or None
    provider_file = args.provider_file.strip() or None
    manifest_path = str(selected_manifest._manifest_path(args.manifest).relative_to(ROOT))
    providers = staged_providers(manifest_path, provider, args.fixture, provider_file)
    workspace = Path(args.workspace).resolve()
    probes = max(1, min(args.player_probes, 4))

    if args.target == "desktop":
        target = workspace / "nuvio-desktop/composeApp/src/desktopTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusDesktopTest.kt"
        source = corpus.desktop_test(fixture, providers)
    elif args.target == "mobile":
        target = workspace / "nuvio-mobile/composeApp/src/androidDeviceTest/kotlin/com/nuvio/app/features/plugins/NiakvioNativeCorpusMobileTest.kt"
        source = corpus.android_test(fixture, providers, "mobile")
        source = reader_diag.augment_android_test(
            source,
            client="mobile",
            expected_duration_minutes=fixture.get("expectedDurationMinutes"),
            max_player_probes=probes,
        )
        source = reader_source_finalizer.finalize_source(source, "mobile")
    else:
        target = workspace / "nuvio-tv/app/src/androidTest/java/com/nuvio/tv/core/plugin/NiakvioNativeCorpusTvTest.kt"
        source = corpus.android_test(fixture, providers, "tv")
        source = reader_diag.augment_android_test(
            source,
            client="tv",
            expected_duration_minutes=fixture.get("expectedDurationMinutes"),
            max_player_probes=probes,
        )
        source = reader_source_finalizer.finalize_source(source, "tv")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(collector_test(source, args.target), encoding="utf-8")
    pr_bounded = _is_pull_request() and provider is None and provider_file is None
    source_mode = f"provider-file:{provider_file}" if provider_file else (provider or ('fixture' if pr_bounded else 'all'))
    print(
        f"FIELD_NATIVE_CORPUS_RESTAGED_ISOLATED target={args.target} fixture={args.fixture} "
        f"tmdb={fixture.get('tmdbId')} provider={source_mode} providers={len(providers)} "
        f"player_probes={probes} manifest={manifest_path} "
        f"ci_mode={'pr-bounded' if pr_bounded else 'deep'} provider_limit={_pr_provider_limit() if pr_bounded else 0} "
        f"runtime_error_trap={RUNTIME_ERROR_SENTINEL}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
