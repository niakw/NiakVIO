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
    if 'captureDesktopPhase("ui-launched"' in text:
        return 0
    text = replace_once(
        text,
        '        captureDesktopPhase("corpus-begin", fixtureSlug)',
        '        captureDesktopPhase("ui-launched", fixtureSlug)\n        captureDesktopPhase("corpus-begin", fixtureSlug)',
        "ui launch",
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
