#!/usr/bin/env python3
"""Apply sanitized Brain-LLM provider mutations to the current Force sandbox only.

This script has no publication authority. Canonical Repair must rematerialize,
probe, verify identity/playback and pass non-regression gates before any Force
candidate can be committed by the workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from import_external_brain_llm_guidance import canon, source_drift  # noqa: E402

SHA40 = re.compile(r"^[0-9a-f]{40}$")
FP64 = re.compile(r"^[0-9a-f]{64}$")
PART = re.compile(r"^[A-Za-z0-9_-]+$")
ALLOWED_DATA_ROOTS = {
    "capability",
    "official_hub",
    "official_site",
    "manifest_overrides",
    "domain_substitutions",
    "published_types",
    "identity_input",
    "learned_routes",
    "candidate_learned_routes",
    "candidate_api_recipe",
    "api_recipe",
    "route_data_state",
    "runtime_domain_replacements",
    "preserve_embed_urls",
    "notes",
}
URL_PATHS = {
    "official_hub",
    "official_site",
    "candidate_api_recipe.base",
    "api_recipe.base",
}
PLACEHOLDER_MARKERS = (
    "api.example",
    "example.com",
    ".example/",
    "changeme",
    "replace_me",
    "placeholder",
    "diff_to_",
    "<current",
    "<replace",
    "todo:",
)


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()


def _provider_patches(overrides: dict[str, Any]) -> dict[str, Any]:
    patches = overrides.get("provider_patches")
    if not isinstance(patches, dict):
        raise ValueError("provider-overrides.json provider_patches is missing")
    return patches


def _provider_entry(patches: dict[str, Any], provider: str) -> tuple[str, dict[str, Any]]:
    wanted = canon(provider)
    for key, value in patches.items():
        if canon(key) == wanted and isinstance(value, dict):
            return str(key), value
    raise ValueError(f"provider override missing for {provider}")


def _mutation_context_fingerprint(
    provider: str,
    entry: dict[str, Any],
    mutations: list[dict[str, Any]],
) -> str:
    surfaces: list[dict[str, Any]] = []
    override_needed = False
    for mutation in mutations:
        scope = str(mutation.get("scope") or "")
        path = str(mutation.get("path") or "")
        if scope == "provider_data":
            override_needed = True
            continue
        if scope in {"provider_patch", "provider_js"}:
            target = ROOT / path
            if not target.is_file():
                raise ValueError(f"{provider}: mutation context path missing: {path}")
            surfaces.append({
                "scope": scope,
                "path": path,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            })
    if override_needed:
        surfaces.append({
            "scope": "provider_data",
            "path": "provider-overrides.json:provider_patches",
            "value": entry,
        })
    return _fingerprint(surfaces)


def _registered_patch_scripts(entry: dict[str, Any]) -> set[str]:
    # Compatibility field name is retained in the repository schema. User-facing
    # terminology is Bloc.
    return {
        str(value).strip()
        for value in (entry.get("provider_lego_scripts") or [])
        if str(value).strip().startswith("scripts/provider_patches/")
    }


def _path_parts(path: str) -> list[str]:
    if not path or len(path) > 240 or "/" in path or "\\" in path or ".." in path:
        return []
    parts = [part for part in path.replace("[", ".").replace("]", "").split(".") if part]
    if not parts or parts[0] not in ALLOWED_DATA_ROOTS:
        return []
    forbidden = {"__proto__", "prototype", "constructor"}
    if any(part.casefold() in forbidden or not PART.fullmatch(part) for part in parts):
        return []
    return parts


def _reject_placeholders(value: Any) -> None:
    if isinstance(value, str):
        lowered = value.casefold()
        if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
            raise ValueError("mutation contains placeholder or synthetic value")
    elif isinstance(value, dict):
        for item in value.values():
            _reject_placeholders(item)
    elif isinstance(value, list):
        for item in value:
            _reject_placeholders(item)


def _validate_url(value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError("URL mutation must be a string")
    parsed = urlparse(value)
    host = (parsed.hostname or "").casefold()
    if parsed.scheme not in {"http", "https"} or not host or "." not in host:
        raise ValueError("URL mutation must be a concrete http(s) URL")
    if host in {"localhost", "example.com"} or host.endswith(".example"):
        raise ValueError("placeholder URL host is forbidden")


def _resolve_parent(entry: dict[str, Any], parts: list[str], *, create: bool) -> tuple[dict[str, Any], str]:
    current: dict[str, Any] = entry
    for part in parts[:-1]:
        value = current.get(part)
        if value is None and create:
            value = {}
            current[part] = value
        if not isinstance(value, dict):
            raise ValueError("provider_data path crosses a non-object value")
        current = value
    return current, parts[-1]


def _apply_data(entry: dict[str, Any], mutation: dict[str, Any]) -> None:
    operation = str(mutation.get("operation") or "")
    path = str(mutation.get("path") or "")
    parts = _path_parts(path)
    if not parts:
        raise ValueError(f"unsafe provider_data path: {path}")
    if operation not in {"set", "delete", "append"}:
        raise ValueError(f"unsupported provider_data operation: {operation}")

    value = mutation.get("value")
    if operation in {"set", "append"}:
        if "value" not in mutation:
            raise ValueError("provider_data set/append requires value")
        _reject_placeholders(value)
        if path in URL_PATHS:
            _validate_url(value)

    parent, leaf = _resolve_parent(entry, parts, create=operation in {"set", "append"})
    if operation == "set":
        parent[leaf] = value
    elif operation == "delete":
        parent.pop(leaf, None)
    else:
        target = parent.get(leaf)
        if target is None:
            target = []
            parent[leaf] = target
        if not isinstance(target, list):
            raise ValueError("provider_data append target is not a list")
        if value not in target:
            target.append(value)


def _validate_diff_path(diff: str, expected_path: str) -> None:
    if not diff or len(diff) > 24000:
        raise ValueError("missing or oversized unified diff")
    _reject_placeholders(diff)
    headers: list[str] = []
    for line in diff.splitlines():
        if line.startswith("--- ") or line.startswith("+++ "):
            token = line[4:].split("\t", 1)[0].strip()
            if token == "/dev/null":
                raise ValueError("Force mutation may not create/delete provider files")
            if token.startswith("a/") or token.startswith("b/"):
                token = token[2:]
            headers.append(token)
    if len(headers) < 2 or any(value != expected_path for value in headers):
        raise ValueError("unified diff targets a path outside the selected provider")
    if "@@" not in diff:
        raise ValueError("unified diff has no hunk")


def _git_apply(diff: str, path: str) -> None:
    for args in (
        ["git", "apply", "--check", "--whitespace=error-all", "-"],
        ["git", "apply", "--whitespace=error-all", "-"],
    ):
        proc = subprocess.run(
            args,
            cwd=ROOT,
            input=diff,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise ValueError(
                f"cannot apply provider Bloc diff to {path}: "
                + (proc.stderr or proc.stdout)[-1200:]
            )


def _apply_file_mutation(
    provider: str,
    entry: dict[str, Any],
    mutation: dict[str, Any],
) -> str:
    scope = str(mutation.get("scope") or "")
    operation = str(mutation.get("operation") or "")
    path = str(mutation.get("path") or "")
    diff = str(mutation.get("diff") or "")
    if operation != "unified_diff":
        raise ValueError(f"unsupported {scope} operation: {operation}")

    if scope == "provider_patch":
        allowed = _registered_patch_scripts(entry)
        if path not in allowed or not path.startswith("scripts/provider_patches/"):
            raise ValueError(f"{provider}: provider_patch is not a registered Bloc: {path}")
    elif scope == "provider_js":
        expected = f"engine_v2/providers/{provider}.mjs"
        if path != expected or not (ROOT / path).is_file():
            raise ValueError(f"{provider}: provider_js target is not the authored module")
    else:
        raise ValueError(f"unsupported file mutation scope: {scope}")

    if not (ROOT / path).is_file():
        raise ValueError(f"provider mutation path does not exist: {path}")
    _validate_diff_path(diff, path)
    _git_apply(diff, path)
    return path


def _selected_queue(
    census: dict[str, Any],
    providers: list[str],
) -> set[str]:
    queue = {canon(value) for value in census.get("repairQueue") or [] if canon(value)}
    if providers:
        requested = {canon(value) for value in providers if canon(value)}
        queue &= requested
    return queue


def apply_payload(
    payload: dict[str, Any],
    *,
    current_sha: str,
    selected: set[str],
) -> dict[str, Any]:
    if int(payload.get("schemaVersion") or 0) != 1:
        raise ValueError("unsupported Force mutation schema")
    if payload.get("sandboxMutationAuthority") is not True:
        raise ValueError("Force mutation artifact lacks sandbox authority")
    for key in ("publicationAuthority", "proofAuthority", "privateContentRetained"):
        if payload.get(key) is not False:
            raise ValueError(f"unsafe Force mutation authority flag: {key}")

    source_sha = str(payload.get("sourceNiakvioSha") or "").strip().casefold()
    brain_sha = str(payload.get("brainLlmSha") or "").strip().casefold()
    current_sha = str(current_sha or "").strip().casefold()
    for label, sha in (("source", source_sha), ("brain", brain_sha), ("current", current_sha)):
        if not SHA40.fullmatch(sha):
            raise ValueError(f"invalid {label} SHA")

    neutral_paths, drifted = source_drift(ROOT, source_sha, current_sha)
    overrides_path = ROOT / "provider-overrides.json"
    overrides = _load(overrides_path)
    if not isinstance(overrides, dict):
        raise ValueError("provider-overrides.json is invalid")
    patches = _provider_patches(overrides)

    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    changed_files: set[str] = set()
    overrides_changed = False

    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Force mutation rows missing")

    seen_force_providers: set[str] = set()
    for raw in rows[:128]:
        if not isinstance(raw, dict):
            raise ValueError("invalid Force mutation row")
        provider = canon(raw.get("providerId"))
        if provider in seen_force_providers:
            raise ValueError(
                f"{provider}: multiple concrete Force candidates cannot share one mutable sandbox"
            )
        if provider:
            seen_force_providers.add(provider)
        if provider not in selected:
            skipped.append({"provider": provider or "<missing>", "reason": "outside-current-repair-scope"})
            continue
        if provider in drifted:
            skipped.append({"provider": provider, "reason": "provider-drift-since-guidance"})
            continue

        mutations = raw.get("mutations")
        if not isinstance(mutations, list) or not mutations:
            skipped.append({"provider": provider, "reason": "empty-mutations"})
            continue
        expected_fp = str(raw.get("mutationFingerprint") or "").strip().casefold()
        if not FP64.fullmatch(expected_fp) or _fingerprint(mutations) != expected_fp:
            raise ValueError(f"{provider}: Force mutation fingerprint mismatch")

        key, entry = _provider_entry(patches, provider)
        expected_context_fp = str(raw.get("mutationContextFingerprint") or "").strip().casefold()
        actual_context_fp = _mutation_context_fingerprint(provider, entry, mutations)
        if (
            not FP64.fullmatch(expected_context_fp)
            or actual_context_fp != expected_context_fp
        ):
            raise ValueError(f"{provider}: Force mutation context fingerprint mismatch")

        before_entry = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        row_changed_files: set[str] = set()
        for mutation in mutations[:8]:
            if not isinstance(mutation, dict):
                raise ValueError(f"{provider}: invalid mutation")
            scope = str(mutation.get("scope") or "")
            if scope == "provider_data":
                _apply_data(entry, mutation)
            elif scope in {"provider_patch", "provider_js"}:
                row_changed_files.add(_apply_file_mutation(provider, entry, mutation))
            else:
                raise ValueError(f"{provider}: unsupported mutation scope: {scope}")

        if json.dumps(entry, sort_keys=True, separators=(",", ":")) != before_entry:
            patches[key] = entry
            overrides_changed = True
            row_changed_files.add("provider-overrides.json")
        changed_files.update(row_changed_files)
        applied.append(
            {
                "provider": provider,
                "mutationFingerprint": expected_fp,
                "mutationContextFingerprint": expected_context_fp,
                "mutationCount": len(mutations),
                "changedFiles": sorted(row_changed_files),
            }
        )

    if overrides_changed:
        overrides_path.write_text(
            json.dumps(overrides, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {
        "schemaVersion": 1,
        "sourceNiakvioSha": source_sha,
        "currentSha": current_sha,
        "sourceBrainLlmSha": brain_sha,
        "neutralDriftPaths": neutral_paths,
        "driftedProviders": sorted(drifted),
        "selectedProviders": sorted(selected),
        "appliedProviderCount": len(applied),
        "appliedProviders": [row["provider"] for row in applied],
        "applied": applied,
        "skipped": skipped,
        "changedFiles": sorted(changed_files),
        "publicationAuthority": False,
        "proofAuthority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument(
        "--census",
        type=Path,
        default=ROOT / "automation/provider-census-status.json",
    )
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    census = _load(args.census)
    if not isinstance(census, dict):
        raise SystemExit("current census is invalid")
    selected = _selected_queue(census, args.provider)
    payload = _load(args.input)
    if not isinstance(payload, dict):
        raise SystemExit("Force mutation payload is invalid")

    report = apply_payload(
        payload,
        current_sha=args.current_sha,
        selected=selected,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "FIELD_BRAIN_LLM_FORCE_MUTATIONS "
        f"selected={len(selected)} applied={report['appliedProviderCount']} "
        f"skipped={len(report['skipped'])} changed_files={len(report['changedFiles'])} "
        "publication=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
