#!/usr/bin/env python3
"""NiakVIO-aware Provider v3 JavaScript minimizer.

This is deliberately not a generic JavaScript minifier. It preserves strings,
template literal payloads, block comments and every managed Provider v3 marker;
never renames identifiers; never folds or reorders expressions; and never uses
Terser. Production transformations are restricted to horizontal indentation,
trailing horizontal whitespace, and blank lines while the lexer is in ordinary
JavaScript code (including template-expression code).

The lexer tracks multiline strings/comments and nested template expressions so
template payload bytes are never rewritten. The result must be idempotent and
parse as JavaScript before publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ROOT / "providers"
MANIFEST = ROOT / "manifest.json"
EXPECTED_PROVIDER_COUNT = 46

PRODUCTION_ENABLED = True
TERSER_ALLOWED = False
TRANSFORMATIONS_ENABLED = [
    "code-line-leading-indentation",
    "code-line-trailing-whitespace",
    "code-blank-lines",
]

MARKERS = (
    "BEGIN NIAKVIO_PROVIDER",
    "END NIAKVIO_PROVIDER",
    "STARTFIX:",
    "CLOSEFIX:",
    "FIXDATA:",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
)

_CODEISH = {"code", "template_expr"}


class MinimizeResult:
    __slots__ = ("text", "saved_bytes", "transformed_lines", "skipped_reason")

    def __init__(
        self,
        *,
        text: str,
        saved_bytes: int,
        transformed_lines: int,
        skipped_reason: str = "",
    ) -> None:
        self.text = text
        self.saved_bytes = int(saved_bytes)
        self.transformed_lines = int(transformed_lines)
        self.skipped_reason = str(skipped_reason)


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1], line[-1:]
    return line, ""


def _ctx(kind: str, **extra: int) -> dict[str, int | str]:
    row: dict[str, int | str] = {"kind": kind}
    row.update(extra)
    return row


def _kind(stack: list[dict[str, int | str]]) -> str:
    return str(stack[-1]["kind"])


def _scan_line(line: str, stack: list[dict[str, int | str]]) -> None:
    """Advance a conservative JS lexical stack using original source bytes."""
    i = 0
    while i < len(line):
        kind = _kind(stack)
        ch = line[i]
        nxt = line[i + 1] if i + 1 < len(line) else ""

        if kind == "block_comment":
            if ch == "*" and nxt == "/":
                stack.pop()
                i += 2
            else:
                i += 1
            continue

        if kind in {"single", "double"}:
            quote = "'" if kind == "single" else '"'
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                stack.pop()
            i += 1
            continue

        if kind == "template":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                stack.pop()
                i += 1
                continue
            if ch == "$" and nxt == "{":
                stack.append(_ctx("template_expr", depth=1))
                i += 2
                continue
            i += 1
            continue

        # Ordinary code or template-expression code.
        if ch == "/" and nxt == "/":
            # Line comments end at the physical line ending and do not alter
            # the persistent lexical stack.
            return
        if ch == "/" and nxt == "*":
            stack.append(_ctx("block_comment"))
            i += 2
            continue
        if ch == "'":
            stack.append(_ctx("single"))
            i += 1
            continue
        if ch == '"':
            stack.append(_ctx("double"))
            i += 1
            continue
        if ch == "`":
            stack.append(_ctx("template"))
            i += 1
            continue

        if kind == "template_expr":
            if ch == "{":
                stack[-1]["depth"] = int(stack[-1].get("depth", 1)) + 1
                i += 1
                continue
            if ch == "}":
                depth = int(stack[-1].get("depth", 1)) - 1
                if depth <= 0:
                    stack.pop()
                else:
                    stack[-1]["depth"] = depth
                i += 1
                continue

        i += 1


def minimize_text(text: str) -> MinimizeResult:
    stack: list[dict[str, int | str]] = [_ctx("code")]
    out: list[str] = []
    transformed = 0

    for raw_line in text.splitlines(keepends=True):
        body, ending = _split_line_ending(raw_line)
        original_body = body
        start_kind = _kind(stack)

        # All lexical decisions are made from original bytes. Only horizontal
        # whitespace outside protected literal/comment payloads is touched.
        if start_kind in _CODEISH:
            body = body.lstrip(" \t")

        _scan_line(original_body, stack)
        end_kind = _kind(stack)

        if end_kind in _CODEISH:
            body = body.rstrip(" \t")

        # Removing an empty code-only physical line leaves the previous line's
        # terminator in place, so adjacent JavaScript statements still retain
        # a line boundary for ASI-sensitive runtimes.
        drop_blank = (
            not body
            and bool(ending)
            and start_kind in _CODEISH
            and end_kind in _CODEISH
        )

        candidate = "" if drop_blank else body + ending
        if candidate != raw_line:
            transformed += 1
        out.append(candidate)

    minimized = "".join(out)
    saved = len(text.encode("utf-8")) - len(minimized.encode("utf-8"))
    if saved < 0:
        raise ValueError(f"minimizer increased provider bytes: saved={saved}")
    return MinimizeResult(
        text=minimized,
        saved_bytes=saved,
        transformed_lines=transformed,
    )


def audit_text(text: str) -> dict:
    encoded = text.encode("utf-8")
    lines = text.splitlines()
    indentation = sum(len(line) - len(line.lstrip(" \t")) for line in lines)
    trailing = sum(len(line) - len(line.rstrip(" \t")) for line in lines)
    blank = sum(1 for line in lines if not line.strip())
    return {
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "lines": len(lines),
        "blank_lines": blank,
        "indentation_bytes": indentation,
        "trailing_space_bytes": trailing,
        "template_literal_tokens": text.count("`"),
        "markers": {marker: text.count(marker) for marker in MARKERS},
    }


def validate_transform(original: str, minimized: str) -> None:
    before = audit_text(original)
    after = audit_text(minimized)

    if after["bytes"] > before["bytes"]:
        raise ValueError("minimizer increased provider bytes")
    if before["markers"] != after["markers"]:
        raise ValueError("minimizer changed Provider v3 structural markers")
    if before["template_literal_tokens"] != after["template_literal_tokens"]:
        raise ValueError("minimizer changed template literal token cardinality")

    expected = minimize_text(original).text
    if expected != minimized:
        raise ValueError("minimized bytes are not the deterministic NiakVIO transform")
    if minimize_text(minimized).text != minimized:
        raise ValueError("minimizer is not idempotent")


def minimize_provider_text(text: str) -> str:
    result = minimize_text(text)
    validate_transform(text, result.text)
    return result.text


def provider_files() -> list[Path]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    filenames = [
        str(row.get("filename") or "").strip()
        for row in (manifest.get("scrapers") or [])
        if str(row.get("filename") or "").strip()
    ]
    if len(filenames) != EXPECTED_PROVIDER_COUNT or len(set(filenames)) != EXPECTED_PROVIDER_COUNT:
        raise SystemExit(
            f"expected {EXPECTED_PROVIDER_COUNT} unique manifest provider filenames, "
            f"got {len(filenames)} / {len(set(filenames))}"
        )
    files: list[Path] = []
    for filename in filenames:
        path = (ROOT / filename).resolve()
        if PROVIDERS.resolve() not in path.parents:
            raise SystemExit(f"manifest provider path escapes providers/: {filename}")
        if not path.is_file():
            raise SystemExit(f"manifest provider asset missing: {filename}")
        files.append(path)
    return files


def _node_check(text: str, name: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        proc = subprocess.run(
            ["node", "--check", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise ValueError(f"Node parse failed for {name}: {proc.stdout}{proc.stderr}")


def portfolio_report(*, syntax_check: bool = False) -> dict:
    files = provider_files()
    rows = []
    totals = {
        "bytes_before": 0,
        "bytes_after": 0,
        "saved_bytes": 0,
        "transformed_lines": 0,
        "skipped_templates": 0,
    }

    for path in files:
        original = path.read_text(encoding="utf-8")
        result = minimize_text(original)
        validate_transform(original, result.text)
        if syntax_check:
            _node_check(result.text, path.name)

        before = audit_text(original)
        after = audit_text(result.text)
        row = {
            "file": path.name,
            "before": before,
            "after": after,
            "saved_bytes": result.saved_bytes,
            "transformed_lines": result.transformed_lines,
            "skipped_reason": result.skipped_reason,
        }
        rows.append(row)
        totals["bytes_before"] += before["bytes"]
        totals["bytes_after"] += after["bytes"]
        totals["saved_bytes"] += result.saved_bytes
        totals["transformed_lines"] += result.transformed_lines

    return {
        "schema_version": 3,
        "mode": "niakvio-safe-minimizer",
        "production_enabled": PRODUCTION_ENABLED,
        "terser_allowed": TERSER_ALLOWED,
        "provider_count": len(files),
        "transformations_enabled": list(TRANSFORMATIONS_ENABLED),
        "safety_contract": [
            "preserve every managed Provider v3 marker cardinality",
            "preserve bytes inside multiline strings, template payloads and block comments",
            "track nested template expressions before touching line whitespace",
            "never rename identifiers",
            "never reorder or fold expressions",
            "never use Terser",
            "retain a physical line boundary between adjacent nonblank code lines",
            f"require idempotence and Node syntax on all {EXPECTED_PROVIDER_COUNT} current providers",
        ],
        "totals": totals,
        "providers": rows,
    }


def write_preview(directory: Path, *, syntax_check: bool = True) -> dict:
    resolved = directory.resolve()
    providers_root = PROVIDERS.resolve()
    if resolved == providers_root or providers_root in resolved.parents:
        raise SystemExit("minimizer preview may never write inside providers/")
    resolved.mkdir(parents=True, exist_ok=True)

    report = portfolio_report(syntax_check=syntax_check)
    by_name = {path.name: path for path in provider_files()}
    for row in report["providers"]:
        path = by_name[row["file"]]
        minimized = minimize_provider_text(path.read_text(encoding="utf-8"))
        (resolved / path.name).write_text(minimized, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--syntax-check", action="store_true")
    parser.add_argument("--published-fixed-point", action="store_true")
    args = parser.parse_args()

    report = portfolio_report(syntax_check=args.syntax_check)
    if report["provider_count"] != EXPECTED_PROVIDER_COUNT:
        raise SystemExit(
            f"expected {EXPECTED_PROVIDER_COUNT} generated providers, got {report['provider_count']}"
        )

    if args.preview_dir:
        report = write_preview(args.preview_dir, syntax_check=True)

    if args.published_fixed_point:
        non_fixed = []
        for path in provider_files():
            text = path.read_text(encoding="utf-8")
            result = minimize_text(text)
            if result.text != text:
                non_fixed.append((path.name, result.saved_bytes))
        if non_fixed:
            detail = ", ".join(f"{name}:{saved}" for name, saved in non_fixed[:20])
            raise SystemExit(f"published providers are not minimizer fixed-point: {detail}")

    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        resolved = args.output.resolve()
        providers_root = PROVIDERS.resolve()
        if resolved == providers_root or providers_root in resolved.parents:
            raise SystemExit("minimizer report may never write inside providers/")
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(payload, encoding="utf-8")

    totals = report["totals"]
    if args.json:
        print(payload, end="")
    else:
        print(
            "FIELD_PROVIDER_V3_MINIMIZER "
            f"providers={report['provider_count']} "
            f"bytes_before={totals['bytes_before']} bytes_after={totals['bytes_after']} "
            f"saved_bytes={totals['saved_bytes']} transformed_lines={totals['transformed_lines']} "
            f"skipped_templates={totals['skipped_templates']} "
            f"production_enabled={str(PRODUCTION_ENABLED).lower()} terser_allowed=false"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
