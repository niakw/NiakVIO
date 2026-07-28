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
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"


def load_overrides() -> dict[str, Any]:
    if not CONFIG.exists():
        return {}
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must be an object")
    return value


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


def apply_overrides(
    provider_id: str,
    data: bytes,
    *,
    phase: str = "discovery",
    profile_names: Iterable[str] | None = None,
) -> tuple[bytes, list[dict[str, Any]]]:
    """Apply stable replacements and profiles allowed for the selected phase.

    ``profile_names`` is used by the runtime repair engine to request an exact
    provider-agnostic strategy after its failure signature has matched. Passing
    explicit names never bypasses structural capability detection.
    """
    config = load_overrides()
    text = data.decode("utf-8")
    applied: list[dict[str, Any]] = []
    provider_id = provider_id.casefold()
    specific = (config.get("provider_patches") or {}).get(provider_id, {})
    if not isinstance(specific, dict):
        raise ValueError(f"provider_patches.{provider_id} must be an object")

    replacements = dict(config.get("domain_replacements") or {})
    replacements.update(specific.get("replacements") or {})
    replacements.update(specific.get("route_replacements") or {})
    for old, new in replacements.items():
        old_text, new_text = str(old), str(new)
        count = text.count(old_text)
        if count:
            text = text.replace(old_text, new_text)
            applied.append(
                {
                    "type": "replace",
                    "from": old_text,
                    "to": new_text,
                    "count": count,
                    "phase": phase,
                }
            )

    profiles = config.get("patch_profiles") or {}
    if not isinstance(profiles, dict):
        raise ValueError("patch_profiles must be an object")

    explicitly_requested = _normalize_profile_names(profile_names)
    explicitly_requested.update(str(value) for value in (specific.get("profiles") or []))
    unknown = explicitly_requested - set(profiles)
    if unknown:
        raise ValueError("unknown patch profile(s): " + ", ".join(sorted(unknown)))

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            continue
        profile_phase = str(profile.get("phase") or "discovery")
        requested = profile_name in explicitly_requested
        automatic = bool(profile.get("auto_apply")) and profile_phase == phase
        if not (requested or automatic):
            continue
        if not profile_matches(text, profile):
            if requested:
                # A requested runtime strategy that does not match the bundle is
                # a normal non-applicable repair, not a build-wide exception.
                continue
            continue
        patch_script = profile.get("patch_script")
        if not patch_script:
            raise ValueError(f"patch profile {profile_name} has no patch_script")
        options = dict(profile.get("options") or {})
        options.setdefault("detect_all", profile.get("detect_all") or [])
        options.setdefault("detect_any", profile.get("detect_any") or [])
        before = text
        text = _apply_patch_script(
            text,
            provider_id,
            str(patch_script),
            options,
            str(profile_name),
        )
        if text != before:
            applied.append(
                {
                    "type": "patch_profile",
                    "profile": str(profile_name),
                    "path": str(patch_script),
                    "phase": profile_phase,
                }
            )

    # Legacy per-provider hooks remain supported only for existing repositories.
    # New structural repairs belong in reusable patch_profiles.
    patch_script = specific.get("patch_script")
    if patch_script and phase == "discovery":
        before = text
        text = _apply_patch_script(
            text,
            provider_id,
            str(patch_script),
            dict(specific.get("patch_options") or {}),
            None,
        )
        if text != before:
            applied.append(
                {"type": "patch_script", "path": str(patch_script), "phase": phase}
            )
    return text.encode("utf-8"), applied


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
