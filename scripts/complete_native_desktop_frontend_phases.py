#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"desktop frontend phase anchor {label!r} count={count}")
    return text.replace(old, new, 1)


def canonicalize_http_terminal_phases(text: str) -> str:
    # The native evidence contract defines a terminal HTTP phase as either a
    # response or an error. Older desktop augmentation emitted a misleading
    # *-http-response phase even when FIELD_NATIVE_*_HTTP_ERROR was terminal.
    # Normalize those generated calls before adding any missing phases.
    return (
        text.replace(
            'captureDesktopPhase("repository-http-response",',
            'captureDesktopPhase("repository-http-terminal",',
        )
        .replace(
            'captureDesktopPhase("provider-http-response",',
            'captureDesktopPhase("provider-http-terminal",',
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()
    path = Path(args.source).resolve()
    original = path.read_text(encoding="utf-8")
    text = canonicalize_http_terminal_phases(original)
    if 'captureDesktopPhase("ui-launched", fixtureSlug)' in text:
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"FIELD_NATIVE_DESKTOP_FRONTEND_PHASES source={path} canonicalized=true")
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
        '                captureDesktopPhase("provider-http-terminal", fixtureSlug)\n                captureDesktopPhase("provider-result", fixtureSlug)',
        "provider terminal",
    )
    path.write_text(text, encoding="utf-8")
    print(f"FIELD_NATIVE_DESKTOP_FRONTEND_PHASES source={path} canonicalized=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
