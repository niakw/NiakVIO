#!/usr/bin/env python3
"""Compatibility entry point for Provider v3 source-plan enrichment.

The implementation now lives in provider_contract_recognizer.py so Discovery,
Learning and reconstruction share one source-aware contract recognition skill.
"""
from provider_contract_recognizer import *  # noqa: F401,F403


if __name__ == "__main__":
    raise SystemExit(main())
