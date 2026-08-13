#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply durable provider overrides and reusable structural patch profiles.

Stable literal/domain replacements are applied during discovery and promotion.
Structural profiles can declare ``phase: runtime``; those profiles are only
applied by the deep-repair loop after a matching runtime failure signature has
been observed. This keeps the build provider-agnostic while preventing blind
rewrites of every downloaded bundle.
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
from pathlib import Path
from typing import Any, Iterable
from override_text_utils import replace_literal

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"


def load_overrides() -> dict[str, Any]:
    """Load overrides through the provider-isolation boundary.

    The JSON file is historical state and may still contain obsolete hooks.
    Consumers must never receive a provider-specific hook that depends on an
    official API owned by another provider. Sanitization is deliberately done
    at read time as well as by rebuild/reapply so stale configuration cannot
    reintroduce a cross-provider dependency.
    """
    if not CONFIG.exists():
        return {}
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    from provider_engine_normalizer import sanitize_provider_hooks
    sanitized, _removed = sanitize_provider_hooks(value, ROOT)
    return sanitized


def _load_patch_module(patch_script: str, provider_id: str):
    patch_path = (ROOT / str(patch_script)).resolve()
    if ROOT not in patch_path.parents or not patch_path.is_file():
        raise ValueError(f"invalid provider patch script: {patch_script}")
    module_name = (
        f"nuvio_provider_patch_{provider_id}_"
        f"{hashlib.sha256(str(patch_path).encode()).hexdigest()[:8]}"
    )
    spec = importlib.util.spec_from_file_location(module_name, patch_path)
    if not spec or not spec.loader:
        raise ValueError(f"cannot load provider patch script: {patch_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def profile_matches(text: str, profile: dict[str, Any]) -> bool:
    """Return whether a profile's structural capability markers match a bundle."""
    all_markers = [str(v) for v in profile.get("detect_all") or []]
    any_markers = [str(v) for v in profile.get("detect_any") or []]
    none_markers = [str(v) for v in profile.get("detect_none") or []]
    if all_markers and not all(marker in text for marker in all_markers):
        return False
    if any_markers and not any(marker in text for marker in any_markers):
        return False
    if none_markers and any(marker in text for marker in none_markers):
        return False
    return bool(all_markers or any_markers or profile.get("auto_apply"))


def _apply_patch_script(
    text: str,
    provider_id: str,
    patch_script: str,
    options: dict[str, Any],
    profile_name: str | None,
) -> str:
    module = _load_patch_module(patch_script, provider_id)
    apply_fn = getattr(module, "apply", None)
    if not callable(apply_fn):
        raise ValueError(f"provider patch {patch_script} has no callable apply()")
    kwargs = {
        "options": options,
        "context": {"provider_id": provider_id, "profile": profile_name},
    }
    signature = inspect.signature(apply_fn)
    if "options" in signature.parameters or any(
        parameter.kind == parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    ):
        result = apply_fn(text, **kwargs)
    else:
        result = apply_fn(text)
    if not isinstance(result, str):
        raise TypeError(f"provider patch {patch_script} must return str")
    return result


def _normalize_profile_names(values: Iterable[str] | None) -> set[str]:
    return {str(value) for value in (values or []) if str(value).strip()}



def _replace_named_function(text: str, function_name: str, replacement: str) -> tuple[str, bool]:
    """Replace a classic named JavaScript function using balanced braces."""
    import re

    match = re.search(rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return text, False
    start = match.start()
    brace_start = text.find("{", match.start())
    depth = 0
    quote = None
    escape = False
    i = brace_start
    while i < len(text):
        char = text[i]
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            i += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            i += 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[:start] + replacement + text[i + 1 :], True
        i += 1
    raise ValueError(f"unterminated function while replacing {function_name}")


def _apply_named_function_replacements(
    text: str,
    provider_id: str,
    function_replacements: dict[str, Any],
    phase: str,
) -> tuple[str, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    for function_name, replacement in function_replacements.items():
        if not isinstance(replacement, str) or not replacement.strip():
            continue
        updated, changed = _replace_named_function(text, str(function_name), replacement)
        if not changed:
            continue
        text = updated
        records.append(
            {
                "type": "function_replace",
                "function": str(function_name),
                "phase": phase,
            }
        )
    return text, records


def _configured_profiles(config: dict[str, Any], provider_id: str) -> list[dict[str, Any]]:
    provider_key = str(provider_id).casefold()
    patches = config.get("provider_patches", {}) if isinstance(config, dict) else {}
    provider_patch = patches.get(provider_key, {}) if isinstance(patches, dict) else {}
    explicit_names = _normalize_profile_names(
        provider_patch.get("profiles") if isinstance(provider_patch, dict) else None
    )
    definitions = config.get("patch_profiles", {}) if isinstance(config, dict) else {}
    profiles: list[dict[str, Any]] = []
    if not isinstance(definitions, dict):
        return profiles
    for name, profile in definitions.items():
        if not isinstance(profile, dict):
            continue
        if explicit_names and name not in explicit_names:
            continue
        if not explicit_names and not profile.get("auto_apply"):
            continue
        row = dict(profile)
        row["name"] = str(name)
        profiles.append(row)
    return profiles


def apply_overrides(
    provider_id: str,
    data: bytes,
    *,
    phase: str = "discovery",
    only_profiles: Iterable[str] | None = None,
    only_profile: str | None = None,
    runtime_context: dict[str, Any] | None = None,
) -> tuple[bytes, list[dict[str, Any]]]:
    """Apply durable overrides and matching profiles for a provider."""
    config = load_overrides()
    provider_key = str(provider_id).casefold()
    provider_patch = (config.get("provider_patches") or {}).get(provider_key, {})
    if not isinstance(provider_patch, dict):
        provider_patch = {}

    text = data.decode("utf-8", errors="strict")
    records: list[dict[str, Any]] = []

    replacements = provider_patch.get("replacements") or {}
    if phase == "discovery" and isinstance(replacements, dict):
        for old, new in replacements.items():
            if not isinstance(old, str) or not isinstance(new, str):
                continue
            updated = replace_literal(text, old, new)
            if updated == text:
                continue
            text = updated
            records.append({"type": "replace", "from": old, "to": new, "phase": phase})

    function_replacements = provider_patch.get("function_replacements") or {}
    if phase == "discovery" and isinstance(function_replacements, dict):
        text, function_records = _apply_named_function_replacements(
            text,
            provider_key,
            function_replacements,
            phase,
        )
        records.extend(function_records)

    scripts = [
        str(value)
        for value in provider_patch.get("patch_scripts") or []
        if str(value).strip()
    ]
    legacy_script = str(provider_patch.get("patch_script") or "").strip()
    if legacy_script and legacy_script not in scripts:
        scripts.append(legacy_script)
    script_options = provider_patch.get("patch_script_options") or {}
    if not isinstance(script_options, dict):
        script_options = {}
    legacy_options = provider_patch.get("patch_options") or {}
    if not isinstance(legacy_options, dict):
        legacy_options = {}

    if phase == "discovery":
        for script in scripts:
            options = script_options.get(script, legacy_options if script == legacy_script else {})
            if not isinstance(options, dict):
                options = {}
            updated = _apply_patch_script(text, provider_key, script, options, None)
            if updated == text:
                continue
            text = updated
            records.append(
                {
                    "type": "patch_script",
                    "path": script,
                    "phase": phase,
                }
            )

    selected_profiles = set(_normalize_profile_names(only_profiles))
    if only_profile:
        selected_profiles.add(str(only_profile))
    profiles = _configured_profiles(config, provider_key)
    for profile in profiles:
        profile_name = str(profile.get("name") or "")
        profile_phase = str(profile.get("phase") or "discovery")
        if profile_phase != phase:
            continue
        if selected_profiles and profile_name not in selected_profiles:
            continue
        if not selected_profiles and phase == "runtime":
            continue
        if not profile_matches(text, profile):
            continue
        script = str(profile.get("patch_script") or "").strip()
        if not script:
            continue
        options = dict(profile.get("options") or {})
        if runtime_context:
            options["runtime_context"] = runtime_context
        updated = _apply_patch_script(text, provider_key, script, options, profile_name)
        if updated == text:
            continue
        text = updated
        records.append(
            {
                "type": "patch_profile",
                "profile": profile_name,
                "phase": phase,
                "options": options,
            }
        )

    return text.encode("utf-8"), records
