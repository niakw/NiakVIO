#!/usr/bin/env python3
"""NiakVIO-aware Provider v3 JavaScript one-line minimizer.

Publication output is exactly one physical line while NiakVIO managed markers,
string/regex payloads, runtime/security markers and editability are preserved.
This is deliberately not a generic minifier: Terser, identifier mangling,
expression folding and reordering are forbidden.

Untagged template physical line breaks become ``\\n`` escapes (same cooked
value); tagged templates fail closed because String.raw semantics would change.
ASI-sensitive line breaks are made explicit when JavaScript ASI already terminates
the restricted production (return/yield/break/continue/async -> semicolon).
Illegal throw-newline and ambiguous postfix-update cases still fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = ROOT / "providers"
MANIFEST = ROOT / "manifest.json"

PRODUCTION_ENABLED = True
TERSER_ALLOWED = False
TRANSFORMATIONS_ENABLED = [
    "one-physical-line",
    "code-linebreak-to-space",
    "post-linebreak-indentation-removal",
    "unmanaged-comment-removal",
    "untagged-template-linebreak-escape",
    "asi-restricted-linebreak-to-semicolon",
]

MARKERS = (
    "BEGIN NIAKVIO_PROVIDER",
    "END NIAKVIO_PROVIDER",
    "STARTFIX:",
    "CLOSEFIX:",
    "FIXDATA:",
    "NUVIO_GLOBAL_CORE_START_BOUNDARY_V1",
)
PROTECTED_COMMENT_TOKENS = (
    "NIAKVIO_", "NUVIO_", "STARTFIX:", "CLOSEFIX:", "FIXDATA:",
    "SPDX-License-Identifier", "@license", "@preserve", "sourceURL",
    "sourceMappingURL", "@cc_on",
)
_RESTRICTED_LINEBREAK_RE = re.compile(
    r"(?:^|[^A-Za-z0-9_$])(return|throw|break|continue|yield|async)\s*$"
)
_PREFIX_TEMPLATE_WORDS = {
    "return", "throw", "case", "delete", "void", "typeof", "yield",
    "await", "new", "in", "of", "instanceof",
}
_REGEX_PREFIX_WORDS = _PREFIX_TEMPLATE_WORDS | {"else", "do"}
_IDENTIFIER_TAIL_RE = re.compile(r"([A-Za-z_$][A-Za-z0-9_$]*)$")
_REGEX_FLAGS = set("dgimsuvy")


class MinimizeResult:
    __slots__ = ("text", "saved_bytes", "transformed_lines", "skipped_reason")

    def __init__(self, *, text: str, saved_bytes: int, transformed_lines: int,
                 skipped_reason: str = "") -> None:
        self.text = text
        self.saved_bytes = int(saved_bytes)
        self.transformed_lines = int(transformed_lines)
        self.skipped_reason = str(skipped_reason)


def _protected_comment(text: str) -> bool:
    stripped = str(text or "").strip()
    if stripped.startswith("/*!"):
        return True
    folded = stripped.casefold()
    return any(token.casefold() in folded for token in PROTECTED_COMMENT_TOKENS)


def _append_space(out: list[str]) -> None:
    if out and not out[-1].isspace():
        out.append(" ")


def _rstrip_horizontal(out: list[str]) -> None:
    while out and out[-1] in {" ", "\t", "\f", "\v"}:
        out.pop()


def _tail(out: list[str], limit: int = 192) -> str:
    return "".join(out[-limit:]) if out else ""


def _linebreak_guard(out: list[str]) -> None:
    tail = _tail(out).rstrip(" \t\f\v")
    if not tail:
        return
    restricted = _RESTRICTED_LINEBREAK_RE.search(tail)
    if restricted:
        keyword = restricted.group(1)
        if keyword == "throw":
            # A LineTerminator is forbidden after throw; accepting it would hide
            # invalid input rather than preserve JavaScript semantics.
            raise ValueError("illegal line break after throw cannot be flattened safely")
        # For return/yield/break/continue and a standalone async token, the
        # physical LineTerminator already terminates the production. Make that
        # ASI decision explicit before flattening to one physical line.
        out.append(";")
    if tail.endswith(("++", "--")):
        raise ValueError("ASI-sensitive line break after postfix update cannot be flattened safely")


def _tagged_template_risk(out: list[str]) -> bool:
    tail = _tail(out).rstrip()
    if not tail:
        return False
    match = _IDENTIFIER_TAIL_RE.search(tail)
    if match and match.group(1) in _PREFIX_TEMPLATE_WORDS:
        return False
    if tail[-1] in "=([{,:;!?&|+-*%~<>":
        return False
    return not tail.endswith("=>")


def _regex_allowed(out: list[str]) -> bool:
    """Claim regex syntax only in conservative expression-prefix positions."""
    tail = _tail(out).rstrip()
    if not tail:
        return True
    match = _IDENTIFIER_TAIL_RE.search(tail)
    if match:
        return match.group(1) in _REGEX_PREFIX_WORDS
    if tail.endswith("=>"):
        return True
    if tail.endswith(("++", "--")):
        return False
    return tail[-1] in "([{,:;=!?&|+-*%^~<>"


def _flatten_protected_block(comment: str) -> str:
    return comment.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")


def _consume_string(text: str, i: int, quote: str, out: list[str]) -> tuple[int, int]:
    transformed = 0
    out.append(quote)
    i += 1
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            if i + 1 >= len(text):
                out.append(ch)
                return i + 1, transformed
            nxt = text[i + 1]
            if nxt == "\r":
                transformed += 1
                i += 2
                if i < len(text) and text[i] == "\n":
                    i += 1
                continue
            if nxt == "\n":
                transformed += 1
                i += 2
                continue
            out.extend((ch, nxt))
            i += 2
            continue
        if ch == quote:
            out.append(ch)
            return i + 1, transformed
        if ch in "\r\n":
            raise ValueError("bare physical line break inside quoted JavaScript string")
        out.append(ch)
        i += 1
    raise ValueError("unterminated JavaScript string literal")


def _consume_regex(text: str, i: int, out: list[str]) -> int:
    """Copy one JavaScript regex literal exactly, including character classes."""
    out.append("/")
    i += 1
    in_class = False
    while i < len(text):
        ch = text[i]
        if ch in "\r\n":
            raise ValueError("bare physical line break inside JavaScript regex literal")
        if ch == "\\":
            if i + 1 >= len(text) or text[i + 1] in "\r\n":
                raise ValueError("unterminated/continued escape in JavaScript regex literal")
            out.extend((ch, text[i + 1]))
            i += 2
            continue
        if ch == "[" and not in_class:
            in_class = True
            out.append(ch)
            i += 1
            continue
        if ch == "]" and in_class:
            in_class = False
            out.append(ch)
            i += 1
            continue
        if ch == "/" and not in_class:
            out.append(ch)
            i += 1
            seen_flags: set[str] = set()
            while i < len(text) and text[i] in _REGEX_FLAGS:
                if text[i] in seen_flags:
                    break
                seen_flags.add(text[i])
                out.append(text[i])
                i += 1
            return i
        out.append(ch)
        i += 1
    raise ValueError("unterminated JavaScript regex literal")


def minimize_text(text: str) -> MinimizeResult:
    source = str(text or "")
    out: list[str] = []
    stack: list[dict[str, int | str]] = [{"kind": "code"}]
    i = 0
    transformed = 0

    while i < len(source):
        state = stack[-1]
        kind = str(state["kind"])
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""

        if kind == "template":
            if ch == "\\":
                if i + 1 >= len(source):
                    out.append(ch)
                    i += 1
                    continue
                nxt = source[i + 1]
                if nxt == "\r":
                    transformed += 1
                    i += 2
                    if i < len(source) and source[i] == "\n":
                        i += 1
                    continue
                if nxt == "\n":
                    transformed += 1
                    i += 2
                    continue
                out.extend((ch, nxt))
                i += 2
                continue
            if ch == "`":
                out.append(ch)
                stack.pop()
                i += 1
                continue
            if ch == "$" and nxt == "{":
                out.append("${")
                stack.append({"kind": "template_expr", "depth": 1})
                i += 2
                continue
            if ch == "\r":
                out.append("\\n")
                transformed += 1
                i += 1
                if i < len(source) and source[i] == "\n":
                    i += 1
                continue
            if ch == "\n":
                out.append("\\n")
                transformed += 1
                i += 1
                continue
            out.append(ch)
            i += 1
            continue

        if kind == "template_expr" and ch == "{":
            state["depth"] = int(state.get("depth", 1)) + 1
            out.append(ch)
            i += 1
            continue
        if kind == "template_expr" and ch == "}":
            depth = int(state.get("depth", 1)) - 1
            out.append(ch)
            i += 1
            if depth <= 0:
                stack.pop()
            else:
                state["depth"] = depth
            continue

        if ch in {"'", '"'}:
            i, count = _consume_string(source, i, ch, out)
            transformed += count
            continue

        if ch == "`":
            if _tagged_template_risk(out):
                raise ValueError("tagged template literal cannot be flattened without changing raw payload")
            out.append(ch)
            stack.append({"kind": "template"})
            i += 1
            continue

        if ch == "/" and nxt == "/":
            start = i
            i += 2
            while i < len(source) and source[i] not in "\r\n":
                i += 1
            comment = source[start:i]
            if _protected_comment(comment):
                out.append(f"/* {comment[2:].strip()} */")
            else:
                _append_space(out)
            transformed += 1
            if i < len(source):
                _rstrip_horizontal(out)
                _linebreak_guard(out)
                _append_space(out)
                if source[i] == "\r":
                    i += 1
                    if i < len(source) and source[i] == "\n":
                        i += 1
                else:
                    i += 1
                while i < len(source) and source[i] in " \t\f\v":
                    i += 1
                transformed += 1
            continue

        if ch == "/" and nxt == "*":
            end = source.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated JavaScript block comment")
            comment = source[i:end + 2]
            if _protected_comment(comment):
                flattened = _flatten_protected_block(comment)
                transformed += int(flattened != comment)
                out.append(flattened)
            else:
                _append_space(out)
                transformed += 1
            i = end + 2
            continue

        if ch == "/" and _regex_allowed(out):
            i = _consume_regex(source, i, out)
            continue

        if ch in "\r\n":
            _rstrip_horizontal(out)
            _linebreak_guard(out)
            _append_space(out)
            if ch == "\r":
                i += 1
                if i < len(source) and source[i] == "\n":
                    i += 1
            else:
                i += 1
            while i < len(source) and source[i] in " \t\f\v":
                i += 1
            transformed += 1
            continue

        out.append(ch)
        i += 1

    if len(stack) != 1 or str(stack[0].get("kind")) != "code":
        raise ValueError(f"unterminated JavaScript lexical state: {stack!r}")
    _rstrip_horizontal(out)
    minimized = "".join(out)
    if "\n" in minimized or "\r" in minimized:
        raise ValueError("one-line minimizer emitted a physical line break")
    saved = len(source.encode("utf-8")) - len(minimized.encode("utf-8"))
    if saved < 0:
        raise ValueError(f"minimizer increased provider bytes: saved={saved}")
    return MinimizeResult(text=minimized, saved_bytes=saved,
                          transformed_lines=transformed)


def audit_text(text: str) -> dict:
    encoded = text.encode("utf-8")
    return {
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "lines": text.count("\n") + text.count("\r") + (1 if text else 0),
        "physical_linebreaks": text.count("\n") + text.count("\r"),
        # Diagnostic only. Raw backticks in comments/regex are not semantic
        # template delimiters and therefore are intentionally not an invariant.
        "raw_backticks": text.count("`"),
        "markers": {marker: text.count(marker) for marker in MARKERS},
    }


def validate_transform(original: str, minimized: str) -> None:
    before = audit_text(original)
    after = audit_text(minimized)
    if after["bytes"] > before["bytes"]:
        raise ValueError("minimizer increased provider bytes")
    if after["physical_linebreaks"] != 0:
        raise ValueError("published provider is not one physical line")
    if before["markers"] != after["markers"]:
        raise ValueError("minimizer changed Provider v3 structural markers")
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
        if isinstance(row, dict) and row.get("enabled") is not False
        and str(row.get("filename") or "").startswith("providers/")
    ]
    if not filenames or len(filenames) != len(set(filenames)):
        raise SystemExit(
            f"active manifest provider filenames must be unique/non-empty: {len(filenames)} / {len(set(filenames))}"
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
        proc = subprocess.run(["node", "--check", str(path)], cwd=ROOT, text=True,
                              capture_output=True, timeout=20, check=False)
        if proc.returncode != 0:
            raise ValueError(f"Node parse failed for {name}: {proc.stdout}{proc.stderr}")


def portfolio_report(*, syntax_check: bool = False) -> dict:
    files = provider_files()
    rows = []
    totals = {
        "bytes_before": 0, "bytes_after": 0, "saved_bytes": 0,
        "transformed_lines": 0, "one_line_providers": 0,
    }
    for path in files:
        original = path.read_text(encoding="utf-8")
        try:
            result = minimize_text(original)
            validate_transform(original, result.text)
            if syntax_check:
                _node_check(result.text, path.name)
        except Exception as exc:
            raise ValueError(f"{path.name}: one-line minimizer failed: {exc}") from exc
        before = audit_text(original)
        after = audit_text(result.text)
        rows.append({
            "file": path.name, "before": before, "after": after,
            "saved_bytes": result.saved_bytes,
            "transformed_lines": result.transformed_lines,
            "skipped_reason": result.skipped_reason,
        })
        totals["bytes_before"] += before["bytes"]
        totals["bytes_after"] += after["bytes"]
        totals["saved_bytes"] += result.saved_bytes
        totals["transformed_lines"] += result.transformed_lines
        totals["one_line_providers"] += int(after["physical_linebreaks"] == 0)

    return {
        "schema_version": 5,
        "mode": "niakvio-safe-one-line-minimizer",
        "production_enabled": PRODUCTION_ENABLED,
        "terser_allowed": TERSER_ALLOWED,
        "provider_count": len(files),
        "transformations_enabled": list(TRANSFORMATIONS_ENABLED),
        "safety_contract": [
            "publish every active Provider v3 bundle as exactly one physical line",
            "preserve every managed Provider v3 marker cardinality",
            "preserve NIAKVIO_/NUVIO_ runtime/security marker comments",
            "preserve license/source-directive payloads as protected comments",
            "preserve quoted string and regular-expression literal payloads",
            "escape physical line breaks only inside untagged template literals",
            "fail closed on tagged templates because raw payload semantics differ",
            "encode ASI-terminated restricted-keyword line breaks as explicit semicolons",
            "fail closed on illegal throw-newline and postfix-update line breaks",
            "never rename identifiers", "never reorder or fold expressions",
            "never use Terser",
            f"require deterministic fixed-point and Node syntax on all {len(files)} current active providers",
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
        (resolved / path.name).write_text(
            minimize_provider_text(path.read_text(encoding="utf-8")), encoding="utf-8"
        )
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
            f"providers={report['provider_count']} bytes_before={totals['bytes_before']} "
            f"bytes_after={totals['bytes_after']} saved_bytes={totals['saved_bytes']} "
            f"transformed_lines={totals['transformed_lines']} one_line={totals['one_line_providers']} "
            f"production_enabled={str(PRODUCTION_ENABLED).lower()} terser_allowed=false"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
