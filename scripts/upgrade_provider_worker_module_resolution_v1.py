#!/usr/bin/env python3
"""Let temp-copied providers resolve pinned repository dependencies safely.

Route recognition executes upstream Provider JS from a temporary directory. Bare
package imports therefore cannot see NiakVIO's node_modules even though the exact
runtime dependencies are installed and locked. This migration adds a fallback
resolution root for bare packages only. Blocked Node built-ins remain blocked, and
relative/absolute provider imports are never redirected.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_worker.cjs"
MARKER = "NIAKVIO_PROVIDER_WORKER_PACKAGE_RESOLUTION_V1"


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
    new = '''/* NIAKVIO_PROVIDER_WORKER_PACKAGE_RESOLUTION_V1 */
function installModuleRestrictions() {
  const originalLoad = Module._load;
  const packageRequire = Module.createRequire(path.join(__dirname, '..', 'package.json'));
  const isBarePackage = (request) => {
    const value = String(request || '').trim();
    return Boolean(value && !value.startsWith('.') && !path.isAbsolute(value) && !value.startsWith('node:'));
  };
  Module._load = function restrictedLoad(request, parent, isMain) {
    if (blockedProviderModule(request)) throw new Error(`provider module blocked: ${request}`);
    try {
      return originalLoad.call(this, request, parent, isMain);
    } catch (error) {
      if (!isBarePackage(request) || error?.code !== 'MODULE_NOT_FOUND') throw error;
      // Providers are copied to a temp directory for isolation, so bare packages
      // cannot naturally reach the repository's pinned node_modules. Resolve the
      // exact package from NiakVIO's package root, then load that resolved file.
      const resolved = packageRequire.resolve(request);
      return originalLoad.call(this, resolved, parent, isMain);
    }
  };
'''
    text = once(text, old, new, "provider-package-resolution")
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "Module.createRequire(path.join(__dirname, '..', 'package.json'))",
        "isBarePackage",
        "error?.code !== 'MODULE_NOT_FOUND'",
        "packageRequire.resolve(request)",
        "blockedProviderModule(request)",
    ):
        if needle not in value:
            raise AssertionError(f"provider package resolution missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_WORKER_PACKAGE_RESOLUTION_V1_OK changed={str(changed).lower()} "
        "bare_packages_from_repo=1 blocked_builtins_preserved=1 relative_redirect=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
