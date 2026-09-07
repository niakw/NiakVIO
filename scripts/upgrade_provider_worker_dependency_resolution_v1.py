#!/usr/bin/env python3
"""Resolve allowlisted provider npm dependencies from the NiakVIO project root.

Upstream provider bytes are copied to a disposable temp directory before probing.
Node normally resolves bare `require()` imports relative to that temp file, so
packages installed by `npm ci` in the repository become invisible and the provider
fails with MODULE_NOT_FOUND before any network call. Keep the sandbox boundary:
blocked builtins remain blocked and only explicitly allowlisted project packages
may fall back to the repository's package resolution context.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_worker.cjs"
MARKER = "NIAKVIO_PROVIDER_WORKER_PROJECT_DEPENDENCIES_V1"


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

    old = '''function installModuleRestrictions() {
  const originalLoad = Module._load;
  Module._load = function restrictedLoad(request, parent, isMain) {
    if (blockedProviderModule(request)) throw new Error(`provider module blocked: ${request}`);
    return originalLoad.call(this, request, parent, isMain);
  };
'''
    new = '''/* NIAKVIO_PROVIDER_WORKER_PROJECT_DEPENDENCIES_V1 */
const ALLOWED_PROVIDER_PROJECT_PACKAGES = new Set([
  "cheerio", "cheerio-without-node-native", "axios", "crypto-js", "@js-temporal/polyfill",
]);
const providerProjectRequire = Module.createRequire(path.join(__dirname, "..", "package.json"));

function providerPackageName(request) {
  const value = canonicalProviderModule(request);
  if (!value || value.startsWith(".") || value.startsWith("/")) return "";
  if (value.startsWith("@")) return value.split("/").slice(0, 2).join("/");
  return value.split("/", 1)[0];
}

function installModuleRestrictions() {
  const originalLoad = Module._load;
  Module._load = function restrictedLoad(request, parent, isMain) {
    if (blockedProviderModule(request)) throw new Error(`provider module blocked: ${request}`);
    try {
      return originalLoad.call(this, request, parent, isMain);
    } catch (error) {
      if (error?.code !== "MODULE_NOT_FOUND") throw error;
      const packageName = providerPackageName(request);
      if (!ALLOWED_PROVIDER_PROJECT_PACKAGES.has(packageName)) throw error;
      const resolved = providerProjectRequire.resolve(request);
      return originalLoad.call(this, resolved, parent, isMain);
    }
  };
'''
    text = once(text, old, new, "project-package-resolution")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    if value.count(MARKER) != 1:
        raise AssertionError(f"project dependency marker count={value.count(MARKER)}")
    for needle in (
        "ALLOWED_PROVIDER_PROJECT_PACKAGES",
        'Module.createRequire(path.join(__dirname, "..", "package.json"))',
        "providerPackageName(request)",
        'error?.code !== "MODULE_NOT_FOUND"',
        "providerProjectRequire.resolve(request)",
        "blockedProviderModule(request)",
    ):
        if needle not in value:
            raise AssertionError(f"provider dependency runtime missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_WORKER_PROJECT_DEPENDENCIES_V1_OK changed={str(changed).lower()} "
        "allowlisted_packages=5 blocked_builtins_preserved=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
