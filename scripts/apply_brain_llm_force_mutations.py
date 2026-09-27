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
    "/* clipped */",
)
BLOC_FAMILY = re.compile(r"^[a-z][a-z0-9_]{2,48}$")
DANGEROUS_RUNTIME_TOKEN = re.compile(
    r"(?i)(?:\beval\s*\(|\bFunction\s*\(|\bprocess\.|\brequire\s*\(|"
    r"\bchild_process\b|\bDeno\.|\bBun\.|\bimport\s*\()"
)
MANAGED_MARKERS = ("/* STARTFIX:", "/* CLOSEFIX:", "/* FIXDATA:")


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


def _provider_owned_source(text: str) -> str:
    begin_marker = "/* BEGIN NIAKVIO_PROVIDER */"
    end_marker = "/* END NIAKVIO_PROVIDER */"
    if text.count(begin_marker) != 1 or text.count(end_marker) != 1:
        return text
    begin = text.index(begin_marker)
    end = text.index(end_marker, begin)
    first_core = text.find("/* STARTFIX:CORE.", begin, end)
    limit = first_core if first_core >= 0 else end
    return text[begin:limit]


def _provider_runtime_surface(provider: str) -> tuple[str, Path, str]:
    manifest = _load(ROOT / "manifest.json")
    rows = manifest.get("scrapers") if isinstance(manifest, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"{provider}: current manifest scrapers unavailable")
    wanted = canon(provider)
    row = next(
        (
            value
            for value in rows
            if isinstance(value, dict) and canon(value.get("id")) == wanted
        ),
        None,
    )
    filename = str((row or {}).get("filename") or "").strip()
    if not filename.startswith(("providers/", "provider-disabled/")):
        raise ValueError(f"{provider}: current runtime filename unavailable")
    path = ROOT / filename
    if not path.is_file():
        raise ValueError(f"{provider}: current runtime bytes unavailable: {filename}")
    return filename, path, path.read_text(encoding="utf-8", errors="replace")


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
        if scope == "provider_bloc":
            override_needed = True
            filename, target, _source = _provider_runtime_surface(provider)
            surfaces.append({
                "scope": "provider_bloc",
                "path": filename,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            })
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
        for value in [
            *(entry.get("patch_scripts") or []),
            *(entry.get("provider_lego_scripts") or []),
        ]
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


def _canonical_git_diff(diff: str, path: str) -> str:
    """Normalize validated patch headers to standard git a/ and b/ paths."""
    lines = diff.splitlines()
    output: list[str] = []
    for line in lines:
        if line.startswith("--- "):
            suffix = "\t" + line.split("\t", 1)[1] if "\t" in line else ""
            output.append(f"--- a/{path}{suffix}")
        elif line.startswith("+++ "):
            suffix = "\t" + line.split("\t", 1)[1] if "\t" in line else ""
            output.append(f"+++ b/{path}{suffix}")
        else:
            output.append(line)
    return "\n".join(output) + ("\n" if diff.endswith("\n") else "")


def _git_apply(diff: str, path: str) -> None:
    normalized = _canonical_git_diff(diff, path)
    for args in (
        ["git", "apply", "--check", "--whitespace=error-all", "-"],
        ["git", "apply", "--whitespace=error-all", "-"],
    ):
        proc = subprocess.run(
            args,
            cwd=ROOT,
            input=normalized,
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


def _validate_generated_bloc_mutation(
    provider: str,
    mutation: dict[str, Any],
) -> tuple[str, str, str, str]:
    if str(mutation.get("operation") or "") != "upsert":
        raise ValueError(f"{provider}: unsupported provider_bloc operation")
    family = str(mutation.get("family") or "").strip().casefold()
    find = str(mutation.get("find") or "")
    replace = str(mutation.get("replace") or "")
    if not BLOC_FAMILY.fullmatch(family):
        raise ValueError(f"{provider}: invalid provider_bloc family")
    if not find or len(find) > 320 or not replace or len(replace) > 1200:
        raise ValueError(f"{provider}: provider_bloc find/replace is missing or oversized")
    if find == replace:
        raise ValueError(f"{provider}: provider_bloc mutation is a no-op")
    _reject_placeholders(find)
    _reject_placeholders(replace)
    if any(marker in find or marker in replace for marker in MANAGED_MARKERS):
        raise ValueError(f"{provider}: provider_bloc may not target managed ownership metadata")
    before_caps = set(DANGEROUS_RUNTIME_TOKEN.findall(find))
    after_caps = set(DANGEROUS_RUNTIME_TOKEN.findall(replace))
    if after_caps - before_caps:
        raise ValueError(f"{provider}: provider_bloc replacement introduces a forbidden runtime capability")

    _filename, _path, runtime_source = _provider_runtime_surface(provider)
    owned = _provider_owned_source(runtime_source)
    if owned.count(find) != 1:
        raise ValueError(
            f"{provider}: provider_bloc find must occur exactly once in current provider-owned runtime bytes"
        )
    spec_fingerprint = _fingerprint({
        "schemaVersion": 1,
        "family": family,
        "find": find,
        "replace": replace,
    })
    return family, find, replace, spec_fingerprint


def _render_generated_bloc_module(
    family: str,
    find: str,
    replace: str,
    spec_fingerprint: str,
) -> str:
    managed_fix_id = f"PROVIDER.BRAIN.RUNTIME.{family.upper()}"
    return f'''#!/usr/bin/env python3
"""Generated by NiakVIO from a bounded Brain runtime Bloc spec.

The model does not author this Python. Only FAMILY/FIND/REPLACE below come from
an already-validated provider-local mutation contract.
"""
from provider_patch_blocks import (
    decode_managed_data,
    has_managed_fix,
    owned_span,
    render_managed_fix,
    replace_managed_fix_in_place,
)

MANAGED_FIX_ID = {json.dumps(managed_fix_id, ensure_ascii=True)}
FAMILY = {json.dumps(family, ensure_ascii=True)}
SPEC_FINGERPRINT = {json.dumps(spec_fingerprint, ensure_ascii=True)}
FIND = {json.dumps(find, ensure_ascii=True)}
REPLACE = {json.dumps(replace, ensure_ascii=True)}
_PROVIDER_BEGIN = "/* BEGIN NIAKVIO_PROVIDER */"
_PROVIDER_END = "/* END NIAKVIO_PROVIDER */"


def _provider_range(text):
    if text.count(_PROVIDER_BEGIN) == 1 and text.count(_PROVIDER_END) == 1:
        begin = text.index(_PROVIDER_BEGIN)
        end = text.index(_PROVIDER_END, begin)
        first_core = text.find("/* STARTFIX:CORE.", begin, end)
        return begin, first_core if first_core >= 0 else end
    return 0, len(text)


def _owned_body(text):
    span = owned_span(text, MANAGED_FIX_ID)
    if span is None:
        raise ValueError("generated Bloc ownership block is missing")
    block = text[span[0]:span[1]]
    fixdata = block.find("/* FIXDATA:")
    fixdata_end = block.find("*/", fixdata + 3) if fixdata >= 0 else -1
    close = block.rfind("/* CLOSEFIX:")
    if fixdata < 0 or fixdata_end < 0 or close <= fixdata_end:
        raise ValueError("generated Bloc ownership block is malformed")
    return block[fixdata_end + 2:close].strip()


def managed_fix_insertion_baseline(text):
    if has_managed_fix(text, MANAGED_FIX_ID):
        return text
    begin, end = _provider_range(text)
    owned = text[begin:end]
    if owned.count(FIND) != 1:
        raise ValueError("generated Bloc anchor is not unique in provider-owned bytes")
    local = owned.index(FIND)
    start = begin + local
    return text[:start] + text[start + len(FIND):]


def apply(text, **_kwargs):
    if has_managed_fix(text, MANAGED_FIX_ID):
        data = decode_managed_data(text, MANAGED_FIX_ID) or {{}}
        if str(data.get("spec_fingerprint") or "") == SPEC_FINGERPRINT:
            return text
        body = _owned_body(text)
        if body.count(FIND) != 1:
            raise ValueError("generated Bloc evolution anchor is not unique in current owned body")
        updated_body = body.replace(FIND, REPLACE, 1)
        updated_data = dict(data)
        updated_data.update({{
            "schema_version": 1,
            "family": FAMILY,
            "spec_fingerprint": SPEC_FINGERPRINT,
        }})
        output, changed = replace_managed_fix_in_place(
            text,
            MANAGED_FIX_ID,
            updated_body,
            data=updated_data,
        )
        if not changed:
            raise ValueError("generated Bloc evolution lost ownership")
        return output

    begin, end = _provider_range(text)
    owned = text[begin:end]
    if owned.count(FIND) != 1:
        raise ValueError("generated Bloc anchor is not unique in provider-owned bytes")
    local = owned.index(FIND)
    start = begin + local
    data = {{
        "schema_version": 1,
        "family": FAMILY,
        "spec_fingerprint": SPEC_FINGERPRINT,
        "restore_source": FIND,
    }}
    block = render_managed_fix(MANAGED_FIX_ID, REPLACE, data=data)
    clean_v3 = (
        "NIAKVIO_PROVIDER_BASE_OWNED_V3" in text
        and text.count(_PROVIDER_BEGIN) == 1
        and text.count(_PROVIDER_END) == 1
    )
    if clean_v3:
        block += "\n"
    return text[:start] + block + text[start + len(FIND):]
'''


def _generated_bloc_path(family: str, spec_fingerprint: str) -> str:
    return (
        "scripts/provider_patches/"
        f"brain_runtime_{family}_{spec_fingerprint[:12]}_v1.py"
    )


def _register_generated_bloc(
    entry: dict[str, Any],
    *,
    family: str,
    path: str,
    spec_fingerprint: str,
) -> None:
    scripts = [
        str(value).strip()
        for value in [
            *(entry.get("patch_scripts") or []),
            *(entry.get("provider_lego_scripts") or []),
        ]
        if str(value).strip().startswith("scripts/provider_patches/")
    ]
    scripts = list(dict.fromkeys(scripts))

    raw_options = entry.get("patch_script_options")
    if raw_options is None:
        options: dict[str, Any] = {}
    elif isinstance(raw_options, dict):
        options = dict(raw_options)
    else:
        raise ValueError("patch_script_options must be an object")

    legacy_options = entry.get("provider_lego_options")
    if isinstance(legacy_options, dict):
        for script, value in legacy_options.items():
            if str(script).startswith("scripts/provider_patches/") and script not in options:
                options[str(script)] = value

    prefix = f"scripts/provider_patches/brain_runtime_{family}_"
    kept: list[str] = []
    for script in scripts:
        metadata = options.get(script)
        same_family = (
            script.startswith(prefix)
            or (
                isinstance(metadata, dict)
                and metadata.get("brainGenerated") is True
                and str(metadata.get("family") or "").strip().casefold() == family
            )
        )
        if same_family:
            options.pop(script, None)
            continue
        kept.append(script)
    if path not in kept:
        kept.append(path)
    options[path] = {
        "brainGenerated": True,
        "family": family,
        "specFingerprint": spec_fingerprint,
        "schemaVersion": 1,
    }
    entry["patch_scripts"] = kept
    entry["patch_script_options"] = options


def _apply_generated_bloc(
    provider: str,
    entry: dict[str, Any],
    mutation: dict[str, Any],
) -> tuple[str, bool]:
    family, find, replace, spec_fingerprint = _validate_generated_bloc_mutation(
        provider, mutation
    )
    relative = _generated_bloc_path(family, spec_fingerprint)
    content = _render_generated_bloc_module(
        family, find, replace, spec_fingerprint
    )
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    created = False
    if target.exists():
        if target.read_text(encoding="utf-8") != content:
            raise ValueError(f"{provider}: generated Bloc path collision: {relative}")
    else:
        target.write_text(content, encoding="utf-8")
        created = True
    _register_generated_bloc(
        entry,
        family=family,
        path=relative,
        spec_fingerprint=spec_fingerprint,
    )
    return relative, created


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

    # Fail closed before touching provider state when an artifact stacks
    # multiple concrete hypotheses for the same provider. Detecting this only
    # inside the application loop could partially apply the first candidate
    # before the second one is rejected.
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

    for raw in rows[:128]:
        provider = canon(raw.get("providerId"))
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
            elif scope == "provider_bloc":
                generated_path, created = _apply_generated_bloc(provider, entry, mutation)
                if created:
                    row_changed_files.add(generated_path)
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
