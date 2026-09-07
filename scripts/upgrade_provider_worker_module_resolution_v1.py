#!/usr/bin/env python3
"""Let temp-copied providers resolve explicitly pinned repository dependencies safely.

Route recognition executes upstream Provider JS from a temporary directory. Bare
package imports therefore cannot see NiakVIO's node_modules even though the exact
runtime dependencies are installed and locked. This migration adds a fallback
resolution root only for packages declared in NiakVIO's top-level dependencies.

Cheerio is deliberately redirected to its `slim` parser export. The normal Node
entry imports Undici and therefore networking built-ins such as `node:net`, which
would either trip the sandbox or, if broadly allowed, create an unwanted network
bypass. Providers need Cheerio for parsing, not its Node-side transport helpers.

Blocked Node built-ins remain blocked, relative/absolute imports are never
redirected, and arbitrary transitive packages are not exposed.
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
  const packageJsonPath = path.join(__dirname, '..', 'package.json');
  const packageRequire = Module.createRequire(packageJsonPath);
  let allowedProviderPackages = new Set();
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    allowedProviderPackages = new Set(Object.keys(packageJson.dependencies || {}));
  } catch {}
  const packageRoot = (request) => {
    const value = String(request || '').trim();
    if (!value || value.startsWith('.') || path.isAbsolute(value) || value.startsWith('node:')) return '';
    const parts = value.split('/').filter(Boolean);
    if (!parts.length) return '';
    return value.startsWith('@') && parts.length >= 2 ? `${parts[0]}/${parts[1]}` : parts[0];
  };
  const safeProviderPackageRequest = (request) => {
    const value = String(request || '').trim();
    // Both names resolve to the same pinned Cheerio package in this repository.
    // Force parser-only code so the sandbox never has to permit Undici/node:net.
    if (value === 'cheerio' || value === 'cheerio-without-node-native') return 'cheerio/slim';
    return value;
  };
  Module._load = function restrictedLoad(request, parent, isMain) {
    if (blockedProviderModule(request)) throw new Error(`provider module blocked: ${request}`);
    try {
      return originalLoad.call(this, request, parent, isMain);
    } catch (error) {
      const root = packageRoot(request);
      if (!root || !allowedProviderPackages.has(root) || error?.code !== 'MODULE_NOT_FOUND') throw error;
      // Providers are copied to a temp directory for isolation, so approved bare
      // packages cannot naturally reach the repository's pinned node_modules.
      // Resolve only an explicitly declared dependency from NiakVIO's package root.
      const resolved = packageRequire.resolve(safeProviderPackageRequest(request));
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
        "Module.createRequire(packageJsonPath)",
        "allowedProviderPackages",
        "Object.keys(packageJson.dependencies || {})",
        "packageRoot",
        "safeProviderPackageRequest",
        "value === 'cheerio' || value === 'cheerio-without-node-native'",
        "return 'cheerio/slim'",
        "!allowedProviderPackages.has(root)",
        "error?.code !== 'MODULE_NOT_FOUND'",
        "packageRequire.resolve(safeProviderPackageRequest(request))",
        "blockedProviderModule(request)",
    ):
        if needle not in value:
            raise AssertionError(f"provider package resolution missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_WORKER_PACKAGE_RESOLUTION_V1_OK changed={str(changed).lower()} "
        "declared_packages_only=1 cheerio_slim=1 blocked_builtins_preserved=1 "
        "relative_redirect=0 transitive_exposure=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
