#!/usr/bin/env python3
"""Safely capture, abstract and replay proof-backed bounded text request bodies.

Some upstream providers send search identity as raw text or as JSON arrays/scalars.
The V2 proof worker intentionally classified these bodies as `text` but discarded
contents, making a live POST route impossible to reconstruct.

V9 remains fail-closed:
- worker only exposes a short printable text body when it contains no obvious
  sensitive marker or high-entropy token shape;
- proof promotion requires at least one fixture/provider substitution and rejects
  any remaining meaningful fixture residue;
- raw text is never written to route DATA: only the abstracted template is stored;
- ProviderBase replays `bodyKind=text` through the existing scalar placeholder
  expander and preserves the already-proofed request Content-Type/header set.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "provider_worker.cjs"
PROOF = ROOT / "scripts" / "provider_route_proof.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
WORKER_MARKER = "NUVIO_PROVIDER_WORKER_TEXT_BODY_PROOF_V9"
PROOF_MARKER = "PROVIDER_ROUTE_PROOF_TEXT_BODY_V9"
BASE_MARKER = "NIAKVIO_PROVIDER_BASE_TEXT_BODY_REQUEST_V9"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_worker() -> bool:
    text = WORKER.read_text(encoding="utf-8")
    if WORKER_MARKER in text:
        validate_worker(text)
        return False
    if "NUVIO_PROVIDER_WORKER_ROUTE_PROOF_REQUEST_CLONE_V2" not in text:
        raise AssertionError("V9 text-body proof requires worker route-proof V2")
    old = "  out.body_kind = 'text';\n  return out;\n}"
    new = r'''  /* NUVIO_PROVIDER_WORKER_TEXT_BODY_PROOF_V9 */
  out.body_kind = 'text';
  // Raw text is evidence-only and is never copied directly into Provider DATA.
  // Keep it in-memory only when it is bounded, printable and clearly not a
  // credential/token-shaped value. Python must still abstract fixture identity
  // before a request spec can become reusable.
  const printable = !/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/.test(text);
  const tokenLike = /(?:^|[^A-Za-z0-9])(?:eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}|[A-Fa-f0-9]{40,}|[A-Za-z0-9_-]{64,})(?:$|[^A-Za-z0-9])/i.test(text);
  const sensitiveLike = /(?:api[_-]?key|access[_-]?token|authorization|bearer|secret|password|cookie|session|signature|nonce)\s*[:=]/i.test(text);
  if (text.length <= 1024 && printable && !tokenLike && !sensitiveLike) {
    out.body_fields = ['$text'];
    out.body_values['$text'] = text;
  }
  return out;
}'''
    text = once(text, old, new, "worker-text-body-capture")
    WORKER.write_text(text, encoding="utf-8")
    validate_worker(text)
    return True


def patch_proof() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if PROOF_MARKER in text:
        validate_proof(text)
        return False

    anchor = "def derive_request_spec(\n"
    helper = r'''# PROVIDER_ROUTE_PROOF_TEXT_BODY_V9
def _text_body_template(
    raw: object,
    fixture: dict[str, Any],
    provider_values: set[str],
) -> tuple[str | None, list[dict[str, str]], list[dict[str, str]]]:
    text = str(raw if raw is not None else "")
    if not text or len(text) > 1024 or "<redacted>" in text:
        return None, [], [{"location": "body:$text", "value": "unsafe-or-empty"}]

    template = text
    substitutions: list[dict[str, str]] = []
    residue: list[dict[str, str]] = []

    # Long/meaningful fixture values first so replacements cannot be fragmented.
    candidates: list[tuple[str, str]] = []
    titles = [fixture.get("title"), *(fixture.get("aliases") or [])]
    for value in titles:
        literal = str(value or "").strip()
        if len(literal) >= 2:
            candidates.append((literal, "{query}"))
    tmdb = str(fixture.get("tmdbId") or "").strip()
    if len(tmdb) >= 3:
        candidates.append((tmdb, "{tmdbId}"))
    year = str(fixture.get("year") or "").strip()
    if len(year) == 4:
        candidates.append((year, "{year}"))
    media = str(fixture.get("mediaType") or fixture.get("type") or fixture.get("category") or "").strip()
    if len(media) >= 2:
        candidates.append((media, "{media}"))
    for value in provider_values:
        literal = str(value or "").strip()
        if len(literal) >= 2:
            candidates.append((literal, "{id}"))

    # Exact literals are evidence from the fixture/provider response. Replace
    # longer values first and record every proof-backed abstraction.
    for literal, placeholder in sorted(set(candidates), key=lambda row: len(row[0]), reverse=True):
        if literal and literal in template:
            template = template.replace(literal, placeholder)
            substitutions.append({
                "location": "body:$text",
                "value": literal[:160],
                "placeholder": placeholder,
            })

    # Single-digit season/episode values are too ambiguous to replace globally.
    # Support them only when the text explicitly labels the field.
    labelled = [
        ("season", str(fixture.get("season") or "").strip(), "{season}"),
        ("episode", str(fixture.get("episode") or "").strip(), "{episode}"),
    ]
    import re as _re
    for label, literal, placeholder in labelled:
        if not literal:
            continue
        pattern = _re.compile(rf"(?i)(\b{label}\b\s*[:=]\s*){_re.escape(literal)}\b")
        if pattern.search(template):
            template = pattern.sub(lambda match: match.group(1) + placeholder, template)
            substitutions.append({
                "location": "body:$text",
                "value": literal,
                "placeholder": placeholder,
            })

    # A text body is never executable as unexplained static data. At least one
    # proof-backed substitution is required.
    if not substitutions:
        return None, [], [{"location": "body:$text", "value": "no-proof-backed-substitution"}]

    # Fail closed if meaningful fixture/provider values remain after abstraction.
    residue_tokens = [
        str(fixture.get("tmdbId") or "").strip(),
        str(fixture.get("title") or "").strip(),
        str(fixture.get("year") or "").strip(),
        *[str(value) for value in provider_values],
    ]
    for token in residue_tokens:
        if len(token) >= 3 and token in template:
            residue.append({"location": "body:$text", "value": token[:160]})
    if residue:
        return None, substitutions, residue
    return template, substitutions, []


'''
    text = once(text, anchor, helper + anchor, "proof-text-helper")

    old_branch = '''    if body_kind in {"json", "form"}:
        if raw_body and not body:
            reusable = False
        spec["bodyKind"] = body_kind
        spec["body"] = body
    elif body_kind not in {"none", "empty", ""}:
        reusable = False
'''
    new_branch = '''    if body_kind in {"json", "form"}:
        if raw_body and not body:
            reusable = False
        spec["bodyKind"] = body_kind
        spec["body"] = body
    elif body_kind == "text":
        text_template, text_substitutions, text_residue = _text_body_template(
            raw_body.get("$text"), fixture, provider_values
        )
        substitutions.extend(text_substitutions)
        residue.extend(text_residue)
        reusable = reusable and text_template is not None and not text_residue
        if text_template is not None:
            spec["bodyKind"] = "text"
            spec["body"] = text_template
    elif body_kind not in {"none", "empty", ""}:
        reusable = False
'''
    text = once(text, old_branch, new_branch, "proof-text-branch")
    PROOF.write_text(text, encoding="utf-8")
    validate_proof(text)
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    if BASE_MARKER in text:
        validate_base(text)
        return False
    if "NIAKVIO_PROVIDER_BASE_ROUTE_REQUEST_SPEC_V1" not in text:
        raise AssertionError("V9 text replay requires route request spec V1")
    old = '''  } else if (bodyKind === "form" && body && typeof body === "object") {
    spec.body = Object.entries(body).map(([key, value]) => encodeURIComponent(key) + "=" + encodeURIComponent(_text(value))).join("&");
    if (!Object.keys(spec.headers).some(key => key.toLowerCase() === "content-type")) spec.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8";
  }
  return spec;
}'''
    new = '''  } else if (bodyKind === "form" && body && typeof body === "object") {
    spec.body = Object.entries(body).map(([key, value]) => encodeURIComponent(key) + "=" + encodeURIComponent(_text(value))).join("&");
    if (!Object.keys(spec.headers).some(key => key.toLowerCase() === "content-type")) spec.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8";
  /* NIAKVIO_PROVIDER_BASE_TEXT_BODY_REQUEST_V9 */
  } else if (bodyKind === "text" && typeof raw.body === "string") {
    spec.body = _recipeExpandScalar(raw.body, values);
  }
  return spec;
}'''
    text = once(text, old, new, "base-text-replay")
    BASE.write_text(text, encoding="utf-8")
    validate_base(text)
    return True


def validate_worker(text: str | None = None) -> None:
    value = text if text is not None else WORKER.read_text(encoding="utf-8")
    for needle in (
        WORKER_MARKER,
        "out.body_values['$text'] = text",
        "text.length <= 1024",
        "!tokenLike",
        "!sensitiveLike",
    ):
        if needle not in value:
            raise AssertionError(f"V9 worker missing: {needle}")


def validate_proof(text: str | None = None) -> None:
    value = text if text is not None else PROOF.read_text(encoding="utf-8")
    for needle in (
        PROOF_MARKER,
        "def _text_body_template",
        'raw_body.get("$text")',
        'spec["bodyKind"] = "text"',
        'spec["body"] = text_template',
        "no-proof-backed-substitution",
    ):
        if needle not in value:
            raise AssertionError(f"V9 proof missing: {needle}")


def validate_base(text: str | None = None) -> None:
    value = text if text is not None else BASE.read_text(encoding="utf-8")
    for needle in (
        BASE_MARKER,
        'bodyKind === "text"',
        "typeof raw.body === \"string\"",
        "spec.body = _recipeExpandScalar(raw.body, values)",
    ):
        if needle not in value:
            raise AssertionError(f"V9 base missing: {needle}")


def main() -> int:
    changed = patch_worker() | patch_proof() | patch_base()
    validate_worker()
    validate_proof()
    validate_base()
    print(
        f"PROVIDER_TEXT_BODY_REQUEST_V9_OK changed={str(changed).lower()} "
        "bounded_text=1024 secret_shapes_rejected=1 proof_substitution_required=1 "
        "opaque_static_text_rejected=1 replay=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
