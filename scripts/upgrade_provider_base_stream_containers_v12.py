#!/usr/bin/env python3
"""Teach the common ProviderBase recipe parser explicit plural stream containers.

Some resolver APIs (PlayIMDb is the current proof case) return media URLs under
`stream_urls` / `streamUrls`. The generic parser previously understood only
singular stream/url/source fields and therefore discarded an otherwise valid
resolver response. This migration adds only narrowly named stream containers;
it does not treat arbitrary HTTP strings in JSON as playable media.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_base_store.py"
MARKER = "NIAKVIO_PROVIDER_BASE_STREAM_CONTAINERS_V12"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    old = '''function _sourceUrls(value, base, out) {
out = out || [];
if (Array.isArray(value)) {
for (const child of value) _sourceUrls(child, base, out);
return out;
}
if (!value || typeof value !== "object") return out;
for (const [key, child] of Object.entries(value)) {
if (typeof child === "string" && /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key)) {
const absolute = _absolute(child, base);
if (absolute && /^https?:/i.test(absolute) &&
!/\\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) {
out.push(absolute);
}
}
if (child && typeof child === "object") _sourceUrls(child, base, out);
}
return out;
}
'''
    new = '''/* NIAKVIO_PROVIDER_BASE_STREAM_CONTAINERS_V12 */
function _sourceUrls(value, base, out, streamContainer) {
out = out || [];
if (typeof value === "string") {
if (streamContainer) {
const absolute = _absolute(value, base);
if (absolute && /^https?:/i.test(absolute) &&
!/\\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) out.push(absolute);
}
return out;
}
if (Array.isArray(value)) {
for (const child of value) _sourceUrls(child, base, out, streamContainer);
return out;
}
if (!value || typeof value !== "object") return out;
for (const [key, child] of Object.entries(value)) {
const directField = /^(?:src|url|file|stream|stream_url|streamUrl|source|source_url|sourceUrl)$/i.test(key);
const pluralStreamContainer = /^(?:stream_urls|streamUrls)$/i.test(key);
if (typeof child === "string" && directField) {
const absolute = _absolute(child, base);
if (absolute && /^https?:/i.test(absolute) &&
!/\\.(?:jpe?g|png|gif|webp|svg|avif)(?:[?#]|$)/i.test(absolute)) {
out.push(absolute);
}
}
if (child && typeof child === "object") _sourceUrls(child, base, out, pluralStreamContainer);
}
return out;
}
'''
    text = once(text, old, new, "source-url-stream-containers")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"stream container marker count={value.count(MARKER)}")
    for needle in (
        "function _sourceUrls(value, base, out, streamContainer)",
        "pluralStreamContainer",
        "/^(?:stream_urls|streamUrls)$/i",
        "_sourceUrls(child, base, out, pluralStreamContainer)",
    ):
        if needle not in value:
            raise AssertionError(f"stream container runtime missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_BASE_STREAM_CONTAINERS_V12_OK changed={str(changed).lower()} "
        "stream_urls=1 arbitrary_http_strings=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
