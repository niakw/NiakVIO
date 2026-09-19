#!/usr/bin/env python3
"""Compatibility entrypoint for official native provider loading.

`restage_native_corpus_client.py` deliberately wraps generated direct-runtime code in
`trapRuntimeErrors(...)` so raw QuickJS diagnostics are not silently collapsed into
an empty result. The official repository-loading augmenter then replaces that direct
runtime call with the real Nuvio repository/manager execution path, where the staged
asset expression is no longer used.

The original augmenter intentionally matches a narrow generated-code contract. This
entrypoint removes only that diagnostic wrapper around the exact generated `code =`
argument before delegating to the canonical augmenter. It never touches provider JS,
client runtime sources, repository state, or production player code.

The request-contract executes each provider inside an `async { ... }` lambda. The
canonical provider-loading augmenter historically injected `continue` at its route
anchor, which crosses that lambda boundary and is rejected by Kotlin. Normalize only
those two generated provider-skip exits to `return@async` after the canonical transform.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANONICAL = HERE / "augment_native_provider_loading.py"


def source_argument(argv: list[str]) -> Path:
    try:
        index = argv.index("--source")
        value = argv[index + 1]
    except (ValueError, IndexError) as error:
        raise SystemExit("provider-loading compatibility entrypoint requires --source") from error
    return Path(value).resolve()


def unwrap_runtime_trap(path: Path, client: str) -> bool:
    text = path.read_text(encoding="utf-8")

    # A prebuild may already have replaced the direct runtime invocation with the
    # official repository-loading path. The in-Lab runner intentionally reuses that
    # generated source, so a second compatibility pass must be a no-op instead of
    # failing because neither the wrapped nor raw `code =` anchor exists anymore.
    if "FIELD_NATIVE_REPOSITORY_LOAD_BEGIN" in text:
        print(
            f"FIELD_NATIVE_PROVIDER_LOADING_COMPAT client={client} "
            "runtime_trap_unwrapped=false already_provider_loaded=true"
        )
        return False

    if client == "desktop":
        wrapped = "code = trapRuntimeErrors(File(root, provider.asset).readText()),"
        raw = "code = File(root, provider.asset).readText(),"
    elif client in {"mobile", "tv"}:
        wrapped = "code = trapRuntimeErrors(code(provider.asset)),"
        raw = "code = code(provider.asset),"
    else:
        raise SystemExit(f"unsupported native provider-loading client: {client}")

    count = text.count(wrapped)
    if count > 1:
        raise SystemExit(f"provider-loading runtime-trap anchor client={client} count={count}")
    if count == 1:
        path.write_text(text.replace(wrapped, raw, 1), encoding="utf-8")
        print(f"FIELD_NATIVE_PROVIDER_LOADING_COMPAT client={client} runtime_trap_unwrapped=true")
        return True

    # Acceptance-prepared sources can already be in canonical raw form. Keep the
    # entrypoint idempotent while still rejecting an unexpected generated contract.
    raw_count = text.count(raw)
    if raw_count != 1:
        raise SystemExit(
            f"provider-loading runtime-code anchor client={client} wrapped={count} raw={raw_count}"
        )
    print(f"FIELD_NATIVE_PROVIDER_LOADING_COMPAT client={client} runtime_trap_unwrapped=false")
    return False



def inject_app_path_diagnostics(path: Path, client: str) -> None:
    if client == "tv":
        print("FIELD_NATIVE_PROVIDER_APP_PATH client=tv injected=false reason=plugin_manager_path")
        return
    if client not in {"desktop", "mobile"}:
        raise SystemExit(f"unsupported app-path diagnostics client: {client}")
    text = path.read_text(encoding="utf-8")
    marker = f"FIELD_NATIVE_REPOSITORY_APP_PATH client={client}"
    if marker in text:
        print(f"FIELD_NATIVE_PROVIDER_APP_PATH client={client} injected=false already=true")
        return
    anchor = "        return byId\n    }\n"
    if text.count(anchor) != 1:
        raise SystemExit(f"provider-loading app-path return anchor client={client} count={text.count(anchor)}")
    diagnostic = f'''        val appMovieScrapers = PluginRepository.getEnabledScrapersForType("movie")
            .filter {{ it.repositoryUrl == repositoryUrl }}
        val appTvScrapers = PluginRepository.getEnabledScrapersForType("tv")
            .filter {{ it.repositoryUrl == repositoryUrl }}
        val appSeriesScrapers = PluginRepository.getEnabledScrapersForType("series")
            .filter {{ it.repositoryUrl == repositoryUrl }}
        val pluginStateForAppPath = PluginRepository.uiState.value
        emit("FIELD_NATIVE_REPOSITORY_APP_PATH client={client} fixture=$fixtureSlugForLoad plugins_enabled=${{pluginStateForAppPath.pluginsEnabled}} group_by_repository=${{pluginStateForAppPath.groupStreamsByRepository}} loaded=${{byId.size}} movie_enabled=${{appMovieScrapers.size}} tv_enabled=${{appTvScrapers.size}} series_enabled=${{appSeriesScrapers.size}}")
        return byId
    }}
'''
    path.write_text(text.replace(anchor, diagnostic, 1), encoding="utf-8")
    print(f"FIELD_NATIVE_PROVIDER_APP_PATH client={client} injected=true already=false")

def normalize_async_provider_skips(path: Path, client: str) -> None:
    text = path.read_text(encoding="utf-8")
    first = "                continue\n            }\n            val loadedScraper = loadedProviders[providerKey]"
    first_fixed = "                return@async\n            }\n            val loadedScraper = loadedProviders[providerKey]"
    second = "                continue\n            }\n            val requestRoutes = requestRoutesFor(provider.id, mediaType)"
    second_fixed = "                return@async\n            }\n            val requestRoutes = requestRoutesFor(provider.id, mediaType)"

    # Idempotency matters because a prebuild and the in-emulator corpus runner can
    # intentionally reuse the same generated test source in one long-lived Lab job.
    if first not in text and second not in text:
        if first_fixed in text and second_fixed in text:
            print(f"FIELD_NATIVE_PROVIDER_ASYNC_FLOW client={client} normalized=false already=true")
            return
        raise SystemExit(f"provider-loading async-flow anchors missing client={client}")
    if text.count(first) != 1 or text.count(second) != 1:
        raise SystemExit(
            f"provider-loading async-flow anchor count client={client} "
            f"platform={text.count(first)} load={text.count(second)}"
        )
    text = text.replace(first, first_fixed, 1).replace(second, second_fixed, 1)
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_PROVIDER_ASYNC_FLOW client={client} normalized=true already=false")


def run_canonical() -> None:
    try:
        runpy.run_path(str(CANONICAL), run_name="__main__")
    except SystemExit as error:
        if error.code not in (None, 0):
            raise


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("usage: augment_native_provider_loading_compat.py <desktop|mobile|tv> ...")
    client = sys.argv[1].strip().lower()
    source = source_argument(sys.argv)
    unwrap_runtime_trap(source, client)
    run_canonical()
    inject_app_path_diagnostics(source, client)
    normalize_async_provider_skips(source, client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
