#!/usr/bin/env python3
"""Summarize local CodeQL SARIF deterministically and optionally fail on High/Critical findings."""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

HIGH_SECURITY_SEVERITY = 7.0


def _security_score(rule: dict) -> float | None:
    props = rule.get("properties") or {}
    raw = props.get("security-severity")
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def summarize(directory: Path) -> tuple[int, collections.Counter[str], list[tuple[str, str, float]], int]:
    sarifs = sorted(directory.glob("*.sarif"))
    if not sarifs:
        raise SystemExit(f"CodeQL local analysis produced no SARIF in {directory}")

    result_count = 0
    by_rule: collections.Counter[str] = collections.Counter()
    high: list[tuple[str, str, float]] = []

    for path in sarifs:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for run in payload.get("runs") or []:
            rules: dict[str, tuple[float | None, str]] = {}
            driver = ((run.get("tool") or {}).get("driver") or {})
            for rule in driver.get("rules") or []:
                if not isinstance(rule, dict):
                    continue
                rule_id = str(rule.get("id") or "")
                rules[rule_id] = (_security_score(rule), str(rule.get("name") or rule_id))

            for result in run.get("results") or []:
                if not isinstance(result, dict):
                    continue
                result_count += 1
                rule_id = str(result.get("ruleId") or "")
                by_rule[rule_id] += 1
                score, name = rules.get(rule_id, (None, rule_id))
                if score is not None and score >= HIGH_SECURITY_SEVERITY:
                    high.append((rule_id, name, score))

    return result_count, by_rule, high, len(sarifs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--fail-high", action="store_true")
    args = parser.parse_args()

    result_count, by_rule, high, sarif_count = summarize(args.directory)
    print(f"CODEQL_RESULT_COUNT={result_count}")
    print(f"NIAKVIO_CODEQL_LOCAL_EXTENDED results={result_count} high_or_critical={len(high)} sarif={sarif_count}")
    for rule_id, count in by_rule.most_common():
        print(f"CODEQL_RULE_COUNT {rule_id}={count}")
    for rule_id, name, score in high:
        print(f"OPEN_LOCAL_HIGH_ALERT {rule_id}|{score}|{name}")

    if args.fail_high and high:
        raise SystemExit("local CodeQL security-extended High/Critical findings remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
