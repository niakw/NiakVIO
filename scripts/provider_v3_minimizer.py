#!/usr/bin/env python3
"""NiakVIO-aware Provider v3 JavaScript minimizer.

This is deliberately not a generic JavaScript minifier. It preserves every line
terminator and every byte inside strings, templates and block comments, never
renames identifiers, never folds/reorders expressions, and never removes managed
comments/markers. The only production transformation is removal of leading
spaces/tabs on lines that begin in ordinary JavaScript code state.

That narrow transform is enough to reduce generated Provider v3 bytes while
remaining compatible with STARTFIX/CLOSEFIX/FIXDATA ownership and ASI-sensitive
QuickJS/native runtimes.
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

PRODUCTION_ENABLED = True
TERSER_ALLOWED = False
TRANSFORMATIONS_ENABLED = ["code-line-leading-indentation"]

MARKERS = (
    "BEGIN NIAKVIO_PROVIDER",
    "END NIAKVIO_PROVIDER",
    "STARTFIX:",
    "CLOSEFIX:",
    "FIXDATA:",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
)


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


def _next_state(line: str, initial: str) -> str:
    """Track only constructs that may legally continue onto the next line."""
    state = initial
    i = 0
    while i < len(line):
        ch = line[i]
        nxt = line[i + 1] if i + 1 < len(line) else ""

        if state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 2
                continue
            i += 1
            continue

        if state in {"single", "double"}:
            quote = "'" if state == "single" else '"'
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                state = "code"
            i += 1
            continue

        if state == "template":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                state = "code"
            i += 1
            continue

        # code
        if ch == "/" and nxt == "/":
            return "code"
        if ch == "/" and nxt == "*":
            state = "block_comment"
            i += 2
            continue
        if ch == "'":
            state = "single"
            i += 1
            continue
        if ch == '"':
            state = "double"
            i += 1
            continue
        if ch == "`":
            state = "template"
            i += 1
            continue
        i += 1
    return state


def minimize_text(text: str) -> MinimizeResult:
    # Templates can contain arbitrary JavaScript interpolation and literal
    # newlines. Keep the complete file byte-stable rather than guessing.
    if "`" in text:
        return MinimizeResult(text=text, saved_bytes=0, transformed_lines=0, skipped_reason="template_literal")

    state = "code"
    out: list[str] = []
    removed = 0
    transformed = 0

    for raw_line in text.splitlines(keepends=True):
        body, ending = _split_line_ending(raw_line)
        original_body = body

        if state == "code":
            cut = 0
            while cut < len(body) and body[cut] in {" ", "\t"}:
                cut += 1
            if cut:
                body = body[cut:]
                removed += len(original_body[:cut].encode("utf-8"))
                transformed += 1

        # State is derived from the original source, never from transformed
        # bytes, so the minimizer cannot alter its own lexical decisions.
        state = _next_state(original_body, state)
        out.append(body + ending)

    minimized = "".join(out)
    saved = len(text.encode("utf-8")) - len(minimized.encode("utf-8"))
    if saved != removed:
        raise ValueError(f"minimizer byte accounting mismatch: saved={saved} removed={removed}")
    return MinimizeResult(text=minimized, saved_bytes=saved, transformed_lines=transformed)


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

    if original.count("\n") != minimized.count("\n") or original.count("\r") != minimized.count("\r"):
        raise ValueError("minimizer changed line terminators")
    if after["bytes"] > before["bytes"]:
        raise ValueError("minimizer increased provider bytes")
    if before["markers"] != after["markers"]:
        raise ValueError("minimizer changed Provider v3 structural markers")
    if before["template_literal_tokens"] != after["template_literal_tokens"]:
        raise ValueError("minimizer changed template literal bytes")

    second = minimize_text(minimized).text
    if second != minimized:
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
    if len(filenames) != 96 or len(set(filenames)) != 96:
        raise SystemExit(
            f"expected 96 unique manifest provider filenames, got {len(filenames)} / {len(set(filenames))}"
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
        if result.skipped_reason == "template_literal":
            totals["skipped_templates"] += 1

    return {
        "schema_version": 2,
        "mode": "niakvio-safe-minimizer",
        "production_enabled": PRODUCTION_ENABLED,
        "terser_allowed": TERSER_ALLOWED,
        "provider_count": len(files),
        "transformations_enabled": list(TRANSFORMATIONS_ENABLED),
        "safety_contract": [
            "preserve every line terminator",
            "preserve all managed marker cardinalities",
            "preserve bytes inside strings, templates and block comments",
            "never rename identifiers",
            "never reorder or fold expressions",
            "never modify template-bearing providers",
            "require idempotence and Node syntax on all 96 providers",
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
    if report["provider_count"] != 96:
        raise SystemExit(f"expected 96 generated providers, got {report['provider_count']}")

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
