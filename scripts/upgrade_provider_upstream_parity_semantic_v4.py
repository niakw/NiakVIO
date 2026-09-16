#!/usr/bin/env python3
"""Install the fail-closed upstream semantic guard into parity V3."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "run_provider_upstream_parity_v3.py"
MARKER = "PARITY_UPSTREAM_SEMANTIC_GUARD_V4"


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise ValueError(f"semantic parity upgrade {label} count={count}")
    return text.replace(old, new, 1)


def apply(text: str) -> str:
    if MARKER in text:
        validate(text)
        return text

    text = once(
        text,
        "from parity_hls_terminal_probe import verify_hls_terminal\n",
        "from parity_hls_terminal_probe import verify_hls_terminal\nimport provider_upstream_semantic_guard as semantic_guard\n",
        "import",
    )

    anchor = "\ndef run_lane(\n"
    helper = '''\n# PARITY_UPSTREAM_SEMANTIC_GUARD_V4\ndef classify_pair_with_semantic_guard(\n    provider_id: str,\n    fixture: dict[str, Any],\n    upstream_path: Path,\n    upstream: dict[str, Any],\n    local: dict[str, Any],\n    timeout: int,\n) -> tuple[str, dict[str, Any] | None]:\n    classification = classify_pair(upstream, local)\n    if classification != "upstream_ok_niakvio_ko":\n        return classification, None\n    evidence = semantic_guard.assess_upstream(\n        provider_id, upstream_path, fixture, timeout, _worker_raw\n    )\n    if evidence.get("trusted") is False:\n        return "upstream_semantic_untrusted", evidence\n    return classification, evidence\n\n'''
    text = once(text, anchor, helper + anchor, "helper")

    text = once(
        text,
        "        confirmation = None\n        confirmation_classification = None\n",
        "        confirmation = None\n        confirmation_classification = None\n        semantic_evidence = None\n",
        "semantic-state",
    )

    text = once(
        text,
        '''            elif upstream_positive_count == 2 and local_positive_count == 0:\n                classification = "upstream_ok_niakvio_ko"\n''',
        '''            elif upstream_positive_count == 2 and local_positive_count == 0:\n                classification = "upstream_ok_niakvio_ko"\n                semantic_evidence = semantic_guard.assess_upstream(\n                    provider_id, upstream_path, up_fixture, timeout, _worker_raw\n                )\n                if semantic_evidence.get("trusted") is False:\n                    classification = "upstream_semantic_untrusted"\n''',
        "confirmed-regression",
    )

    text = once(
        text,
        '''        if confirmation is not None:\n            sample["confirmation"] = confirmation\n            sample["confirmationClassification"] = confirmation_classification\n        samples.append(sample)\n''',
        '''        if confirmation is not None:\n            sample["confirmation"] = confirmation\n            sample["confirmationClassification"] = confirmation_classification\n        if semantic_evidence is not None:\n            sample["semanticValidation"] = semantic_evidence\n        samples.append(sample)\n''',
        "sample-evidence",
    )

    text = once(
        text,
        '''        "upstream_advantage_unconfirmed",\n        "order_sensitive_resample",\n''',
        '''        "upstream_advantage_unconfirmed",\n        "order_sensitive_resample",\n        "upstream_semantic_untrusted",\n''',
        "resample-status",
    )

    validate(text)
    return text


def validate(text: str) -> None:
    required = (
        MARKER,
        "import provider_upstream_semantic_guard as semantic_guard",
        "def classify_pair_with_semantic_guard(",
        'return "upstream_semantic_untrusted", evidence',
        'sample["semanticValidation"] = semantic_evidence',
        '"upstream_semantic_untrusted",',
    )
    for needle in required:
        if needle not in text:
            raise ValueError(f"semantic parity upgrade missing {needle}")
    if text.count(MARKER) != 1:
        raise ValueError(f"semantic parity marker count={text.count(MARKER)}")


def main() -> None:
    source = PATH.read_text(encoding="utf-8")
    patched = apply(source)
    PATH.write_text(patched, encoding="utf-8")
    print("PARITY_UPSTREAM_SEMANTIC_GUARD_V4_APPLIED changed=" + str(patched != source).lower())


if __name__ == "__main__":
    main()
