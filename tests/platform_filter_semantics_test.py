#!/usr/bin/env python3
from __future__ import annotations


def allowed(row: dict, tags: set[str]) -> bool:
    supported = {str(value).lower() for value in row.get("supportedPlatforms") or []}
    disabled = {str(value).lower() for value in row.get("disabledPlatforms") or []}
    if supported and tags.isdisjoint(supported):
        return False
    if not tags.isdisjoint(disabled):
        return False
    return True


clients = {
    "android": {"android"},
    "ios": {"ios"},
    "windows": {"desktop", "jvm", "windows"},
    "macos": {"desktop", "jvm", "macos"},
    "linux": {"desktop", "jvm", "linux"},
}

# A desktop block must cover every JVM desktop OS without affecting mobile.
row = {"disabledPlatforms": ["desktop"]}
assert not allowed(row, clients["windows"])
assert not allowed(row, clients["macos"])
assert not allowed(row, clients["linux"])
assert allowed(row, clients["android"])
assert allowed(row, clients["ios"])

# OS-specific blocks remain possible when evidence is OS-specific.
row = {"disabledPlatforms": ["windows"]}
assert not allowed(row, clients["windows"])
assert allowed(row, clients["macos"])
assert allowed(row, clients["linux"])

# Mobile tokens are independent.
row = {"disabledPlatforms": ["android"]}
assert not allowed(row, clients["android"])
assert allowed(row, clients["ios"])
assert allowed(row, clients["windows"])

# supportedPlatforms uses intersection semantics exactly like Nuvio Desktop.
row = {"supportedPlatforms": ["desktop"]}
assert allowed(row, clients["windows"])
assert allowed(row, clients["macos"])
assert allowed(row, clients["linux"])
assert not allowed(row, clients["android"])
assert not allowed(row, clients["ios"])

row = {"supportedPlatforms": ["ios", "android"]}
assert allowed(row, clients["android"])
assert allowed(row, clients["ios"])
assert not allowed(row, clients["windows"])

print("platform filter semantics tests passed")
