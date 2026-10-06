#!/usr/bin/env python3
"""Materialize a bounded Brain architecture proposal during explicit FORCE.

The model may only edit allowlisted Brain/Core/Lab architecture surfaces.
Provider bundles, manifests, ProviderBase and publication files are forbidden.
Every edit is exact find/replace or a new isolated Brain layer/test file.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PREFIXES = (
    "providers/", "provider-disabled/", "provider-bases/", "vf/",
)
FORBIDDEN_EXACT = {"manifest.json", "PROVENANCE.json", "provider-overrides.json"}
CREATE_PREFIXES = ("scripts/brain_layers/", "tests/brain_")
MAX_EDITS = 3
MAX_FIND = 600
MAX_REPLACE = 5000
MAX_CREATE = 12000
MAX_SOURCE_SNIPPET = 4200
MAX_TOTAL_SOURCE_CONTEXT = 10500
MAX_MODEL_TOKENS = 512
MODEL_TIMEOUT_SECONDS = 180
RETRY_MODEL_TOKENS = 640
RETRY_MODEL_TIMEOUT_SECONDS = 240
VALIDATION_RETRY_MODEL_TOKENS = 512
VALIDATION_RETRY_TIMEOUT_SECONDS = 180
VALIDATION_FORMAT_RETRY_MODEL_TOKENS = 768
VALIDATION_FORMAT_RETRY_TIMEOUT_SECONDS = 240
RETRY_SOURCE_CONTEXT = 3600
MINIMAL_SOURCE_CONTEXT = 1800
EDIT_VALIDATION_CORRECTION_ROUNDS = 2
MATERIALIZED_CORRECTION_ROUNDS = 3
MAX_MATERIALIZED_FAILURE_CONTEXT = 3200


class MaterializedValidationError(ValueError):
    def __init__(
        self,
        message: str,
        candidate_sources: dict[str, str],
        baseline_sources: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.candidate_sources = candidate_sources
        self.baseline_sources = baseline_sources or {}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def allowed_patterns(config: dict[str, Any]) -> list[str]:
    force = config.get("forceArchitecture") if isinstance(config.get("forceArchitecture"), dict) else {}
    generated = force.get("generatedEditAllowlist") if isinstance(force.get("generatedEditAllowlist"), list) else []
    values = generated or config.get("structuralProposalSurfaces") or []
    return [str(x) for x in values if str(x)]


def path_allowed(path: str, patterns: list[str]) -> bool:
    if not path or path.startswith("/") or ".." in Path(path).parts:
        return False
    if path in FORBIDDEN_EXACT or any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    for pattern in patterns:
        if pattern.endswith("*") and path.startswith(pattern[:-1]):
            return True
        if path == pattern:
            return True
    return any(path.startswith(prefix) for prefix in CREATE_PREFIXES)



def _resolve_non_unique_replace_edits(
    edits: list[dict[str, Any]],
    payload: dict[str, Any],
    patterns: list[str],
    *,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    """Bind a repeated model find to the exact focused source occurrence.

    Architecture FORCE already chooses and sends a bounded exact source snippet
    to the model. If the model returns a replace whose find is repeated in the
    full file but occurs exactly once inside that exact snippet, Brain can
    deterministically widen the anchor with unchanged neighboring bytes until
    it is unique. The replacement receives the same unchanged prefix/suffix, so
    only the model's intended inner edit changes behavior. Any uncertainty
    remains fail-closed and is left for normal validation/correction.
    """
    focused_sources: dict[str, list[str]] = {}
    for source_key in (
        "sources",
        "materializedBaselineSources",
        "materializedFailureSources",
    ):
        values = payload.get(source_key)
        if not isinstance(values, dict):
            continue
        for path, snippet in values.items():
            text = str(snippet or "")
            if text:
                focused_sources.setdefault(str(path), []).append(text)
    if not focused_sources:
        return [dict(edit) for edit in edits]

    resolved: list[dict[str, Any]] = []
    for raw_edit in edits:
        edit = dict(raw_edit)
        if str(edit.get("operation") or "") != "replace":
            resolved.append(edit)
            continue
        path = str(edit.get("path") or "")
        find = str(edit.get("find") or "")
        replace = str(edit.get("replace") or "")
        target = root / path
        if (
            not path_allowed(path, patterns)
            or not target.is_file()
            or not find
            or len(find) > MAX_FIND
            or len(replace) > MAX_REPLACE
        ):
            resolved.append(edit)
            continue

        source = target.read_text(encoding="utf-8")
        occurrence_count = source.count(find)
        if occurrence_count <= 1:
            resolved.append(edit)
            continue

        snippet = ""
        for candidate_snippet in focused_sources.get(path, []):
            if (
                candidate_snippet
                and source.count(candidate_snippet) == 1
                and candidate_snippet.count(find) == 1
            ):
                snippet = candidate_snippet
                break
        if not snippet:
            resolved.append(edit)
            continue

        snippet_start = source.index(snippet)
        local_offset = snippet.index(find)
        absolute_start = snippet_start + local_offset
        if source[absolute_start:absolute_start + len(find)] != find:
            resolved.append(edit)
            continue

        available_extra = min(
            MAX_FIND - len(find),
            MAX_REPLACE - len(replace),
        )
        if available_extra <= 0:
            resolved.append(edit)
            continue

        unique_find = ""
        unique_replace = ""
        widths = list(range(16, available_extra + 1, 16))
        if not widths or widths[-1] != available_extra:
            widths.append(available_extra)
        for width in widths:
            left_budget = width // 2
            right_budget = width - left_budget
            left = min(left_budget, absolute_start)
            right = min(
                right_budget,
                len(source) - (absolute_start + len(find)),
            )
            missing = width - left - right
            if missing > 0:
                add_left = min(missing, absolute_start - left)
                left += add_left
                missing -= add_left
            if missing > 0:
                right += min(
                    missing,
                    len(source) - (absolute_start + len(find)) - right,
                )

            prefix = source[absolute_start - left:absolute_start]
            suffix = source[
                absolute_start + len(find):
                absolute_start + len(find) + right
            ]
            candidate_find = prefix + find + suffix
            candidate_replace = prefix + replace + suffix
            if (
                len(candidate_find) <= MAX_FIND
                and len(candidate_replace) <= MAX_REPLACE
                and source.count(candidate_find) == 1
            ):
                unique_find = candidate_find
                unique_replace = candidate_replace
                break

        if unique_find:
            edit["find"] = unique_find
            edit["replace"] = unique_replace
            print(
                "FIELD_BRAIN_ARCH_FORCE_ANCHOR_RESOLVED "
                f"path={path} repeated={occurrence_count} "
                f"find_chars={len(find)} anchored_chars={len(unique_find)}",
                flush=True,
            )
        resolved.append(edit)
    return resolved


def _bounded_unique_replace_from_sources(before: str, after: str) -> tuple[str, str] | None:
    """Collapse a full-file correction into one bounded unique baseline replace.

    Corrective Qwen turns may describe bytes from the rejected materialized
    candidate instead of the restored checkout.  Once the desired full source
    is known, reduce baseline -> desired back to the exact bounded replace
    contract used by FORCE.  Uncertainty or an oversized diff remains
    fail-closed.
    """
    if before == after:
        return None

    prefix = 0
    prefix_max = min(len(before), len(after))
    while prefix < prefix_max and before[prefix] == after[prefix]:
        prefix += 1

    suffix = 0
    suffix_max = min(len(before) - prefix, len(after) - prefix)
    while (
        suffix < suffix_max
        and before[len(before) - 1 - suffix] == after[len(after) - 1 - suffix]
    ):
        suffix += 1

    before_end = len(before) - suffix if suffix else len(before)
    after_end = len(after) - suffix if suffix else len(after)
    find_core = before[prefix:before_end]
    replace_core = after[prefix:after_end]

    # Exact find/replace cannot express a pure insertion. Bind one unchanged
    # neighboring byte into both sides so the operation remains reversible.
    if not find_core:
        if prefix > 0:
            prefix -= 1
            find_core = before[prefix:before_end]
            replace_core = after[prefix:after_end]
        elif before_end < len(before):
            before_end += 1
            after_end += 1
            find_core = before[prefix:before_end]
            replace_core = after[prefix:after_end]
        else:
            return None

    if len(find_core) > MAX_FIND or len(replace_core) > MAX_REPLACE:
        return None

    available_extra = min(
        MAX_FIND - len(find_core),
        MAX_REPLACE - len(replace_core),
    )
    widths = [0]
    if available_extra > 0:
        widths.extend(range(16, available_extra + 1, 16))
        if widths[-1] != available_extra:
            widths.append(available_extra)

    for width in widths:
        left_budget = width // 2
        right_budget = width - left_budget
        left = min(left_budget, prefix)
        right = min(right_budget, len(before) - before_end)
        missing = width - left - right
        if missing > 0:
            add_left = min(missing, prefix - left)
            left += add_left
            missing -= add_left
        if missing > 0:
            right += min(missing, len(before) - before_end - right)

        stable_prefix = before[prefix - left:prefix]
        stable_suffix = before[before_end:before_end + right]
        candidate_find = stable_prefix + find_core + stable_suffix
        candidate_replace = stable_prefix + replace_core + stable_suffix
        if (
            candidate_find
            and len(candidate_find) <= MAX_FIND
            and len(candidate_replace) <= MAX_REPLACE
            and before.count(candidate_find) == 1
        ):
            return candidate_find, candidate_replace
    return None


def _rebase_candidate_relative_replace_edits(
    corrected_edits: list[dict[str, Any]],
    rejected_edits: list[dict[str, Any]],
    patterns: list[str],
    *,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    """Project candidate-relative correction edits back onto restored bytes.

    Materialized validation is transactional: after a candidate fails, the
    checkout is restored before Qwen receives the failure. Qwen can correctly
    say "replace this byte from the rejected candidate", but that find string
    then occurs zero times in the restored baseline. Reconstruct the rejected
    candidate in memory, apply the correction there, and collapse the resulting
    desired source back into one exact unique baseline replace. Provider paths
    and ambiguous transformations remain untouched so normal validation fails
    closed.
    """
    corrected = [dict(edit) for edit in corrected_edits]
    candidate_paths: set[str] = set()
    for edit in corrected:
        if str(edit.get("operation") or "") != "replace":
            continue
        path = str(edit.get("path") or "")
        find = str(edit.get("find") or "")
        target = root / path
        if (
            path_allowed(path, patterns)
            and target.is_file()
            and find
            and target.read_text(encoding="utf-8").count(find) != 1
        ):
            candidate_paths.add(path)

    rebased: dict[str, dict[str, Any]] = {}
    for path in sorted(candidate_paths):
        target = root / path
        baseline = target.read_text(encoding="utf-8")
        rejected_for_path = [
            edit for edit in rejected_edits
            if str(edit.get("path") or "") == path
        ]
        corrected_for_path = [
            edit for edit in corrected
            if str(edit.get("path") or "") == path
        ]
        if (
            not rejected_for_path
            or not corrected_for_path
            or any(str(edit.get("operation") or "") != "replace" for edit in rejected_for_path)
            or any(str(edit.get("operation") or "") != "replace" for edit in corrected_for_path)
        ):
            continue

        candidate = baseline
        reconstructable = True
        for edit in rejected_for_path:
            find = str(edit.get("find") or "")
            replace = str(edit.get("replace") or "")
            if not find or candidate.count(find) != 1:
                reconstructable = False
                break
            candidate = candidate.replace(find, replace, 1)
        if not reconstructable:
            continue

        desired = candidate
        for edit in corrected_for_path:
            find = str(edit.get("find") or "")
            replace = str(edit.get("replace") or "")
            if not find or desired.count(find) != 1:
                reconstructable = False
                break
            desired = desired.replace(find, replace, 1)
        if not reconstructable:
            continue

        bounded = _bounded_unique_replace_from_sources(baseline, desired)
        if not bounded:
            continue
        find, replace = bounded
        rebased[path] = {
            "operation": "replace",
            "path": path,
            "find": find,
            "replace": replace,
        }
        print(
            "FIELD_BRAIN_ARCH_FORCE_CORRECTION_REBASED "
            f"path={path} rejected_edits={len(rejected_for_path)} "
            f"corrected_edits={len(corrected_for_path)} "
            f"find_chars={len(find)} replace_chars={len(replace)}",
            flush=True,
        )

    if not rebased:
        return corrected

    out: list[dict[str, Any]] = []
    emitted: set[str] = set()
    for edit in corrected:
        path = str(edit.get("path") or "")
        if path in rebased:
            if path not in emitted:
                out.append(rebased[path])
                emitted.add(path)
            continue
        out.append(edit)
    return out


def validate_edits(edits: list[dict[str, Any]], patterns: list[str], root: Path = ROOT) -> None:
    if not edits or len(edits) > MAX_EDITS:
        raise ValueError("architecture FORCE requires 1..3 bounded edits")
    code_edits = 0
    for edit in edits:
        op = str(edit.get("operation") or "")
        path = str(edit.get("path") or "")
        if not path_allowed(path, patterns):
            raise ValueError(f"architecture FORCE path outside allowlist: {path}")
        if not path.startswith("tests/"):
            code_edits += 1
        target = root / path
        if op == "replace":
            find = str(edit.get("find") or "")
            replace = str(edit.get("replace") or "")
            if not target.is_file():
                raise ValueError(f"replace target missing: {path}")
            if not find or len(find) > MAX_FIND or len(replace) > MAX_REPLACE:
                raise ValueError("invalid bounded replace")
            source = target.read_text(encoding="utf-8")
            if source.count(find) != 1:
                raise ValueError(f"replace find must occur exactly once: {path}")
            if find == replace:
                raise ValueError("architecture FORCE no-op")
        elif op == "create":
            body = str(edit.get("content") or "")
            if target.exists():
                raise ValueError(f"create target already exists: {path}")
            if not any(path.startswith(prefix) for prefix in CREATE_PREFIXES):
                raise ValueError("new files restricted to Brain layers/tests")
            if not body or len(body) > MAX_CREATE:
                raise ValueError("invalid bounded create")
        else:
            raise ValueError(f"unsupported architecture FORCE operation: {op}")
    if code_edits <= 0:
        raise ValueError("architecture FORCE must include an executable non-test change")


def apply_edits(edits: list[dict[str, Any]], root: Path = ROOT) -> list[str]:
    changed: list[str] = []
    for edit in edits:
        path = str(edit["path"])
        target = root / path
        if edit["operation"] == "replace":
            source = target.read_text(encoding="utf-8")
            target.write_text(source.replace(str(edit["find"]), str(edit.get("replace") or ""), 1), encoding="utf-8")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(edit["content"]), encoding="utf-8")
        changed.append(path)
    return changed


def validate_changed_syntax(changed: list[str], root: Path = ROOT) -> None:
    """Fail closed when a generated architecture edit cannot even parse/compile."""
    for path in changed:
        target = root / path
        suffix = target.suffix.casefold()
        if suffix == ".py":
            try:
                ast.parse(target.read_text(encoding="utf-8"), filename=path)
            except (SyntaxError, UnicodeError) as exc:
                detail = getattr(exc, "msg", None) or str(exc)
                line = getattr(exc, "lineno", None)
                where = f" line {line}" if line else ""
                raise ValueError(
                    f"materialized syntax validation failed: {path}{where}: {detail}"
                ) from exc
        elif suffix == ".json":
            try:
                json.loads(target.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeError) as exc:
                raise ValueError(
                    f"materialized JSON validation failed: {path}: {exc}"
                ) from exc
        elif suffix in {".js", ".mjs", ".cjs"}:
            result = subprocess.run(
                ["node", "--check", str(target)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "node --check failed").strip()
                raise ValueError(
                    f"materialized JavaScript validation failed: {path}: {detail[:800]}"
                )


MATERIALIZED_CONTRACT_TESTS = (
    "tests/brain_meta_learning_gap_synthesis_test.py",
    "tests/brain_architecture_force_materializer_test.py",
    "tests/brain_self_architecture_test.py",
)


def validate_materialized_contracts(
    changed: list[str],
    *,
    root: Path = ROOT,
) -> None:
    """Run the same focused Brain contracts before a generated edit is accepted.

    Architecture FORCE previously syntax-checked transactionally, then applied
    the edit permanently and only afterwards ran these tests in the workflow.
    That prevented same-run model correction for semantically invalid but
    parseable changes. Keep the tests bounded and fail closed inside the
    transaction so their exact failure becomes corrective feedback.
    """
    if not any(not str(path).startswith("tests/") for path in changed):
        return
    for relative in MATERIALIZED_CONTRACT_TESTS:
        test = root / relative
        if not test.is_file():
            continue
        result = subprocess.run(
            [sys.executable, str(test)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "contract test failed").strip()
            raise ValueError(
                f"materialized contract validation failed: {relative}: {detail[:1200]}"
            )


def _materialized_failure_snippet(before: str, after: str, limit: int) -> str:
    """Return exact bounded context centered on bytes changed by a candidate."""
    if limit <= 0 or not after:
        return ""
    if before == after:
        return after[:limit]
    prefix = 0
    prefix_max = min(len(before), len(after))
    while prefix < prefix_max and before[prefix] == after[prefix]:
        prefix += 1
    suffix = 0
    suffix_max = min(len(before) - prefix, len(after) - prefix)
    while (
        suffix < suffix_max
        and before[len(before) - 1 - suffix] == after[len(after) - 1 - suffix]
    ):
        suffix += 1
    changed_end = len(after) - suffix if suffix else len(after)
    changed_end = max(prefix + 1, changed_end)
    changed_len = max(1, changed_end - prefix)
    if changed_len >= limit:
        return after[prefix:prefix + limit]
    spare = limit - changed_len
    left = min(prefix, spare // 2)
    right = min(len(after) - changed_end, spare - left)
    missing = spare - left - right
    if missing > 0:
        add_left = min(prefix - left, missing)
        left += add_left
        missing -= add_left
    if missing > 0:
        right += min(len(after) - changed_end - right, missing)
    return after[prefix - left:changed_end + right]


def validate_materialized_edits(
    edits: list[dict[str, Any]],
    *,
    root: Path = ROOT,
) -> list[str]:
    """Apply edits transactionally, validate syntax/contracts, then restore baseline."""
    snapshots: dict[str, tuple[bool, bytes]] = {}
    for edit in edits:
        path = str(edit.get("path") or "")
        target = root / path
        snapshots[path] = (target.exists(), target.read_bytes() if target.exists() else b"")

    changed: list[str] = []
    try:
        changed = apply_edits(edits, root=root)
        validate_changed_syntax(changed, root=root)
        validate_materialized_contracts(changed, root=root)
        return changed
    except ValueError as exc:
        remaining = MAX_MATERIALIZED_FAILURE_CONTEXT
        candidate_sources: dict[str, str] = {}
        baseline_sources: dict[str, str] = {}
        for path in changed:
            if remaining <= 0:
                break
            target = root / path
            if not target.is_file():
                continue
            try:
                text = target.read_text(encoding="utf-8")
                baseline = snapshots.get(path, (False, b""))[1].decode("utf-8")
            except (UnicodeError, OSError):
                continue
            limit = min(remaining, 2200)
            snippet = _materialized_failure_snippet(
                baseline,
                text,
                limit,
            )
            baseline_snippet = _materialized_failure_snippet(
                text,
                baseline,
                limit,
            )
            if snippet:
                candidate_sources[path] = snippet
                remaining -= len(snippet)
            if baseline_snippet:
                baseline_sources[path] = baseline_snippet
        raise MaterializedValidationError(
            str(exc),
            candidate_sources,
            baseline_sources,
        ) from exc
    finally:
        for path, (existed, content) in snapshots.items():
            target = root / path
            if existed:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            elif target.exists():
                target.unlink()


def select_blueprint(proposal: dict[str, Any]) -> dict[str, Any]:
    rows = [x for x in proposal.get("strategyBlueprints") or [] if isinstance(x, dict)]
    eligible = [x for x in rows if x.get("forcePromotionEligible") is True]
    if not eligible:
        raise ValueError("no FORCE-promotable architecture blueprint")
    return eligible[0]


def _blueprint_focus_terms(blueprint: dict[str, Any]) -> list[str]:
    """Return bounded source-search terms that describe the executable strategy."""
    raw = [
        str(blueprint.get(key) or "").strip().casefold()
        for key in (
            "strategyId",
            "repairScope",
            "capabilityStrategy",
            "groupId",
            "causalTrigger",
            "method",
        )
    ]
    ignored = {
        "provider", "core", "repair", "strategy", "runtime", "current",
        "bounded", "evidence", "provider-owned", "not-applicable",
    }
    terms: list[str] = []
    for value in raw:
        if not value:
            continue
        candidates = [value]
        candidates.extend(re.findall(r"[a-z0-9_][a-z0-9_-]{3,}", value))
        for term in candidates:
            term = term.strip(" -_")
            if len(term) < 4 or term in ignored or term in terms:
                continue
            terms.append(term)
            if len(terms) >= 24:
                return terms
    return terms


def _focused_source_snippet(text: str, blueprint: dict[str, Any], limit: int) -> str:
    """Prefer executable strategy neighborhoods over unrelated file prefixes."""
    if limit <= 0 or not text:
        return ""
    if len(text) <= limit:
        return text

    strategy_id = str(blueprint.get("strategyId") or "").strip()
    anchors: list[str] = []
    if strategy_id:
        anchors.extend([
            f'new_strategy_id == "{strategy_id}"',
            f"new_strategy_id == '{strategy_id}'",
            f'"{strategy_id}"',
            f"'{strategy_id}'",
            strategy_id,
        ])
    anchors.extend(_blueprint_focus_terms(blueprint))

    lowered = text.casefold()
    terms = _blueprint_focus_terms(blueprint)
    candidates: list[tuple[int, int, str]] = []
    seen_positions: set[int] = set()
    for anchor_rank, anchor in enumerate(anchors):
        needle = anchor.casefold()
        if not needle:
            continue
        start_at = 0
        while True:
            pos = lowered.find(needle, start_at)
            if pos < 0:
                break
            start_at = pos + max(1, len(needle))
            if pos in seen_positions:
                continue
            seen_positions.add(pos)
            start = max(0, pos - limit // 3)
            end = min(len(text), start + limit)
            start = max(0, end - limit)
            window = text[start:end]
            window_lower = window.casefold()
            score = max(0, 20 - anchor_rank)
            if "new_strategy_id ==" in window:
                score += 30
            if strategy_id:
                score += min(30, 10 * window_lower.count(strategy_id.casefold()))
            score += sum(min(3, window_lower.count(term)) for term in terms[:12])
            candidates.append((score, pos, window))

    if not candidates:
        return text[:limit]
    candidates.sort(key=lambda row: (-row[0], row[1]))
    return candidates[0][2]


def source_context(blueprint: dict[str, Any], patterns: list[str]) -> dict[str, str]:
    layer = str(blueprint.get("targetLayer") or "")
    candidates = ["scripts/brain_meta_learning.py", "scripts/brain_repair_runtime.py"]
    if layer in {"provider", "core"}:
        candidates.append("scripts/adaptive_runtime/runtime_repair.py")
    elif layer in {"harness", "network", "client-runtime"}:
        candidates.append("scripts/nuvio_client_lab.cjs")
    else:
        candidates.append("scripts/run_brain_learning_sandbox.py")
    out: dict[str, str] = {}
    remaining = MAX_TOTAL_SOURCE_CONTEXT
    for path in candidates:
        if remaining <= 0:
            break
        if path_allowed(path, patterns) and (ROOT / path).is_file():
            text = (ROOT / path).read_text(encoding="utf-8")
            snippet = _focused_source_snippet(
                text,
                blueprint,
                min(MAX_SOURCE_SNIPPET, remaining),
            )
            if snippet:
                out[path] = snippet
                remaining -= len(snippet)
    return out


def _response_format(exact_paths: list[str] | None = None) -> dict[str, Any]:
    path_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    if exact_paths:
        path_schema["enum"] = sorted({str(path) for path in exact_paths if str(path)})
    return {
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "edits": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_EDITS,
                    "items": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["replace", "create"],
                            },
                            "path": path_schema,
                            "find": {"type": "string", "maxLength": MAX_FIND},
                            "replace": {"type": "string", "maxLength": MAX_REPLACE},
                            "content": {"type": "string", "maxLength": MAX_CREATE},
                        },
                        "required": ["operation", "path"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["edits"],
            "additionalProperties": False,
        },
    }


def _model_request(
    endpoint: str,
    model: str,
    payload: dict[str, Any],
    *,
    max_tokens: int,
    timeout: int,
    compact: bool = False,
) -> dict[str, Any]:
    system = (
        "You are NiakVIO Brain architecture FORCE materializer. "
        "Return JSON only: {edits:[...]}. Create the smallest executable architecture change "
        "that implements the supplied blueprint. Never edit providers, manifests, ProviderBase, "
        "publication files or secrets. Use only exact source snippets supplied. Max 3 edits. "
        "Allowed operations: replace {operation,path,find,replace}; create {operation,path,content}. "
        "New files only under scripts/brain_layers/ or tests/brain_. "
        "Prefer one minimal code edit plus one focused test. The resulting source must parse/compile. No prose."
    )
    if compact:
        system += (
            " Be extremely compact. Prefer exactly one small replace edit. "
            "Avoid creating a new file unless replacement cannot implement the capability. "
            "Keep the complete JSON response short enough for the supplied token budget. "
            "The server enforces the edits JSON schema; never emit markdown or commentary."
        )
    exact_paths = [
        str(path)
        for path in (payload.get("exactAllowedPaths") or [])
        if str(path)
    ]
    if exact_paths:
        system += (
            " For this corrective request, edit only a path from exactAllowedPaths. "
            "Do not rewrite, prefix, relocate, normalize or invent a path. "
            "Paths listed in existingAllowedPaths already exist and MUST use replace, never create. "
            "Use create only for a path listed in newAllowedPaths."
        )
    if str(payload.get("correctionReason") or "") == "materialized-syntax-validation":
        system += (
            " Repair only the parser defect in the rejected candidate. "
            "Use materializedFailureSources as candidate bytes and materializedBaselineSources as original bytes. "
            "Preserve the intended change, avoid duplicate surrounding tokens, and prefer one small replace."
        )
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": _response_format(exact_paths),
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
            },
        ],
    }
    req = Request(
        endpoint.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = ""
        raise RuntimeError(
            f"architecture model HTTP {exc.code}: {error_body[:1200] or exc.reason}"
        ) from exc


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    compact = dict(payload)
    remaining = RETRY_SOURCE_CONTEXT
    sources: dict[str, str] = {}
    for path, text in (payload.get("sources") or {}).items():
        if remaining <= 0:
            break
        snippet = str(text)[: min(2600, remaining)]
        if snippet:
            sources[str(path)] = snippet
            remaining -= len(snippet)
    compact["sources"] = sources
    keep = {
        "capability_gap_detector",
        "meta_learning_gap_synthesis",
        "architecture_layer_synthesis",
        "verification_contract_synthesis",
    }
    compact["architectureLayers"] = [
        row
        for row in (payload.get("architectureLayers") or [])
        if isinstance(row, dict) and str(row.get("id") or "") in keep
    ]
    return compact


def _minimal_payload(payload: dict[str, Any]) -> dict[str, Any]:
    minimal = {
        "blueprint": payload.get("blueprint") or {},
        "allowedPaths": payload.get("allowedPaths") or [],
        "contract": payload.get("contract") or {},
    }
    remaining = MINIMAL_SOURCE_CONTEXT
    sources: dict[str, str] = {}
    for path, text in (payload.get("sources") or {}).items():
        if remaining <= 0:
            break
        snippet = str(text)[: min(1800, remaining)]
        if snippet:
            sources[str(path)] = snippet
            remaining -= len(snippet)
    minimal["sources"] = sources
    return minimal


def _validation_retry_payload(
    payload: dict[str, Any],
    error: Exception,
    edits: list[dict[str, Any]],
    *,
    extra_exact_paths: list[str] | None = None,
    restrict_to_extra_paths: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    retry = _minimal_payload(payload)
    source_paths = {
        str(path)
        for path in (retry.get("sources") or {}).keys()
        if str(path)
    }
    extra_paths = {
        str(path)
        for path in (extra_exact_paths or [])
        if str(path)
    }
    exact_paths = sorted(extra_paths if restrict_to_extra_paths and extra_paths else source_paths | extra_paths)
    if restrict_to_extra_paths and extra_paths:
        retry["sources"] = {
            path: text
            for path, text in (retry.get("sources") or {}).items()
            if path in extra_paths
        }
    existing_paths = [path for path in exact_paths if (root / path).is_file()]
    new_paths = [
        path for path in exact_paths
        if not (root / path).exists()
        and any(path.startswith(prefix) for prefix in CREATE_PREFIXES)
    ]
    retry["exactAllowedPaths"] = exact_paths
    retry["existingAllowedPaths"] = existing_paths
    retry["newAllowedPaths"] = new_paths
    retry["validationError"] = str(error)[:800]
    retry["rejectedEditIntent"] = [
        {
            "operation": str(edit.get("operation") or ""),
            "find": str(edit.get("find") or "")[:400],
            "replace": str(edit.get("replace") or "")[:900],
            "content": str(edit.get("content") or "")[:900],
        }
        for edit in edits[:MAX_EDITS]
    ]
    retry["correctionContract"] = {
        "pathMustBeOneOfExactAllowedPaths": True,
        "existingPathsMustUseReplace": True,
        "createOnlyForNewAllowedPaths": True,
        "doNotInventPaths": True,
        "doNotRelocatePaths": True,
        "changeOnlyWhatValidationRejected": True,
        "preferSingleSmallReplace": True,
        "reuseRejectedIntentWhenValid": True,
        "maxEdits": MAX_EDITS,
    }
    return retry


def _extract_balanced_object(raw: str) -> str:
    start = raw.find("{")
    if start < 0:
        raise ValueError("architecture model output contains no object")
    depth = 0
    in_string = False
    escaped = False
    quote = ""
    for index in range(start, len(raw)):
        char = raw[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
            continue
        if char in {'"', "'"}:
            in_string = True
            quote = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw[start:index + 1]
    raise ValueError("architecture model output contains an unbalanced object")


def _parse_model_value(value: dict[str, Any]) -> dict[str, Any]:
    raw = str(value["choices"][0]["message"]["content"]).strip()
    if raw.startswith("~~~") or raw.startswith(chr(96) * 3):
        raw = "\n".join(raw.splitlines()[1:-1]).strip()
        if raw.casefold().startswith("json"):
            raw = raw[4:].lstrip()

    candidate = _extract_balanced_object(raw)
    attempts = [candidate]
    no_trailing_commas = re.sub(r",\s*([}\]])", r"\1", candidate)
    if no_trailing_commas != candidate:
        attempts.append(no_trailing_commas)

    for attempt in attempts:
        try:
            parsed = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            raise ValueError("architecture model output must be object")
        return parsed

    # Qwen occasionally emits a Python-style dict (single quotes) despite the
    # JSON-only instruction. literal_eval parses literals only and never runs
    # arbitrary code; all returned edits are still validated by the allowlist.
    try:
        parsed = ast.literal_eval(no_trailing_commas)
    except (ValueError, SyntaxError) as exc:
        raise ValueError("architecture model output is not valid bounded JSON/object") from exc
    if not isinstance(parsed, dict):
        raise ValueError("architecture model output must be object")
    return parsed


def call_model(endpoint: str, model: str, payload: dict[str, Any]) -> dict[str, Any]:
    # Architecture FORCE runs on CPU-hosted Qwen in GitHub Actions. Keep both
    # attempts wall-clock bounded, but retry not only transport timeouts: a
    # max-token-truncated JSON object is also a recoverable model-format failure.
    try:
        value = _model_request(
            endpoint,
            model,
            _compact_payload(payload),
            max_tokens=MAX_MODEL_TOKENS,
            timeout=MODEL_TIMEOUT_SECONDS,
            compact=True,
        )
        return _parse_model_value(value)
    except (TimeoutError, ValueError) as exc:
        reason = "timeout" if isinstance(exc, TimeoutError) else "invalid-json"
        print(
            f"FIELD_BRAIN_ARCH_FORCE_MODEL_RETRY reason={reason} mode=minimal",
            flush=True,
        )
        value = _model_request(
            endpoint,
            model,
            _minimal_payload(payload),
            max_tokens=RETRY_MODEL_TOKENS,
            timeout=RETRY_MODEL_TIMEOUT_SECONDS,
            compact=True,
        )
        return _parse_model_value(value)

def _request_corrected_plan(
    endpoint: str,
    model: str,
    correction_payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        value = _model_request(
            endpoint,
            model,
            correction_payload,
            max_tokens=VALIDATION_RETRY_MODEL_TOKENS,
            timeout=VALIDATION_RETRY_TIMEOUT_SECONDS,
            compact=True,
        )
        return _parse_model_value(value)
    except (TimeoutError, ValueError) as correction_exc:
        reason = "timeout" if isinstance(correction_exc, TimeoutError) else "invalid-json"
        print(
            "FIELD_BRAIN_ARCH_FORCE_MODEL_RETRY "
            f"reason=corrective-{reason} mode=corrective-format-retry",
            flush=True,
        )
        value = _model_request(
            endpoint,
            model,
            correction_payload,
            max_tokens=VALIDATION_FORMAT_RETRY_MODEL_TOKENS,
            timeout=VALIDATION_FORMAT_RETRY_TIMEOUT_SECONDS,
            compact=True,
        )
        return _parse_model_value(value)


def validated_model_plan(
    endpoint: str,
    model: str,
    payload: dict[str, Any],
    patterns: list[str],
    *,
    root: Path = ROOT,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    planned = call_model(endpoint, model, payload)
    edits = [dict(x) for x in planned.get("edits") or [] if isinstance(x, dict)]
    validation_payload = payload
    for correction_round in range(0, EDIT_VALIDATION_CORRECTION_ROUNDS + 1):
        edits = _resolve_non_unique_replace_edits(
            edits,
            validation_payload,
            patterns,
            root=root,
        )
        try:
            validate_edits(edits, patterns, root=root)
            break
        except ValueError as exc:
            if correction_round >= EDIT_VALIDATION_CORRECTION_ROUNDS:
                raise
            print(
                "FIELD_BRAIN_ARCH_FORCE_MODEL_RETRY "
                f"reason=edit-validation mode=corrective round={correction_round + 1} "
                f"error={str(exc)[:240]}",
                flush=True,
            )
            exact_paths = [
                str(edit.get("path") or "")
                for edit in edits
                if str(edit.get("path") or "")
                and path_allowed(str(edit.get("path") or ""), patterns)
            ]
            correction_payload = _validation_retry_payload(
                validation_payload,
                exc,
                edits,
                extra_exact_paths=exact_paths,
                root=root,
            )
            correction_payload["correctionReason"] = "edit-validation"
            correction_payload["correctionContract"].update({
                "editValidationCorrectionRound": correction_round + 1,
                "editValidationCorrectionRounds": EDIT_VALIDATION_CORRECTION_ROUNDS,
            })
            planned = _request_corrected_plan(endpoint, model, correction_payload)
            edits = [
                dict(x) for x in planned.get("edits") or [] if isinstance(x, dict)
            ]
            validation_payload = correction_payload

    try:
        validate_materialized_edits(edits, root=root)
        return planned, edits
    except ValueError as exc:
        current_error: ValueError = exc
        current_edits = edits

    for correction_round in range(1, MATERIALIZED_CORRECTION_ROUNDS + 1):
        print(
            "FIELD_BRAIN_ARCH_FORCE_MODEL_RETRY "
            f"reason=materialized-validation mode=corrective round={correction_round} "
            f"error={str(current_error)[:240]}",
            flush=True,
        )
        exact_paths = [
            str(edit.get("path") or "")
            for edit in current_edits
            if str(edit.get("path") or "")
            and path_allowed(str(edit.get("path") or ""), patterns)
        ]
        correction_payload = _validation_retry_payload(
            payload,
            current_error,
            current_edits,
            extra_exact_paths=exact_paths,
            restrict_to_extra_paths=True,
            root=root,
        )
        candidate_sources = getattr(current_error, "candidate_sources", {})
        baseline_sources = getattr(current_error, "baseline_sources", {})
        if isinstance(candidate_sources, dict) and candidate_sources:
            correction_payload["materializedFailureSources"] = candidate_sources
        if isinstance(baseline_sources, dict) and baseline_sources:
            correction_payload["materializedBaselineSources"] = baseline_sources
        validation_text = str(current_error).casefold()
        syntax_failure = any(marker in validation_text for marker in (
            "syntax validation failed",
            "json validation failed",
            "javascript validation failed",
        ))
        correction_payload["correctionReason"] = (
            "materialized-syntax-validation"
            if syntax_failure
            else "materialized-source-validation"
        )
        correction_payload["correctionContract"].update({
            "mustPassMaterializedSyntaxValidation": True,
            "mustPassMaterializedContractValidation": True,
            "doNotRepeatRejectedReplacement": True,
            "useMaterializedFailureSources": bool(candidate_sources),
            "useMaterializedBaselineSources": bool(baseline_sources),
            "materializedCorrectionRound": correction_round,
            "materializedCorrectionRounds": MATERIALIZED_CORRECTION_ROUNDS,
            "syntaxRepairOnly": syntax_failure,
            "preserveValidatedIntent": syntax_failure,
            "doNotConcatenateCandidateAndBaseline": syntax_failure,
            "doNotDuplicateSurroundingTokens": syntax_failure,
        })

        corrected = _request_corrected_plan(endpoint, model, correction_payload)
        corrected_edits = [
            dict(x) for x in corrected.get("edits") or [] if isinstance(x, dict)
        ]
        corrected_edits = _resolve_non_unique_replace_edits(
            corrected_edits,
            correction_payload,
            patterns,
            root=root,
        )
        corrected_edits = _rebase_candidate_relative_replace_edits(
            corrected_edits,
            current_edits,
            patterns,
            root=root,
        )
        try:
            validate_edits(corrected_edits, patterns, root=root)
            validate_materialized_edits(corrected_edits, root=root)
            return corrected, corrected_edits
        except ValueError as correction_error:
            current_error = correction_error
            current_edits = corrected_edits

    raise current_error


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--proposal", type=Path, required=True)
    p.add_argument("--self-config", type=Path, required=True)
    p.add_argument("--endpoint", default="http://127.0.0.1:8080")
    p.add_argument("--model", default="qwen2.5-coder-3b")
    p.add_argument("--response-file", type=Path)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()

    proposal = load(a.proposal)
    config = load(a.self_config)
    force = config.get("forceArchitecture") if isinstance(config.get("forceArchitecture"), dict) else {}
    if force.get("enabled") is not True:
        raise SystemExit("architecture FORCE disabled")
    blueprint = select_blueprint(proposal)
    patterns = allowed_patterns(config)
    payload = {
        "blueprint": blueprint,
        "architectureLayers": proposal.get("architectureLayers") or [],
        "allowedPaths": patterns,
        "sources": source_context(blueprint, patterns),
        "contract": {
            "providerPublicationAuthority": False,
            "productionProviderWritesAllowed": False,
            "requireExecutableDiff": True,
            "requireTargetedTests": True,
        },
    }
    if a.response_file:
        planned = load(a.response_file)
        edits = [dict(x) for x in planned.get("edits") or [] if isinstance(x, dict)]
        validate_edits(edits, patterns)
        validate_materialized_edits(edits)
    else:
        planned, edits = validated_model_plan(
            a.endpoint,
            a.model,
            payload,
            patterns,
        )
    changed = apply_edits(edits) if a.apply else [str(x.get("path") or "") for x in edits]
    report = {
        "schemaVersion": 1,
        "strategyId": blueprint.get("strategyId"),
        "targetLayer": blueprint.get("targetLayer"),
        "changedFiles": changed,
        "editCount": len(edits),
        "applied": bool(a.apply),
        "providerPublicationAuthority": False,
        "productionProviderWritesAllowed": False,
        "requiresTargetedTests": True,
        "requiresRequiredCi": True,
    }
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("FIELD_BRAIN_ARCH_FORCE_MATERIALIZED edits=%d files=%s" % (len(edits), ",".join(changed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
