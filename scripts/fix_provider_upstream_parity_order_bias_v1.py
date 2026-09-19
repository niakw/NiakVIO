#!/usr/bin/env python3
"""Remove execution-order bias from terminal-verified upstream parity V3."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/run_provider_upstream_parity_v3.py"
TEST = ROOT / "tests/provider_upstream_parity_v3_test.py"

OLD_IMPORT = "import argparse\nimport concurrent.futures\n"
NEW_IMPORT = "import argparse\nimport concurrent.futures\nimport hashlib\n"

OLD_SAMPLE = '''        upstream = _run_verified(upstream_path, up_fixture, timeout)\n        local = _run_verified(local_path, local_fixture, timeout)\n        classification = classify_pair(upstream, local)\n        samples.append({\n            "fixture": candidate["slug"],\n            "tmdbId": str(candidate.get("tmdbId") or ""),\n            "classification": classification,\n            "upstream": upstream,\n            "niakvio": local,\n        })\n'''

NEW_SAMPLE = '''        # Never give the upstream a systematic first-request advantage. Some\n        # services are cold-start/rate-limit sensitive (PersianStremio is a\n        # proven example: identical requests alternated 200/503). Pick the first\n        # order deterministically per sample, then reverse-confirm every\n        # asymmetric positive before it can become a certain regression.\n        identity = f"{provider_id}:{lane}:{candidate['slug']}"\n        local_first = bool(hashlib.sha256(identity.encode("utf-8")).digest()[0] & 1)\n\n        def ordered_pair(first_local: bool) -> tuple[dict[str, Any], dict[str, Any]]:\n            if first_local:\n                local_result = _run_verified(local_path, local_fixture, timeout)\n                upstream_result = _run_verified(upstream_path, up_fixture, timeout)\n            else:\n                upstream_result = _run_verified(upstream_path, up_fixture, timeout)\n                local_result = _run_verified(local_path, local_fixture, timeout)\n            return upstream_result, local_result\n\n        upstream, local = ordered_pair(local_first)\n        classification = classify_pair(upstream, local)\n        confirmation = None\n        confirmation_classification = None\n\n        if classification in {"upstream_ok_niakvio_ko", "niakvio_ok_upstream_ko"}:\n            upstream_confirm, local_confirm = ordered_pair(not local_first)\n            confirmation_classification = classify_pair(upstream_confirm, local_confirm)\n            confirmation = {\n                "executionOrder": "upstream_first" if local_first else "niakvio_first",\n                "classification": confirmation_classification,\n                "upstream": upstream_confirm,\n                "niakvio": local_confirm,\n            }\n            upstream_positive_count = sum(\n                int(row.get("stream_count") or 0) > 0 for row in (upstream, upstream_confirm)\n            )\n            local_positive_count = sum(\n                int(row.get("stream_count") or 0) > 0 for row in (local, local_confirm)\n            )\n            if upstream_positive_count and local_positive_count:\n                classification = "both_ok_flaky"\n            elif upstream_positive_count == 2 and local_positive_count == 0:\n                classification = "upstream_ok_niakvio_ko"\n            elif local_positive_count and upstream_positive_count == 0:\n                classification = "niakvio_ok_upstream_ko"\n            elif upstream_positive_count and local_positive_count == 0:\n                classification = "upstream_advantage_unconfirmed"\n            else:\n                classification = "order_sensitive_resample"\n\n        sample = {\n            "fixture": candidate["slug"],\n            "tmdbId": str(candidate.get("tmdbId") or ""),\n            "executionOrder": "niakvio_first" if local_first else "upstream_first",\n            "classification": classification,\n            "upstream": upstream,\n            "niakvio": local,\n        }\n        if confirmation is not None:\n            sample["confirmation"] = confirmation\n            sample["confirmationClassification"] = confirmation_classification\n        samples.append(sample)\n'''

OLD_STATUS = '''    if "upstream_ok_niakvio_ko" in classes:\n        status = "REGRESSION"\n    elif any(value in {"both_ok", "niakvio_ok_upstream_ko"} for value in classes):\n        status = "POSITIVE"\n    elif classes and all(value in {"catalog_miss_both", "upstream_candidate_unverified", "niakvio_candidate_unverified"} for value in classes):\n        status = "RESAMPLE"\n'''

NEW_STATUS = '''    if "upstream_ok_niakvio_ko" in classes:\n        status = "REGRESSION"\n    elif any(value in {"both_ok", "both_ok_flaky", "niakvio_ok_upstream_ko"} for value in classes):\n        status = "POSITIVE"\n    elif classes and all(value in {\n        "catalog_miss_both",\n        "upstream_candidate_unverified",\n        "niakvio_candidate_unverified",\n        "upstream_advantage_unconfirmed",\n        "order_sensitive_resample",\n    } for value in classes):\n        status = "RESAMPLE"\n'''

OLD_TEST_ASSERT = '''assert row["status"] == "REGRESSION", row\nassert [sample["fixture"] for sample in row["samples"]] == ["a", "b"], row\nassert len(calls) == 4, calls\n\n# If every sampled work is a clean 0/0, the lane is RESAMPLE, never ZERO.\n'''

NEW_TEST_ASSERT = '''assert row["status"] == "REGRESSION", row\nassert [sample["fixture"] for sample in row["samples"]] == ["a", "b"], row\n# Clean 0/0 costs two calls; the asymmetric positive is reverse-confirmed and\n# therefore costs four calls before it can be called a certain regression.\nassert len(calls) == 6, calls\nassert row["samples"][-1]["confirmationClassification"] == "upstream_ok_niakvio_ko", row\n\n# First-request-wins services must never manufacture a regression. The reverse\n# order proves that both implementations can produce terminal media, so the\n# lane is positive-but-flaky instead of upstream_ok_niakvio_ko.\nparity.select_fixtures = lambda *args, **kwargs: [fixtures[1]]\nflaky_calls = 0\ndef first_request_wins(path, fixture, timeout):\n    global flaky_calls\n    flaky_calls += 1\n    return result(1 if flaky_calls % 2 else 0)\nparity._run_verified = first_request_wins\nflaky = parity.run_lane(\n    "demo",\n    "movie",\n    Path("local.js"),\n    Path("upstream.js"),\n    timeout=10,\n    sample_count=1,\n    seed="seed",\n)\nassert flaky["status"] == "POSITIVE", flaky\nassert flaky["samples"][0]["classification"] == "both_ok_flaky", flaky\nassert flaky["samples"][0]["confirmation"] is not None, flaky\nassert flaky_calls == 4, flaky_calls\n\n# If every sampled work is a clean 0/0, the lane is RESAMPLE, never ZERO.\nparity.select_fixtures = lambda *args, **kwargs: fixtures\n'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise AssertionError(f"parity order-bias migration anchor drifted: {label}")
    return text.replace(old, new, 1)


def main() -> int:
    source = TARGET.read_text(encoding="utf-8")
    before_source = source
    source = replace_once(source, OLD_IMPORT, NEW_IMPORT, "hashlib import")
    source = replace_once(source, OLD_SAMPLE, NEW_SAMPLE, "sample execution")
    source = replace_once(source, OLD_STATUS, NEW_STATUS, "lane status")
    if source != before_source:
        TARGET.write_text(source, encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    before_test = test
    test = replace_once(test, OLD_TEST_ASSERT, NEW_TEST_ASSERT, "unit test")
    if test != before_test:
        TEST.write_text(test, encoding="utf-8")

    assert "reverse-confirm every" in source
    assert 'classification = "both_ok_flaky"' in source
    assert 'classification = "upstream_advantage_unconfirmed"' in source
    assert "first-request-wins" in test.lower()
    print(
        "PARITY_ORDER_BIAS_V1_OK",
        f"source_changed={str(source != before_source).lower()}",
        f"test_changed={str(test != before_test).lower()}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
