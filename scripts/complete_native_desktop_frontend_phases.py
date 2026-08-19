#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"desktop frontend phase anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()
    path = Path(args.source).resolve()
    text = path.read_text(encoding="utf-8")
    if 'captureDesktopPhase("ui-launched", fixtureSlug)' in text:
        return 0

    # The repository call itself owns the outcome. Capture "loaded" only when the
    # official Nuvio repository layer emitted a successful terminal result, and
    # capture "load-error" exactly on its terminal error. This avoids a false green
    # screenshot when addRepository() failed but the lab intentionally continued to
    # collect actionable Core/repository evidence.
    text = replace_once(
        text,
        '        val loadedProviders = loadProvidersThroughNuvio()\n',
        '        captureDesktopPhase("ui-launched", fixtureSlug)\n'
        '        captureDesktopPhase("repository-load", fixtureSlug)\n'
        '        val loadedProviders = loadProvidersThroughNuvio()\n'
        '        captureDesktopPhase("provider-load-state", fixtureSlug)\n',
        "repository loading",
    )
    repository_result = '        emit("FIELD_NATIVE_REPOSITORY_LOAD_RESULT client=desktop fixture=$fixtureSlugForLoad expected=$expectedLoaded loaded=$selectedLoaded")'
    text = replace_once(
        text,
        repository_result,
        '        captureDesktopPhase("repository-loaded", fixtureSlugForLoad)\n' + repository_result,
        "repository success",
    )
    repository_error = '                    emit("FIELD_NATIVE_REPOSITORY_LOAD_ERROR client=desktop fixture=$fixtureSlugForLoad reason=install_failed error64=${b64(installed.message)}")'
    text = replace_once(
        text,
        repository_error,
        '                    captureDesktopPhase("repository-load-error", fixtureSlugForLoad)\n' + repository_error,
        "repository error",
    )
    text = replace_once(
        text,
        '                captureDesktopPhase("provider-loading", fixtureSlug)',
        '                captureDesktopPhase("provider-loading", fixtureSlug)\n                captureDesktopPhase("provider-http-request", fixtureSlug)',
        "provider request",
    )
    text = replace_once(
        text,
        '                captureDesktopPhase("provider-result", fixtureSlug)',
        '                captureDesktopPhase("provider-http-response", fixtureSlug)\n                captureDesktopPhase("provider-result", fixtureSlug)',
        "provider response",
    )
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_DESKTOP_FRONTEND_PHASES source={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
