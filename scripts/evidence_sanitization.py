#!/usr/bin/env python3
"""Redact credentials from persisted diagnostic evidence.

Runtime requests are intentionally untouched. Sanitization happens only on data
that is about to be written to repository evidence files.
"""
from __future__ import annotations

import re
import urllib.parse
from typing import Any

REDACTED = "<redacted>"

SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "bearer",
    "cookie",
    "credentials",
    "dle_password",
    "jwt",
    "pass",
    "passwd",
    "password",
    "secret",
    "set_cookie",
    "set-cookie",
    "sig",
    "signature",
    "sign_secret",
    "token",
    "x_api_key",
    "x_auth_token",
}

JWT_RE = re.compile(
    r"\beyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}\b"
)
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")
ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    (?P<prefix>
      ["']?
      (?:api[_-]?key|access[_-]?token|auth(?:orization)?|credential(?:s)?|
         dle[_-]?password|jwt|pass(?:wd|word)?|secret|sig(?:nature)?|
         sign[_-]?secret|token)
      ["']?
      \s*[:=]\s*
      ["']?
    )
    (?P<value>[A-Za-z0-9._~+/=-]{8,})
    """
)
URL_RE = re.compile(r"""https?://[^\s<>"']+""", re.I)
EMBEDDED_SECRET_RE = re.compile(
    r"""(?ix)
    (?P<prefix>
      (?:data-secret\s*=\s*\\*["'])
      |
      (?:(?:\\*["']?(?:token|secret|password|api[_-]?key)\\*["']?)\s*:\s*\\*["'])
    )
    (?P<value>[^"'<>\\\s]{4,})
    (?P<suffix>\\*["'])
    """
)


def normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").casefold()).strip("_")


def sensitive_key(value: str) -> bool:
    key = normalized_key(value)
    return (
        key in SENSITIVE_KEYS
        or key.endswith("_token")
        or key.endswith("_secret")
        or key.endswith("_password")
        or key.endswith("_signature")
        or key.endswith("_api_key")
    )


def redact_url(value: str) -> str:
    text = str(value or "")
    try:
        parsed = urllib.parse.urlsplit(text)
    except Exception:
        return redact_text(text, sanitize_urls=False)
    if parsed.scheme not in {"http", "https"}:
        return redact_text(text, sanitize_urls=False)

    query: list[tuple[str, str]] = []
    for key, raw in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if sensitive_key(key) or JWT_RE.search(raw) or BEARER_RE.search(raw):
            query.append((key, REDACTED))
        else:
            query.append((key, redact_text(raw, sanitize_urls=False)))

    fragment = redact_text(parsed.fragment, sanitize_urls=False)
    return urllib.parse.urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urllib.parse.urlencode(query, doseq=True),
            fragment,
        )
    )


def redact_text(value: str, *, sanitize_urls: bool = True) -> str:
    text = str(value or "")
    text = JWT_RE.sub("<redacted-jwt>", text)
    text = BEARER_RE.sub("Bearer <redacted>", text)
    text = ASSIGNMENT_RE.sub(lambda match: match.group("prefix") + REDACTED, text)
    text = EMBEDDED_SECRET_RE.sub(
        lambda match: match.group("prefix") + REDACTED + match.group("suffix"),
        text,
    )
    if sanitize_urls:
        text = URL_RE.sub(lambda match: redact_url(match.group(0)), text)
    return text


def sanitize_evidence(value: Any, *, key: str | None = None) -> Any:
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for child_key, child_value in value.items():
            if sensitive_key(str(child_key)):
                output[str(child_key)] = REDACTED
            else:
                output[str(child_key)] = sanitize_evidence(child_value, key=str(child_key))
        return output

    if isinstance(value, list):
        return [sanitize_evidence(item, key=key) for item in value]

    if isinstance(value, tuple):
        return [sanitize_evidence(item, key=key) for item in value]

    if isinstance(value, str):
        if sensitive_key(key or ""):
            return REDACTED
        normalized = normalized_key(key or "")
        if "url" in normalized or normalized in {"location", "origin", "referer"}:
            return redact_url(value)
        return redact_text(value)

    return value
