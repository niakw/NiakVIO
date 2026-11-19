#!/usr/bin/env python3
"""Inject official TV BuildConfig TMDB capability into an isolated native Lab build.

NuvioTV's PluginRuntime supplies BuildConfig.TMDB_API_KEY to its QuickJS global,
but NuvioTV Gradle reads that value *only* from local.properties. A CI checkout
with an empty local.properties file produces false zero-stream results for
title-first providers. Never log, persist to the repo or echo the key.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

REQUIRES = re.compile(r'["\']requiresTmdbBeforeRun["\']\s*:\s*true\b')
KEY_NAME = "TMDB_API_KEY"


def source_requires_tmdb(root: Path, manifest: str, provider: str) -> bool:
    if not provider or provider == "declared-type":
        return False
    if manifest not in ("manifest.json", "vf/manifest.json"):
        raise ValueError("only canonical native manifests can be executed")
    manifest_file = (root / manifest).resolve()
    doc = json.loads(manifest_file.read_text("utf-8"))
    matching = [
        x for x in doc.get("scrapers") or []
        if isinstance(x, dict)
        and str(x.get("id") or "").strip().casefold() == provider.casefold()
        and x.get("enabled") is True
    ]
    if len(matching) != 1:
        raise ValueError("target provider is not uniquely active in canonical manifest")
    code_file = (manifest_file.parent / str(matching[0].get("filename") or "")).resolve()
    try:
        relative = code_file.relative_to(root.resolve()).parts
    except ValueError:
        raise ValueError("provider path escapes repository") from None
    if len(relative) < 2 or relative[0] != "providers" or not code_file.is_file():
        raise ValueError("invalid canonical active provider source")
    return bool(REQUIRES.search(code_file.read_text("utf-8")))


def inject(root: Path, client_root: Path, manifest: str, provider: str,
           key: str) -> str:
    required = source_requires_tmdb(root, manifest, provider)
    # TMDB API v3 keys are hexadecimal; refuse unexpected content, including
    # newlines/property escapes, rather than writing arbitrary Gradle properties.
    usable = bool(re.fullmatch(r"[A-Fa-f0-9]{32}", key or ""))
    if key and not usable:
        raise ValueError("TMDB_API_KEY has invalid v3 key shape")
    local = client_root / "local.properties"
    if not client_root.is_dir() or not local.is_file():
        raise ValueError("official NuvioTV local.properties not initialized")
    if required and not usable:
        raise ValueError("TMDB_REQUIRED_BUT_UNAVAILABLE: native TV proof is environment-blocked, not a provider failure")
    if usable:
        lines = [s for s in local.read_text("utf-8").splitlines()
                 if not re.match(r"\s*TMDB_API_KEY\s*=", s)]
        lines.append(f"{KEY_NAME}={key}")
        local.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.chmod(local, 0o600)
    return "configured" if usable else "not_required_and_unconfigured"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--client-root", type=Path, required=True)
    p.add_argument("--manifest", choices=("manifest.json", "vf/manifest.json"), required=True)
    p.add_argument("--provider", required=True)
    a = p.parse_args()
    try:
        state = inject(a.repo_root, a.client_root, a.manifest,
                       a.provider, os.environ.get(KEY_NAME, ""))
    except ValueError as error:
        # Only constant, non-sensitive diagnostic codes; no raw key included.
        if str(error).startswith("TMDB_REQUIRED_BUT_UNAVAILABLE"):
            print("FIELD_NATIVE_TV_TMDB_CAPABILITY state=environment_blocked required=true secret_logged=false")
        else:
            print("FIELD_NATIVE_TV_TMDB_CAPABILITY state=setup_error secret_logged=false")
        return 2
    print("FIELD_NATIVE_TV_TMDB_CAPABILITY "
          f"state={state} secret_logged=false manifest={a.manifest} "
          f"targeted={str(a.provider != 'declared-type').lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
